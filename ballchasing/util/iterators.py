import bisect
import heapq
import logging
from datetime import timedelta

from ballchasing.constants import ReplaySortBy, SortDir
from .dates import from_rfc3339
from .replays import get_players, get_pid, ID_KEYS


def deduplicate_single(replay, seen_replays) -> str | None:
    # Check if any of the ID keys are already seen, and return the first one that is
    for key in ID_KEYS:
        val = replay.get(key)
        if val is None:
            continue
        if val in seen_replays:
            return key
        seen_replays.add(val)
    return None


def deduplicate(replays, check_dates=False):
    seen_replays = set()

    appearances = {}

    def add_appearance(pid, start, end):
        # Track replay time span for each player, and check for overlaps with previous replays
        apps = appearances.setdefault(pid, [])
        key = (start, end)
        # (t1, t2), (t3, t4), ... where t1 < t2 < t3 < t4 < ...
        idx = bisect.bisect_left(apps, key)
        # Check for overlap with previous interval
        if idx > 0 and apps[idx - 1][1] > start:
            return True
        # Check for overlap with next interval
        if idx < len(apps) and apps[idx][0] < end:
            return True
        apps.insert(idx, key)
        return False

    for replay in replays:
        # First, check
        already_exists = deduplicate_single(replay, seen_replays)
        if already_exists:
            logging.info("Replay %s shares '%s' with a previous replay, skipping", replay["id"], already_exists)
            continue

        # If we want to check dates, track appearances of each player
        if check_dates:
            date = from_rfc3339(replay["date"])
            start_time = date - timedelta(seconds=replay.get("duration", 0))
            overlaps = False
            for player in get_players(replay):
                pid = get_pid(player)
                overlaps = add_appearance(pid, start_time, date)
                if overlaps:
                    rid = replay["id"]
                    logging.info("Replay %s overlaps with a previous replay for player %s, skipping", rid, pid)
                    break
            if overlaps:
                continue
        # logging.debug("Found no duplicates for replay %s", replay["id"])
        yield replay


def _get_sorting_key_fn(sort_by, sort_dir):
    if sort_by == ReplaySortBy.REPLAY_DATE:
        key = "date"
    elif sort_by == ReplaySortBy.UPLOAD_DATE:
        key = "created"
    else:
        raise ValueError(f"Unsupported sort_by: {sort_by}")

    if sort_dir == SortDir.DESC:
        return lambda r: -from_rfc3339(r[key]).timestamp()
    elif sort_dir == SortDir.ASC:
        return lambda r: from_rfc3339(r[key]).timestamp()
    else:
        raise ValueError(f"Unsupported sort_dir: {sort_dir}")


# Note that the default in ballchasing is to sort descending by upload date, so we use that as the default here as well

def ensure_sorted(replays, sort_dir=SortDir.DESC, sort_by=ReplaySortBy.UPLOAD_DATE, buffer_size=1_000):
    """
    Ensures that the replays are sorted by date.
    It maintains a buffer of the specified size and yields replays in sorted order.
    """
    key_fn = _get_sorting_key_fn(sort_by, sort_dir)

    # Initial replays
    buffer = []
    for i, replay in enumerate(replays):
        # Date first, index to prevent collisions, then the replay itself
        item = (key_fn(replay), i, replay)  # To make it sortable
        if len(buffer) >= buffer_size:
            yield heapq.heappop(buffer)[2]  # Yield the smallest item
        heapq.heappush(buffer, item)
    # Exhaust the buffer
    while buffer:
        yield heapq.heappop(buffer)[2]


def mix_replay_iterators(*iterables, sort_dir=SortDir.DESC, sort_by=ReplaySortBy.UPLOAD_DATE):
    """
    Merges multiple replay iterators while maintaining the specified sort order.
    This is useful for merging multiple sources of replays while ensuring the final output is sorted.
    The input iterables must already be sorted by the same key and direction.
    """
    key_fn = _get_sorting_key_fn(sort_by, sort_dir)

    it = heapq.merge(
        *iterables,
        key=key_fn,
    )
    yield from it
