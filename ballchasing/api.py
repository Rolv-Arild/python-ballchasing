import os
import time
from datetime import datetime
from typing import Optional, Iterator, Union, List
from urllib.parse import parse_qs, urlparse

from requests import sessions, Response, ConnectionError

from ballchasing.constants import GroupSortBy, SortDir, AnyPlaylist, AnyMap, AnySeason, AnyRank, AnyReplaySortBy, \
    AnySortDir, AnyVisibility, AnyGroupSortBy, AnyPlayerIdentification, AnyTeamIdentification, AnyMatchResult
from .util import rfc3339, replay_cols, team_cols, player_cols, parse_replay

DEFAULT_URL = "https://ballchasing.com/api"


class Api:
    """
    Class for communication with ballchasing.com API (https://ballchasing.com/doc/api)
    """

    def __init__(self, auth_key: str, sleep_time_on_rate_limit: Optional[float] = None,
                 print_on_rate_limit: bool = False, base_url=None, do_initial_ping=True):
        """

        :param auth_key: authentication key for API calls.
        :param sleep_time_on_rate_limit: seconds to wait after being rate limited.
                                         Default value is calculated depending on patron type.
        :param print_on_rate_limit: whether or not to print upon rate limits.
        """
        self.auth_key = auth_key
        self._session = sessions.Session()
        self.steam_name = None
        self.steam_id = None
        self.patron_type = None
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

    def _request(self, url_or_endpoint: str, method: callable, **params) -> Response:
        """
        Helper method for all requests.

        :param url: url or endpoint for request.
        :param method: the method to use.
        :param params: parameters for GET request.
        :return: the request result.
        """
        headers = {"Authorization": self.auth_key}
        url = f"{self.base_url}{url_or_endpoint}" if url_or_endpoint.startswith("/") else url_or_endpoint
        retries = 0
        while True:
            try:
                r = method(url, headers=headers, **params)
                retries = 0
            except ConnectionError as e:
                print("Connection error, trying again in 10 seconds...")
                time.sleep(10)
                retries += 1
                if retries >= 10:
                    raise e
                continue
            if 200 <= r.status_code < 300:
                return r
            elif r.status_code == 429:
                if self.print_on_rate_limit:
                    print(429, url, self.rate_limit_count)
                if self.sleep_time_on_rate_limit:
                    time.sleep(self.sleep_time_on_rate_limit)
                self.rate_limit_count += 1
            else:
                raise ValueError(r, r.json())

    def ping(self):
        """
        Use this API to:

        - check if your API key is correct
        - check if ballchasing API is reachable

        This method runs automatically at initialization and the steam name and id as well as patron type are stored.
        :return: ping response.
        """
        result = self._request("/", self._session.get).json()
        self.steam_name = result["name"]
        self.steam_id = result["steam_id"]
        self.patron_type = result["type"]
        return result

    def get_replays(self, title: Optional[str] = None,
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
                    deep: bool = False
                    ) -> Iterator[dict]:
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
        :return: an iterator over the replays returned by the API.
        """
        url = f"{self.base_url}/replays"
        params = {"title": title, "player-name": player_name, "player-id": player_id, "playlist": playlist,
                  "season": season, "match-result": match_result, "min-rank": min_rank, "max-rank": max_rank,
                  "pro": pro, "uploader": uploader, "group": group_id, "map": map_id,
                  "created-before": rfc3339(created_before), "created-after": rfc3339(created_after),
                  "replay-date-after": rfc3339(replay_after), "replay-date-before": rfc3339(replay_before),
                  "sort-by": sort_by, "sort-dir": sort_dir}
        left = count
        while left > 0:
            request_count = min(left, 200)
            params["count"] = request_count
            d = self._request(url, self._session.get, params=params).json()

            batch = d["list"][:request_count]
            if not deep:
                yield from batch
            else:
                yield from (self.get_replay(r["id"]) for r in batch)

            if "next" not in d:
                break

            next_url = d["next"]
            left -= len(batch)
            params["after"] = parse_qs(urlparse(next_url).query)["after"][0]

    def get_replay(self, replay_id: str) -> dict:
        """
        Retrieve a given replay’s details and stats.

        :param replay_id: the replay id.
        :return: the result of the GET request.
        """
        return self._request(f"/replays/{replay_id}", self._session.get).json()

    def patch_replay(self, replay_id: str, **params) -> None:
        """
        This endpoint can patch one or more fields of the specified replay

        :param replay_id: the replay id.
        :param params: parameters for the PATCH request.
        """
        self._request(f"/replays/{replay_id}", self._session.patch, json=params)

    def upload_replay(self, replay_file, visibility: Optional[AnyVisibility] = None, group: Optional[str] = None) -> dict:
        """
        Use this API to upload a replay file to ballchasing.com.

        :param replay_file: replay file to upload.
        :param visibility: to set the visibility of the uploaded replay.
        :param group: to upload the replay to an existing group.
        :return: the result of the POST request.
        """
        return self._request(f"/v2/upload", self._session.post, files={"file": replay_file},
                             params={"group": group, "visibility": visibility}).json()

    def delete_replay(self, replay_id: str) -> None:
        """
        This endpoint deletes the specified replay.
        WARNING: This operation is permanent and undoable.

        :param replay_id: the replay id.
        """
        self._request(f"/replays/{replay_id}", self._session.delete)

    def get_groups(self, name: Optional[str] = None,
                   creator: Optional[str] = None,
                   group: Optional[str] = None,
                   created_before: Optional[Union[str, datetime]] = None,
                   created_after: Optional[Union[str, datetime]] = None,
                   count: int = 200,
                   sort_by: AnyGroupSortBy = GroupSortBy.CREATED,
                   sort_dir: AnySortDir = SortDir.DESCENDING
                   ) -> Iterator[dict]:
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
        :return: an iterator over the groups returned by the API.
        """
        url = f"{self.base_url}/groups/"
        params = {"name": name, "creator": creator, "group": group, "created-before": rfc3339(created_before),
                  "created-after": rfc3339(created_after), "sort-by": sort_by, "sort-dir": sort_dir}

        left = count
        while left > 0:
            request_count = min(left, 200)
            params["count"] = request_count
            d = self._request(url, self._session.get, params=params).json()

            batch = d["list"][:request_count]
            yield from batch

            if "next" not in d:
                break

            next_url = d["next"]
            left -= len(batch)
            params["after"] = parse_qs(urlparse(next_url).query)["after"][0]

    def create_group(self,
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
        return self._request(f"/groups", self._session.post, json=json).json()

    def get_group(self, group_id: str) -> dict:
        """
        This endpoint retrieves a specific replay group info and stats given its id.

        :param group_id: the group id.
        :return: the group info with stats.
        """
        return self._request(f"/groups/{group_id}", self._session.get).json()

    def patch_group(self, group_id: str, **params) -> None:
        """
        This endpoint can patch one or more fields of the specified group.

        :param group_id: the group id
        :param params: parameters for the PATCH request.
        """
        self._request(f"/groups/{group_id}", self._session.patch, json=params)

    def delete_group(self, group_id: str) -> None:
        """
        This endpoint deletes the specified group.
        WARNING: This operation is permanent and undoable.

        :param group_id: the group id.
        """
        self._request(f"/groups/{group_id}", self._session.delete)

    def get_group_replays(self, group_id: str, deep: bool = False) -> Iterator[dict]:
        """
        Finds all replays in a group, including child groups.

        :param group_id: the base group id.
        :param deep: whether or not to get full stats for each replay (will be much slower).
        :return: an iterator over all the replays in the group.
        """
        child_groups = self.get_groups(group=group_id)
        for child in child_groups:
            for replay in self.get_group_replays(child["id"], deep):
                yield replay
        for replay in self.get_replays(group_id=group_id, deep=deep):
            yield replay

    def download_replay(self, replay_id: str, folder: str):
        """
        Download a replay file.

        :param replay_id: the replay id.
        :param folder: the folder to download into.
        """
        r = self._request(f"/replays/{replay_id}/file", self._session.get)
        with open(f"{folder}/{replay_id}.replay", "wb") as f:
            for ch in r:
                f.write(ch)

    def download_group(self, group_id: str, folder: str, recursive=True):
        """
        Download an entire group.

        :param group_id: the base group id.
        :param folder: the folder in which to create the group folder.
        :param recursive: whether or not to create new folders for child groups.
        """
        folder = os.path.join(folder, group_id)
        if recursive:
            os.makedirs(folder, exist_ok=True)
            for child_group in self.get_groups(group=group_id):
                self.download_group(child_group["id"], folder, True)
            for replay in self.get_replays(group_id=group_id):
                self.download_replay(replay["id"], folder)
        else:
            for replay in self.get_group_replays(group_id):
                self.download_replay(replay["id"], folder)

    def get_maps(self):
        """
        Use this API to get the list of map codes to map names (map as in stadium).
        """
        res = self._request("/maps", self._session.get).json()
        return res

    def generate_tsvs(self, replays: Iterator[Union[dict, str]],
                      path_name: str,
                      player_suffix: Optional[str] = "-players.tsv",
                      team_suffix: Optional[str] = "-teams.tsv",
                      replay_suffix: Optional[str] = "-replays.tsv",
                      sep="\t",
                      ):
        """
        Generates tsv files for players, teams and replay info.

        :param replays: an iterator over either replays (with stats) or replay ids.
        :param path_name: the path to save the files at, including the name prefix.
        :param player_suffix: suffix for the player file. Set to None to disable player file writing.
        :param team_suffix: suffix for the team file. Set to None to disable team file writing.
        :param replay_suffix: suffix for the replay file. Set to None to disable replay file writing.
        :param sep: the separator to use. Default is tab character (tsv).
        """
        player_file = None
        if player_suffix is not None:
            player_file = open(path_name + player_suffix, "w")
            player_file.write(sep.join(player_cols) + "\n")

        team_file = None
        if team_suffix is not None:
            team_file = open(path_name + team_suffix, "w")
            team_file.write(sep.join(team_cols) + "\n")

        replay_file = None
        if replay_suffix is not None:
            replay_file = open(path_name + replay_suffix, "w")
            replay_file.write(sep.join(replay_cols) + "\n")

        for replay in replays:
            if isinstance(replay, str):
                replay = self.get_replay(replay)
            for kind, values in parse_replay(replay):
                values = [str(v) for v in values]
                if kind == "replay" and replay_file is not None:
                    replay_file.write(sep.join(values) + "\n")
                elif kind == "team" and team_file is not None:
                    team_file.write(sep.join(values) + "\n")
                elif kind == "player" and player_file is not None:
                    player_file.write(sep.join(values) + "\n")

    def __str__(self):
        return f"BallchasingApi[key={self.auth_key},name={self.steam_name}," \
               f"steam_id={self.steam_id},type={self.patron_type}]"


if __name__ == '__main__':
    # Basic initial tests
    import sys

    token = sys.argv[1]
    api = Api(token)
    print(api)
    # api.get_replays(season="123")
    # api.delete_replay("a22a8c81-fadd-4453-914e-ae54c2b8391f")
    upload_response = api.upload_replay(open("4E2B22344F748C6EB4922DB8CC8AC282.replay", "rb"))
    replays_response = api.get_replays()
    replay_response = api.get_replay(next(replays_response)["id"])

    groups_response = api.get_groups()
    group_response = api.get_group(next(groups_response)["id"])

    create_group_response = api.create_group(f"test-{time.time()}", "by-id", "by-distinct-players")
    api.patch_group(create_group_response["id"], team_identification="by-player-clusters")

    api.patch_replay(upload_response["id"], group=create_group_response["id"])

    api.delete_group(create_group_response["id"])
    api.delete_replay(upload_response["id"])
    print("Nice")
