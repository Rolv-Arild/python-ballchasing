from __future__ import annotations

import functools
import threading
import time
from enum import Enum
from typing import Callable, Any


class RateLimitCategory(str, Enum):
    """Rate limit categories defined in ballchasing.com API documentation."""
    LIST = "list"          # GET /replays, GET /groups
    CORE = "core"          # GET/PATCH/DELETE /replays/{id}, /groups/{id}, POST /groups, upload, maps
    DOWNLOAD = "download"  # GET /replays/{id}/file
    PING = "ping"          # GET /


# Hourly rate limit backoff times per category (seconds to wait between requests)
# - regular: list 500/hr (7.2s), core 1000/hr (3.6s), download 200/hr (18.0s)
# - gold: list 1000/hr (3.6s), core 2000/hr (1.8s), download 400/hr (9.0s)
# - diamond: list 2000/hr (1.8s), core 5000/hr (0.72s), download 1000/hr (3.6s)
# - champion: list 8/s, core 8/s, download 2000/hr (1.8s)
# - gc: list 16/s, core 16/s, download 2/s (0.5s)
CATEGORY_HOURLY_SLEEP_TIMES: dict[str, dict[RateLimitCategory, float]] = {
    "regular": {
        RateLimitCategory.LIST: 3600 / 500,      # 7.2s
        RateLimitCategory.CORE: 3600 / 1000,     # 3.6s
        RateLimitCategory.DOWNLOAD: 3600 / 200,  # 18.0s
        RateLimitCategory.PING: 0.0,
    },
    "gold": {
        RateLimitCategory.LIST: 3600 / 1000,     # 3.6s
        RateLimitCategory.CORE: 3600 / 2000,     # 1.8s
        RateLimitCategory.DOWNLOAD: 3600 / 400,  # 9.0s
        RateLimitCategory.PING: 0.0,
    },
    "diamond": {
        RateLimitCategory.LIST: 3600 / 2000,     # 1.8s
        RateLimitCategory.CORE: 3600 / 5000,     # 0.72s
        RateLimitCategory.DOWNLOAD: 3600 / 1000, # 3.6s
        RateLimitCategory.PING: 0.0,
    },
    "champion": {
        RateLimitCategory.LIST: 1.0 / 8,         # 0.125s
        RateLimitCategory.CORE: 1.0 / 8,         # 0.125s
        RateLimitCategory.DOWNLOAD: 3600 / 2000, # 1.8s
        RateLimitCategory.PING: 0.0,
    },
    "gc": {
        RateLimitCategory.LIST: 1.0 / 16,        # 0.0625s
        RateLimitCategory.CORE: 1.0 / 16,        # 0.0625s
        RateLimitCategory.DOWNLOAD: 1.0 / 2,     # 0.5s
        RateLimitCategory.PING: 0.0,
    },
}

# Maximum calls per second (burst rates)
CATEGORY_BURST_RATES: dict[str, dict[RateLimitCategory, float]] = {
    "regular": {RateLimitCategory.LIST: 2.0, RateLimitCategory.CORE: 2.0, RateLimitCategory.DOWNLOAD: 1.0, RateLimitCategory.PING: 10.0},
    "gold": {RateLimitCategory.LIST: 2.0, RateLimitCategory.CORE: 2.0, RateLimitCategory.DOWNLOAD: 2.0, RateLimitCategory.PING: 10.0},
    "diamond": {RateLimitCategory.LIST: 4.0, RateLimitCategory.CORE: 4.0, RateLimitCategory.DOWNLOAD: 2.0, RateLimitCategory.PING: 10.0},
    "champion": {RateLimitCategory.LIST: 8.0, RateLimitCategory.CORE: 8.0, RateLimitCategory.DOWNLOAD: 2.0, RateLimitCategory.PING: 10.0},
    "gc": {RateLimitCategory.LIST: 16.0, RateLimitCategory.CORE: 16.0, RateLimitCategory.DOWNLOAD: 2.0, RateLimitCategory.PING: 10.0},
}


def resolve_category(url_or_endpoint: str) -> RateLimitCategory:
    """Categorize an endpoint URL or path into a RateLimitCategory."""
    path = url_or_endpoint.split("?")[0].rstrip("/")
    if path.endswith("/file"):
        return RateLimitCategory.DOWNLOAD
    if path.endswith("/replays") or path.endswith("/groups"):
        return RateLimitCategory.LIST
    if path == "" or path.endswith("/api") or path.endswith("/api/"):
        return RateLimitCategory.PING
    return RateLimitCategory.CORE


