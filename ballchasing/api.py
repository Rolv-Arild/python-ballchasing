import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, List, BinaryIO, Iterator
from urllib.parse import parse_qs, urlparse

from requests import sessions, Response, ConnectionError, HTTPError

from ballchasing.constants import GroupSortBy, SortDir, AnyPlaylist, AnyMap, AnySeason, AnyRank, AnyReplaySortBy, \
    AnySortDir, AnyVisibility, AnyGroupSortBy, AnyPlayerIdentification, AnyTeamIdentification, AnyMatchResult
from ballchasing.typed import DeepReplay, ShallowReplay, DeepGroup, ShallowGroup
from .typed.shared import BaseGroup, BasicGroup
from .util import to_rfc3339, parse_replay_stats

DEFAULT_URL = "https://ballchasing.com/api"


class BallchasingApi:
    """
    Class for communication with ballchasing.com API (https://ballchasing.com/doc/api)
    """

    def __init__(
            self,
            auth_key: str,
            *,
            sleep_time_on_rate_limit: Optional[float] = None,
            print_on_rate_limit: bool = False,
            base_url=None,
            do_initial_ping=True,
            typed=False,
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
        if sleep_time_on_rate_limit is None:
            self.sleep_time_on_rate_limit = {
                "regular": 3600 / 1000,
                "gold": 3600 / 2000,
                "diamond": 3600 / 5000,
                "champion": 1 / 8,
                "gc": 1 / 16
            }.get(self.patron_type or "regular")
        else:
            self.sleep_time_on_rate_limit = sleep_time_on_rate_limit
        self.print_on_rate_limit = print_on_rate_limit
        self.typed = typed

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
        while True:
            try:
                r: Response = self._session.request(method=method, url=url, headers=headers, **params)
                if 200 <= r.status_code < 300:
                    return r
                elif r.status_code == 429:
                    self.rate_limit_count += 1
                    if self.print_on_rate_limit:
                        print(f"Rate limited at {url} ({self.rate_limit_count} total rate limits)")
                    retry_after = r.headers.get("Retry-After", '0')
                    retry_after = int(retry_after) if retry_after.isdigit() else None
                    if retry_after:  # integer > 0
                        time.sleep(retry_after)
                    elif self.sleep_time_on_rate_limit:
                        time.sleep(self.sleep_time_on_rate_limit)
                else:
                    r.raise_for_status()  # Raise an error for any other status code'
            except ConnectionError as e:
                if retries >= max_retries - 1:
                    raise e
                s = 2 ** retries
                print(f"Connection error, trying again in {s} seconds...")
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

    def _iterable_from_request(self, url, params):
        # Shared by get_replays and get_groups
        remaining = params["count"]
        # return_length = True
        while remaining > 0:
            request_count = min(remaining, 200)
            params["count"] = request_count
            try:
                d = self._request(url, "GET", params=params).json()
            except HTTPError as e:
                if e.response.status_code == 504:
                    # Gateway Timeout, retry
                    time.sleep(5)
                    continue
                else:
                    raise e

            batch = d["list"][:request_count]
            yield from batch

            if "next" not in d:
                break

            next_url = d["next"]
            remaining -= len(batch)
            params["after"] = parse_qs(urlparse(next_url).query)["after"][0]

    def get_replays(
            self,
            *,
            title: Optional[str] = None,
            player_name: Optional[Union[str, List[str]]] = None,
            player_id: Optional[Union[str, List[str]]] = None,
            playlist: Optional[Union[AnyPlaylist, List[AnyPlaylist]]] = None,
            season: Optional[Union[AnySeason, List[AnySeason]]] = None,
            match_result: Optional[Union[AnyMatchResult, List[AnyMatchResult]]] = None,
            min_rank: Optional[AnyRank] = None,
            max_rank: Optional[AnyRank] = None,
            pro: Optional[bool] = None,
            uploader: Optional[str] = None,
            group_id: Optional[Union[str, List[str]]] = None,
            map_id: Optional[Union[AnyMap, List[AnyMap]]] = None,
            created_before: Optional[Union[str, datetime]] = None,
            created_after: Optional[Union[str, datetime]] = None,
            replay_after: Optional[Union[str, datetime]] = None,
            replay_before: Optional[Union[str, datetime]] = None,
            count: int = 150,
            sort_by: Optional[AnyReplaySortBy] = None,
            sort_dir: AnySortDir = SortDir.DESCENDING,
            deep: bool = False,
            typed: Optional[bool] = None,
    ) -> Iterator[Union[dict, ShallowReplay, DeepReplay]]:
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
        :return: an iterator over the replays returned by the API.
        """
        url = f"{self.base_url}/replays"
        params = {"title": title, "player-name": player_name, "player-id": player_id, "playlist": playlist,
                  "season": season, "match-result": match_result, "min-rank": min_rank, "max-rank": max_rank,
                  "pro": pro, "uploader": uploader, "group": group_id, "map": map_id,
                  "created-before": to_rfc3339(created_before), "created-after": to_rfc3339(created_after),
                  "replay-date-after": to_rfc3339(replay_after), "replay-date-before": to_rfc3339(replay_before),
                  "count": count, "sort-by": sort_by, "sort-dir": sort_dir}

        if typed is None:
            typed = self.typed

        iterator = self._iterable_from_request(url, params)
        if deep:
            iterator = (self.get_replay(r["id"], typed=typed) for r in iterator)
        elif typed:
            iterator = (ShallowReplay(**r) for r in iterator)
        yield from iterator

    def get_replay(self, replay_id: str, *, typed: Optional[bool] = None) -> Union[dict, DeepReplay]:
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
            replay_file: Union[str, Path, BinaryIO],
            *,
            visibility: Optional[AnyVisibility] = None,
            group: Optional[str] = None
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
            name: Optional[str] = None,
            creator: Optional[str] = None,
            group: Optional[str] = None,
            created_before: Optional[Union[str, datetime]] = None,
            created_after: Optional[Union[str, datetime]] = None,
            count: int = 200,
            sort_by: AnyGroupSortBy = GroupSortBy.CREATED,
            sort_dir: AnySortDir = SortDir.DESCENDING,
            deep: bool = False,
            typed: bool = None,
    ) -> Iterator[Union[dict, ShallowGroup, DeepGroup]]:
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
        :return: an iterator over the groups returned by the API.
        """
        url = f"{self.base_url}/groups/"
        params = {"name": name, "creator": creator, "group": group, "created-before": to_rfc3339(created_before),
                  "created-after": to_rfc3339(created_after), "count": count, "sort-by": sort_by, "sort-dir": sort_dir}
        iterator = self._iterable_from_request(url, params)
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
            parent: Optional[str] = None
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
            typed: Optional[bool] = None
    ) -> Union[dict, DeepGroup]:
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
            group: Union[str, dict, BasicGroup],
            *,
            deep: bool = False,
            typed: Optional[bool] = None
    ) -> Iterator[Union[dict, ShallowReplay, DeepReplay]]:
        """
        Finds all replays in a group, including child groups.

        :param group: the base group id, group dict, or BaseGroup object.
        :param deep: whether or not to get full stats for each replay (will be much slower).
        :param typed: whether to return a typed object (default is self.typed).
        :return: an iterator over all the replays in the group.
        """
        for path in self.get_group_tree(group, deep=deep, typed=typed):
            group, replay = path
            yield replay

    def get_group_tree(
            self,
            group: Union[str, dict, BaseGroup],
            *,
            deep: bool = False,
            typed: Optional[bool] = None
    ):
        """
        Finds all replays in a group, and includes the groups leading up to the replays.
        :param group: the group id or a group dict.
        :param deep: whether to get full stats for each replay and group (will be much slower).
        :param typed: whether to return a typed object (default is self.typed).
        """
        if isinstance(group, str):
            group = self.get_group(group)
        if isinstance(group, BasicGroup):
            group_id = group.id
        else:
            group_id = group["id"]
        child_groups = self.get_groups(group=group_id, typed=typed)
        for child in child_groups:
            for path in self.get_group_tree(child, deep=deep, typed=typed):
                yield group_id, *path
        for replay in self.get_replays(group_id=group_id, deep=deep, typed=typed):
            yield group_id, replay

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

    def get_stats(self, replay: Union[dict, str]):
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
