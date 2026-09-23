import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Iterator
from urllib.parse import parse_qs, urlparse

from requests import sessions, Response
from requests.exceptions import ConnectionError, Timeout

from ballchasing.constants import GroupSortBy, SortDir, AnySeason, AnyRank, AnyReplaySortBy, AnySortDir, \
    AnyVisibility, AnyGroupSortBy, AnyPlayerIdentification, AnyTeamIdentification, AnyMatchResult, NoneOrMore
from ballchasing.typed import DeepReplay, ShallowReplay, DeepGroup, ShallowGroup
from .typed.shared import BaseGroup, BasicGroup
from .util.dates import to_rfc3339
from .util.iterators import deduplicate as deduplicator
from .util.stats import parse_replay_stats

logger = logging.getLogger("ballchasing")

DEFAULT_URL = "https://ballchasing.com/api"

PATRON_RATE_LIMIT_SLEEP_TIMES = {
    "regular": 3600 / 1000,
    "gold": 3600 / 2000,
    "diamond": 3600 / 5000,
    "champion": 1 / 8,
    "gc": 1 / 16,
}


class BallchasingApi:
    """
    Class for communication with ballchasing.com API (https://ballchasing.com/doc/api)
    """

    def __init__(
            self,
            auth_key: str,
            *,
            sleep_time_on_rate_limit: float | None = None,
            print_on_rate_limit: bool = False,
            base_url: str | None = None,
            do_initial_ping: bool = True,
            typed: bool = False,
    ):
        """

        :param auth_key: authentication key for API calls.
        :param sleep_time_on_rate_limit: seconds to wait after being rate limited.
                                         Default value is calculated depending on patron type.
        :param print_on_rate_limit: whether or not to print upon rate limits.
        """
        self.auth_key = auth_key
        self._session = sessions.Session()
        self._ping_result = None
        self.rate_limit_count = 0
        self.base_url = DEFAULT_URL if base_url is None else base_url
        if do_initial_ping:
            self.ping()
        self._sleep_time_on_rate_limit = sleep_time_on_rate_limit
        self.print_on_rate_limit = print_on_rate_limit
        self.typed = typed

    @property
    def sleep_time_on_rate_limit(self) -> float:
        if self._sleep_time_on_rate_limit is not None:
            return self._sleep_time_on_rate_limit
        if self._ping_result is not None:
            return PATRON_RATE_LIMIT_SLEEP_TIMES.get(self.patron_type or "regular", 3600 / 1000)
        return PATRON_RATE_LIMIT_SLEEP_TIMES["regular"]

    @sleep_time_on_rate_limit.setter
    def sleep_time_on_rate_limit(self, value: float | None):
        self._sleep_time_on_rate_limit = value

    @property
    def steam_name(self):
        if self._ping_result is None:
            self.ping()
        return self._ping_result.get("name")

    @property
    def steam_id(self):
        if self._ping_result is None:
            self.ping()
        return self._ping_result.get("steam_id")

    @property
    def patron_type(self):
        if self._ping_result is None:
            self.ping()
        return self._ping_result.get("type")

    @property
    def quota(self):
        if self._ping_result is None:
            self.ping()
        return self._ping_result.get("quota")

    def _request(
            self,
            url_or_endpoint: str,
            method: str,
            **params
    ) -> Response:
        """
        Helper method for all requests.

        :param url: url or endpoint for request.
        :param method: the method to use.
        :param params: parameters for GET request.
        :return: the request result.
        :raises ConnectionError: if the connection fails after max retries.
        :raises HTTPError: if the request fails with a status code other than 2xx or 429.
        """
        headers = {"Authorization": self.auth_key}
        url = f"{self.base_url}{url_or_endpoint}" if url_or_endpoint.startswith("/") else url_or_endpoint
        max_retries = 8
        retries = 0
        rate_limit_retries = 0
        while True:
            try:
                r: Response = self._session.request(method=method, url=url, headers=headers, **params)
                if 200 <= r.status_code < 300:
                    return r
                elif r.status_code == 429:
                    self.rate_limit_count += 1
                    if self.print_on_rate_limit:
                        logger.warning(f"Rate limited at {url} ({self.rate_limit_count} total rate limits)")
                    else:
                        logger.debug(f"Rate limited at {url} ({self.rate_limit_count} total rate limits)")
                    rate_limit_retries += 1
                    if rate_limit_retries > max_retries:
                        r.raise_for_status()
                    retry_after = r.headers.get("Retry-After", '0')
                    retry_after = int(retry_after) if retry_after.isdigit() else None
                    if retry_after:  # integer > 0
                        time.sleep(retry_after)
                    elif self.sleep_time_on_rate_limit:
                        time.sleep(self.sleep_time_on_rate_limit)
                    else:
                        time.sleep(max(1.0, float(2 ** (rate_limit_retries - 1))))
                elif r.status_code in (502, 503, 504):
                    raise ConnectionError(f"Server error {r.status_code}: {r.reason or 'Transient gateway error'}")
                else:
                    r.raise_for_status()  # Raise an error for any other status code
            except (ConnectionError, Timeout) as e:
                if retries >= max_retries - 1:
                    raise e
                s = 2 ** retries
                logger.warning(f"Connection or timeout error ({e}), trying again in {s} seconds...")
                time.sleep(s)
                retries += 1

    def ping(self) -> dict:
        """
        Use this API to:

        - check if your API key is correct
        - check if ballchasing API is reachable

        This method runs automatically at initialization and the steam name and id as well as patron type are stored.
        :return: ping response.
        """
        result = self._request("/", "GET").json()
        self._ping_result = result
        return result

    def _iterable_from_request(self, url, params, prefetch=True):
        # Shared by get_replays and get_groups.
        # When prefetch=True, the next page is requested in a background
        # thread *before* yielding, so network I/O overlaps with the
        # consumer processing items.  When prefetch=False (e.g. deep mode
        # where the consumer also makes API calls), the next request is
        # submitted *after* yielding to avoid doubling the request rate.
        remaining = params.get("count", 0)
        if remaining <= 0:
            return

        def fetch_page(p):
            return self._request(url, "GET", params=p).json()

        with ThreadPoolExecutor(max_workers=1) as executor:
            params["count"] = min(remaining, 200)
            future = executor.submit(fetch_page, dict(params))

            while remaining > 0:
                d = future.result()
                batch = d.get("list", [])[:min(remaining, 200)]
                remaining -= len(batch)

                next_url = d.get("next")
                has_next = bool(next_url) and remaining > 0
                if has_next:
                    after_param = parse_qs(urlparse(next_url).query).get("after", [None])[0]
                    if after_param is not None:
                        params["after"] = after_param
                    else:
                        has_next = False
                    params["count"] = min(remaining, 200)
                    if prefetch and has_next:
                        future = executor.submit(fetch_page, dict(params))

                yield from batch

                if not has_next:
                    break
                if not prefetch:
                    future = executor.submit(fetch_page, dict(params))

    def get_replays(
            self,
            *,
            title: NoneOrMore[str] = None,
            player_name: NoneOrMore[str] = None,
            player_id: NoneOrMore[str] = None,
            playlist: NoneOrMore[str] = None,
            season: NoneOrMore[AnySeason] = None,
            match_result: NoneOrMore[AnyMatchResult] = None,
            min_rank: AnyRank | None = None,
            max_rank: AnyRank | None = None,
            pro: bool | None = None,
            uploader: str | None = None,
            group_id: NoneOrMore[str] = None,
            map_id: NoneOrMore[str] = None,
            created_before: str | datetime | None = None,
            created_after: str | datetime | None = None,
            replay_after: str | datetime | None = None,
            replay_before: str | datetime | None = None,
            count: int = 150,
            sort_by: AnyReplaySortBy | None = None,
            sort_dir: AnySortDir = SortDir.DESCENDING,
            deep: bool = False,
            typed: bool | None = None,
            deduplicate: bool = False,
            disable_prefetch: bool | None = None,
    ) -> Iterator[dict | ShallowReplay | DeepReplay]:
        """
        This endpoint lets you filter and retrieve replays. The implementation returns an iterator.

        :param title: filter replays by title.
        :param player_name: filter replays by a player’s name.
        :param player_id: filter replays by a player’s platform id in the $platform:$id, e.g. steam:76561198141161044,
        ps4:gamertag, … You can filter replays by multiple player ids, e.g ?player-id=steam:1&player-id=steam:2
        :param playlist: filter replays by one or more playlists.
        :param season: filter replays by season. Must be a number between 1 and 14 (for old seasons)
                       or f1, f2, … for the new free to play seasons
        :param match_result: filter your replays by result.
        :param min_rank: filter your replays based on players minimum rank.
        :param max_rank: filter your replays based on players maximum rank.
        :param pro: only include replays containing at least one pro player.
        :param uploader: only include replays uploaded by the specified user. Accepts either the
                         numerical 76*************44 steam id, or the special value 'me'
        :param group_id: only include replays belonging to the specified group. This only include replays immediately
                         under the specified group, but not replays in child groups
        :param map_id: only include replays in the specified map. Check get_maps for the list of valid map codes
        :param created_before: only include replays created (uploaded) before some date.
                               RFC3339 format, e.g. '2020-01-02T15:00:05+01:00'
        :param created_after: only include replays created (uploaded) after some date.
                              RFC3339 format, e.g. '2020-01-02T15:00:05+01:00'
        :param replay_after: only include replays for games that happened after some date.
                             RFC3339 format, e.g. '2020-01-02T15:00:05+01:00'
        :param replay_before: only include replays for games that happened before some date.
                              RFC3339 format, e.g. '2020-01-02T15:00:05+01:00'
        :param count: returns at most count replays. Since the implementation uses an iterator it supports iterating
                      past the limit of 200 set by the API
        :param sort_by: sort replays according the selected field
        :param sort_dir: sort direction
        :param deep: whether to get full stats for each replay (will be much slower).
        :param typed: whether to return a typed object (default is self.typed).
        :param deduplicate: whether to deduplicate replays that seem to be the same game.
        :param disable_prefetch: whether to disable prefetching replays.
        :return: an iterator over the replays returned by the API.
        """
        url = f"{self.base_url}/replays"
        params = {"title": title, "player-name": player_name, "player-id": player_id, "playlist": playlist,
                  "season": season, "match-result": match_result, "min-rank": min_rank, "max-rank": max_rank,
                  "pro": str(pro).lower() if isinstance(pro, bool) else pro, "uploader": uploader, "group": group_id,
                  "map": map_id,
                  "created-before": to_rfc3339(created_before), "created-after": to_rfc3339(created_after),
                  "replay-date-after": to_rfc3339(replay_after), "replay-date-before": to_rfc3339(replay_before),
                  "count": count, "sort-by": sort_by, "sort-dir": sort_dir}

        if typed is None:
            typed = self.typed

        if disable_prefetch is None:
            disable_prefetch = deep

        iterator = self._iterable_from_request(url, params, prefetch=not disable_prefetch)
        if deduplicate:
            # Deep replays have match and replay IDs to deduplicate with. For shallow replays we check dates.
            iterator = deduplicator(iterator, check_dates=not deep)
        if deep:
            iterator = (self.get_replay(r["id"]) for r in iterator)
        if typed:
            if deep:
                iterator = (DeepReplay(**r) for r in iterator)
            else:
                iterator = (ShallowReplay(**r) for r in iterator)
        yield from iterator

    def get_replay(self, replay_id: str, *, typed: bool | None = None) -> dict | DeepReplay:
        """
        Retrieve a given replay’s details and stats.

        :param replay_id: the replay id.
        :param typed: whether to return a typed object (default is self.typed).
        :return: the result of the GET request.
        """
        result = self._request(f"/replays/{replay_id}", "GET").json()
        if typed is None:
            typed = self.typed
        if typed:
            result = DeepReplay(**result)
        return result

    def patch_replay(self, replay_id: str, **params) -> None:
        """
        This endpoint can patch one or more fields of the specified replay

        :param replay_id: the replay id.
        :param params: parameters for the PATCH request.
        """
        self._request(f"/replays/{replay_id}", "PATCH", json=params)

    def upload_replay(
            self,
            replay_file: str | Path | BinaryIO,
            *,
            visibility: AnyVisibility | None = None,
            group: str | None = None
    ) -> dict:
        """
        Use this API to upload a replay file to ballchasing.com.

        :param replay_file: replay file to upload. Can be a file path (str or Path) or a file-like object.
        :param visibility: to set the visibility of the uploaded replay.
        :param group: to upload the replay to an existing group.
        :return: the result of the POST request.
        """
        if isinstance(replay_file, (str, Path)):
            with open(replay_file, "rb") as f:
                return self.upload_replay(f, visibility=visibility, group=group)
        return self._request(f"/v2/upload", "POST", files={"file": replay_file},
                             params={"group": group, "visibility": visibility}).json()

    def delete_replay(self, replay_id: str) -> None:
        """
        This endpoint deletes the specified replay.
        WARNING: This operation is permanent and undoable.

        :param replay_id: the replay id.
        """
        self._request(f"/replays/{replay_id}", "DELETE")

    def get_groups(
            self,
            *,
            name: str | None = None,
            creator: str | None = None,
            group: str | None = None,
            created_before: str | datetime | None = None,
            created_after: str | datetime | None = None,
            count: int = 200,
            sort_by: AnyGroupSortBy = GroupSortBy.CREATED,
            sort_dir: AnySortDir = SortDir.DESCENDING,
            deep: bool = False,
            typed: bool | None = None,
            disable_prefetch: bool | None = None,
    ) -> Iterator[dict | ShallowGroup | DeepGroup]:
        """
        This endpoint lets you filter and retrieve replay groups.

        :param name: filter groups by name
        :param creator: only include groups created by the specified user.
                        Accepts either the numerical 76*************44 steam id, or the special value me
        :param group: only include children of the specified group
        :param created_before: only include groups created (uploaded) before some date.
                               RFC3339 format, e.g. 2020-01-02T15:00:05+01:00
        :param created_after: only include groups created (uploaded) after some date.
                              RFC3339 format, e.g. 2020-01-02T15:00:05+01:00
        :param count: returns at most count groups. Since the implementation uses an iterator it supports iterating
                      past the limit of 200 set by the API
        :param sort_by: Sort groups according the selected field.
        :param sort_dir: Sort direction.
        :param deep: whether to get full stats for each group (will be much slower).
        :param typed: whether to return a typed object (default is self.typed).
        :param disable_prefetch: whether to disable prefetching.
        :return: an iterator over the groups returned by the API.
        """
        url = f"{self.base_url}/groups/"
        params = {"name": name, "creator": creator, "group": group, "created-before": to_rfc3339(created_before),
                  "created-after": to_rfc3339(created_after), "count": count, "sort-by": sort_by, "sort-dir": sort_dir}

        if disable_prefetch is None:
            disable_prefetch = deep

        iterator = self._iterable_from_request(url, params, prefetch=not disable_prefetch)
        if typed is None:
            typed = self.typed
        if deep:
            iterator = (self.get_group(g["id"], typed=typed) for g in iterator)
        elif typed:
            iterator = (ShallowGroup(**g) for g in iterator)
        yield from iterator

    def create_group(
            self,
            *,
            name: str,
            player_identification: AnyPlayerIdentification,
            team_identification: AnyTeamIdentification,
            parent: str | None = None
    ) -> dict:
        """
        Use this API to create a new replay group.

        :param name: the new group name.
        :param player_identification: how to identify the same player across multiple replays.
                                      Some tournaments (e.g. RLCS) make players use a pool of generic Steam accounts,
                                      meaning the same player could end up using 2 different accounts in 2 series.
                                      That's when the `by-name` comes in handy
        :param team_identification: How to identify the same team across multiple replays.
                                    Set to `by-distinct-players` if teams have a fixed roster of players for
                                    every single game. In some tournaments/leagues, teams allow player rotations,
                                    or a sub can replace another player, in which case use `by-player-clusters`.
        :param parent: if set,the new group will be created as a child of the specified group
        :return: the result of the POST request.
        """
        json = {"name": name, "player_identification": player_identification,
                "team_identification": team_identification, "parent": parent}
        return self._request(f"/groups", "POST", json=json).json()

    def get_group(
            self,
            group_id: str,
            *,
            typed: bool | None = None
    ) -> dict | DeepGroup:
        """
        This endpoint retrieves a specific replay group info and stats given its id.

        :param group_id: the group id.
        :param typed: whether to return a typed object (default is self.typed).
        :return: the group info with stats.
        """
        result = self._request(f"/groups/{group_id}", "GET").json()
        if typed is None:
            typed = self.typed
        if typed:
            result = DeepGroup(**result)
        return result

    def patch_group(self, group_id: str, **params) -> None:
        """
        This endpoint can patch one or more fields of the specified group.

        :param group_id: the group id
        :param params: parameters for the PATCH request.
        """
        self._request(f"/groups/{group_id}", "PATCH", json=params)

    def delete_group(self, group_id: str) -> None:
        """
        This endpoint deletes the specified group.
        WARNING: This operation is permanent and undoable.

        :param group_id: the group id.
        """
        self._request(f"/groups/{group_id}", "DELETE")

    def get_group_replays(
            self,
            group: str | dict | BasicGroup,
            *,
            deep: bool = False,
            typed: bool | None = None
    ) -> Iterator[dict | ShallowReplay | DeepReplay]:
        """
        Finds all replays in a group, including child groups.

        :param group: the base group id, group dict, or BaseGroup object.
        :param deep: whether or not to get full stats for each replay (will be much slower).
        :param typed: whether to return a typed object (default is self.typed).
        :return: an iterator over all the replays in the group.
        """
        for path, replay in self.get_group_tree(group, deep=deep, typed=typed):
            yield replay

    def get_group_tree(
            self,
            group: str | dict | BaseGroup,
            *,
            deep: bool = False,
            typed: bool | None = None
    ) -> Iterator[tuple[list[str], dict | ShallowReplay | DeepReplay]]:
        """
        Finds all replays in a group, and includes the group path leading up to each replay.

        :param group: the group id or a group dict.
        :param deep: whether to get full stats for each replay and group (will be much slower).
        :param typed: whether to return a typed object (default is self.typed).
        :return: an iterator of (path, replay) tuples, where path is a list of group ids.
        """
        if isinstance(group, str):
            group_id = group
        elif isinstance(group, BasicGroup):
            group_id = group.id
        else:
            group_id = group["id"]
        child_groups = self.get_groups(group=group_id, typed=typed)
        for child in child_groups:
            for path, replay in self.get_group_tree(child, deep=deep, typed=typed):
                yield [group_id] + path, replay
        for replay in self.get_replays(group_id=group_id, deep=deep, typed=typed):
            yield [group_id], replay

    def download_replay(self, replay_id: str, path: str):
        """
        Download a replay file.

        :param replay_id: the replay id.
        :param path: the path to download the replay to. Can be a file path or a directory.
        """
        r = self._request(f"/replays/{replay_id}/file", "GET")
        if os.path.isdir(path):
            # If path is a directory, use the replay id as the filename
            filename = f"{replay_id}.replay"
            path = os.path.join(path, filename)
        with open(path, "wb") as f:
            f.write(r.content)

    def download_group(self, group_id: str, folder: str, *, keep_tree_structure=True):
        """
        Download an entire group.

        :param group_id: the base group id.
        :param folder: the folder in which to create the group folder.
        :param keep_tree_structure: whether to create new folders for child groups.
        """
        folder = os.path.join(folder, group_id)
        if keep_tree_structure:
            os.makedirs(folder, exist_ok=True)
            for child_group in self.get_groups(group=group_id):
                self.download_group(child_group["id"], folder, keep_tree_structure=True)
            for replay in self.get_replays(group_id=group_id):
                self.download_replay(replay["id"], folder)
        else:
            for replay in self.get_group_replays(group_id):
                self.download_replay(replay["id"], folder)

    def get_maps(self):
        """
        Use this API to get the list of map codes to map names (map as in stadium).
        """
        res = self._request("/maps", "GET").json()
        return res

    def get_stats(self, replay: dict | str):
        """
        Gets stats for players, teams and replay info.

        :param replay: the replay to get stats for. Can be a replay id (str) or a replay dict.
        :return: a dictionary containing replay, team and player stats.
        """

        if isinstance(replay, str):
            replay = self.get_replay(replay, typed=False)
        elif isinstance(replay, dict) and "title" not in replay:
            replay = self.get_replay(replay["id"], typed=False)

        stats = parse_replay_stats(replay)
        return stats

    def __repr__(self):
        return f"BallchasingApi(key={self.auth_key},name={self.steam_name}," \
               f"steam_id={self.steam_id},type={self.patron_type})"