class RateLimiter:
    """
    Thread-safe rate limiter and global 429 tracker for BallchasingApi.

    Coordinates rate limits across concurrent requests/threads sharing the same
    BallchasingApi instance to prevent cascading 429 errors.
    """

    def __init__(
            self,
            patron_type_getter: Callable[[], str | None] | None = None,
            *,
            proactive: bool = False,
    ):
        self._lock = threading.Lock()
        self._patron_type_getter = patron_type_getter
        self.proactive = proactive

        # Global reactive cooldown (shared across all threads/endpoints for this API instance)
        self._rate_limited_until: float = 0.0
        self._last_rate_limited_at: float | None = None

        # Per-category tracking
        self._last_request_time: dict[RateLimitCategory, float] = {}
        self._category_rate_limit_count: dict[RateLimitCategory, int] = {}
        self._last_rate_limited_per_category: dict[RateLimitCategory, float] = {}

    @property
    def last_rate_limited_at(self) -> float | None:
        """Timestamp (time.time()) of the most recent 429 response, or None if never rate-limited."""
        with self._lock:
            return self._last_rate_limited_at

    @property
    def is_rate_limited(self) -> bool:
        """True if the instance is currently waiting out a 429 rate-limit cooldown."""
        with self._lock:
            return time.monotonic() < self._rate_limited_until

    @property
    def rate_limited_until(self) -> float:
        """Monotonic timestamp until which the global cooldown is active."""
        with self._lock:
            return self._rate_limited_until

    def get_patron_type(self) -> str:
        if self._patron_type_getter:
            try:
                pt = self._patron_type_getter()
                if pt:
                    return pt
            except Exception:
                pass
        return "regular"

    def get_category_sleep_time(self, category: RateLimitCategory) -> float:
        """Returns the hourly backoff sleep time for the specified category and current patron tier."""
        pt = self.get_patron_type()
        return CATEGORY_HOURLY_SLEEP_TIMES.get(pt, CATEGORY_HOURLY_SLEEP_TIMES["regular"]).get(
            category, 3.6
        )

    def before_request(self, category: RateLimitCategory) -> None:
        """
        Called before sending an HTTP request.
        If a global 429 cooldown is active, waits for it to expire.
        If proactive rate limiting is enabled, paces requests according to the category's burst rate.
        """
        sleep_duration = 0.0
        with self._lock:
            now_mono = time.monotonic()
            # 1. Check global reactive 429 cooldown
            if now_mono < self._rate_limited_until:
                sleep_duration = self._rate_limited_until - now_mono

            # 2. If proactive mode, ensure spacing between requests
            if self.proactive:
                pt = self.get_patron_type()
                rate = CATEGORY_BURST_RATES.get(pt, CATEGORY_BURST_RATES["regular"]).get(category, 2.0)
                min_interval = 1.0 / rate if rate > 0 else 0.0
                last_time = self._last_request_time.get(category, 0.0)
                elapsed = now_mono - last_time
                if elapsed < min_interval:
                    proactive_wait = min_interval - elapsed
                    sleep_duration = max(sleep_duration, proactive_wait)

                self._last_request_time[category] = now_mono + sleep_duration

        if sleep_duration > 0:
            time.sleep(sleep_duration)

    def record_429(
            self,
            category: RateLimitCategory,
            *,
            retry_after: float | None = None,
            fallback_sleep_time: float | None = None,
            retries: int = 1,
    ) -> float:
        """
        Record a 429 response. Updates the global and per-category tracker,
        and returns the duration (in seconds) that the caller should sleep.
        """
        with self._lock:
            now_wall = time.time()
            now_mono = time.monotonic()

            self._last_rate_limited_at = now_wall
            self._last_rate_limited_per_category[category] = now_wall
            self._category_rate_limit_count[category] = self._category_rate_limit_count.get(category, 0) + 1

            if retry_after is not None and retry_after > 0:
                wait_time = float(retry_after)
            elif fallback_sleep_time is not None and fallback_sleep_time > 0:
                wait_time = float(fallback_sleep_time)
            else:
                cat_sleep = self.get_category_sleep_time(category)
                backoff = float(2 ** (retries - 1))
                wait_time = max(cat_sleep, min(backoff, 60.0))

            # Extend global cooldown until this wait expires
            self._rate_limited_until = max(self._rate_limited_until, now_mono + wait_time)
            return wait_time

    def get_stats(self) -> dict[str, Any]:
        """Returns statistics on rate limits encountered per category."""
        with self._lock:
            return {
                "last_rate_limited_at": self._last_rate_limited_at,
                "is_rate_limited": time.monotonic() < self._rate_limited_until,
                "category_counts": {k.value: v for k, v in self._category_rate_limit_count.items()},
                "last_per_category": {k.value: v for k, v in self._last_rate_limited_per_category.items()},
            }


def rate_limited(category: RateLimitCategory | str | None = None):
    """
    Decorator for BallchasingApi methods to declare their RateLimitCategory
    and ensure proper categorization.
    """
    cat = RateLimitCategory(category) if category else RateLimitCategory.CORE

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs):
            return fn(self, *args, **kwargs)
        wrapper.rate_limit_category = cat
        return wrapper
    return decorator
