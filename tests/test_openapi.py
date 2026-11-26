"""
Tests against the ballchasing.com OpenAPI document (tests/data/openapi.json, a snapshot of
https://ballchasing.com/doc/api/openapi.json). Refresh it with `python scripts/check_api_spec.py --update`.
"""
import dataclasses
import io
import json
import typing
from pathlib import Path
from unittest.mock import patch

import pytest
from requests.exceptions import HTTPError

from ballchasing import constants
from ballchasing.api import BallchasingApi, PATRON_RATE_LIMIT_SLEEP_TIMES
from ballchasing.exceptions import AccountRestrictedError, DailyDownloadLimitError, QuotaExceededError, \
    UploadQuotaError
from ballchasing.rate_limit import RateLimiter, RateLimitCategory, CATEGORY_HOURLY_SLEEP_TIMES
from ballchasing.typed import DeepReplay, ShallowReplay, DeepGroup, ShallowGroup
from ballchasing.util.stats import get_stats_info, parse_replay_stats
from tests.test_fixes import make_mock_response

SPEC = json.loads((Path(__file__).parent / "data" / "openapi.json").read_text(encoding="utf-8"))


def resolve(schema):
    while isinstance(schema, dict) and "$ref" in schema:
        node = SPEC
        for part in schema["$ref"].lstrip("#/").split("/"):
            node = node[part]
        schema = node
    return schema


def properties(schema) -> dict:
    schema = resolve(schema)
    props = {}
    for sub in schema.get("allOf", []) + schema.get("oneOf", []) + schema.get("anyOf", []):
        props.update(properties(sub))
    props.update(schema.get("properties", {}))
    return props


def item_schema(schema):
    """The element schema of an array (or of the array/object variant of a union), else the schema itself."""
    schema = resolve(schema)
    if "items" in schema:
        return resolve(schema["items"])
    for sub in schema.get("oneOf", []) + schema.get("anyOf", []):
        sub = resolve(sub)
        if sub.get("type") == "array":
            return resolve(sub["items"])
        if sub.get("properties") or sub.get("allOf"):
            return sub
    return schema


def enum_values(schema) -> set | None:
    schema = resolve(schema)
    if "enum" in schema:
        return set(schema["enum"])
    if "items" in schema:
        return enum_values(schema["items"])
    for sub in schema.get("oneOf", []) + schema.get("anyOf", []):
        if values := enum_values(sub):
            return values
    return None


def response_schema(path, method="get", status="200"):
    response = resolve(SPEC["paths"][path][method]["responses"][status])
    return resolve(response["content"]["application/json"]["schema"])


def query_param(path, method, name):
    for param in SPEC["paths"][path][method].get("parameters", []):
        param = resolve(param)
        if param["name"] == name:
            return param["schema"]
    raise KeyError(name)


def literals(type_alias) -> set:
    return set(typing.get_args(typing.get_args(type_alias)[1]))


def unwrap(type_):
    while args := typing.get_args(type_):
        type_ = [a for a in args if a is not type(None)][0]
    return type_


def missing_fields(cls, schema, path) -> list[str]:
    """Properties of the response schema that the dataclass (recursively) has no field for."""
    props = properties(schema)
    if not dataclasses.is_dataclass(cls) or not props:
        return []
    hints = typing.get_type_hints(cls)
    names = {f.name for f in dataclasses.fields(cls)}
    missing = []
    for name, sub in props.items():
        if name not in names:
            missing.append(f"{path}.{name} ({cls.__name__})")
        else:
            missing += missing_fields(unwrap(hints[name]), item_schema(sub), f"{path}.{name}")
    return missing


class TestTypedModelsCoverSpec:
    @pytest.mark.parametrize("cls, schema, path", [
        (DeepReplay, lambda: response_schema("/replays/{id}"), "Replay"),
        (ShallowReplay, lambda: item_schema(properties(response_schema("/replays"))["list"]), "ReplayList[]"),
        (DeepGroup, lambda: response_schema("/groups/{id}"), "Group"),
        (ShallowGroup, lambda: item_schema(properties(response_schema("/groups"))["list"]), "GroupList[]"),
    ])
    def test_every_response_field_has_a_dataclass_field(self, cls, schema, path):
        assert missing_fields(cls, schema(), path) == []


class TestTypedModelsTolerateUnknownFields:
    def test_unknown_fields_are_kept_not_fatal(self):
        replay = DeepReplay(id="r1", some_future_field=1, blue={"name": "B", "another_new_one": "x"})
        assert replay.id == "r1"
        assert replay._extra == {"some_future_field": 1}
        assert replay.blue._extra == {"another_new_one": "x"}

    def test_to_dict_includes_unknown_fields(self):
        d = ShallowReplay(id="r1", some_future_field={"a": 1}).to_dict()
        assert d["some_future_field"] == {"a": 1}
        assert d["id"] == "r1"

    def test_unknown_field_not_in_equality_or_repr(self):
        a = DeepGroup(id="g", status="ok", new_field=1)
        b = DeepGroup(id="g", status="ok", new_field=2)
        assert a == b
        assert "new_field" not in repr(a)

    def test_new_group_fields(self):
        g = DeepGroup(id="g", dedup=True, duplicates={"total_replays": 3, "duplicate_replays": 1, "unique_games": 2})
        assert g.dedup is True
        assert g.duplicates.unique_games == 2


class TestConstantsMatchSpec:
    @pytest.mark.parametrize("type_alias, schema", [
        (constants.AnyPlaylist, lambda: query_param("/replays", "get", "playlist")),
        (constants.AnyRank, lambda: query_param("/replays", "get", "min-rank")),
        (constants.AnyMatchResult, lambda: query_param("/replays", "get", "match-result")),
        (constants.AnyReplaySortBy, lambda: query_param("/replays", "get", "sort-by")),
        (constants.AnySortDir, lambda: query_param("/replays", "get", "sort-dir")),
        (constants.AnyGroupSortBy, lambda: query_param("/groups", "get", "sort-by")),
        (constants.AnyVisibility, lambda: query_param("/v2/upload", "post", "visibility")),
        (constants.AnyPlayerIdentification,
         lambda: SPEC["components"]["schemas"]["GroupCreate"]["properties"]["player_identification"]),
        (constants.AnyTeamIdentification,
         lambda: SPEC["components"]["schemas"]["GroupCreate"]["properties"]["team_identification"]),
    ])
    def test_enum(self, type_alias, schema):
        assert literals(type_alias) == enum_values(schema())

    def test_every_patron_type_has_rate_limits(self):
        account_types = enum_values(SPEC["components"]["schemas"]["Ping"]["properties"]["type"]) - {"admin"}
        assert account_types <= set(CATEGORY_HOURLY_SLEEP_TIMES)
        assert account_types <= set(PATRON_RATE_LIMIT_SLEEP_TIMES)


class TestStats:
    def test_stats_info_loads(self):
        assert "aerial_hits" in {stat["name"] for stat in get_stats_info().values()}

    def test_team_stats_not_shadowed_by_player_stats(self):
        core = {"goals": 3, "aerial_hits": 2}
        team = {"name": "t", "players": [], "stats": {"core": core}}
        stats = parse_replay_stats({"id": "r", "blue": team, "orange": team})
        assert stats["teams"]["blue"]["goals"] == 3 and stats["teams"]["blue"]["aerial_hits"] == 2

    def test_parse_replay_stats(self):
        core = {"shots": 1, "goals": 1, "aerial_hits": 2}
        player = {"name": "p", "id": {"platform": "steam", "id": "1"}, "stats": {"core": core}}
        team = {"name": "t", "players": [player], "stats": {"core": core}}
        stats = parse_replay_stats({"id": "r", "blue": team, "orange": {**team, "players": []}})
        assert stats["players"]["steam:1"]["aerial_hits"] == 2


@pytest.fixture
def api():
    return BallchasingApi("dummy_key", do_initial_ping=False)


def sent(mock_request, call=-1):
    return mock_request.call_args_list[call][1]


class TestNewParameters:
    def test_upload_date_sort_is_sent_as_created(self, api):
        with patch.object(api._session, "request", return_value=make_mock_response(json_data={"list": []})) as m:
            list(api.get_replays(sort_by=constants.ReplaySortBy.UPLOAD_DATE, count=1, disable_prefetch=True))
            assert sent(m)["params"]["sort-by"] == "created"

    def test_roulette(self, api):
        with patch.object(api._session, "request", return_value=make_mock_response(json_data={"list": []})) as m:
            list(api.get_replays(roulette=True, count=1, disable_prefetch=True))
            assert sent(m)["params"]["roulette"] == "true"

    def test_get_replay_through_shared_group(self, api):
        with patch.object(api._session, "request", return_value=make_mock_response(json_data={"id": "r"})) as m:
            api.get_replay("r", group="shared-group")
            assert sent(m)["params"] == {"group": "shared-group"}

    def test_upload_title_match_and_group_token(self, api):
        resp = make_mock_response(201, json_data={"id": "r", "location": "https://ballchasing.com/replay/r"})
        with patch.object(api._session, "request", return_value=resp) as m:
            api.upload_replay(io.BytesIO(b"data"), title="Finals, game 3", match={"MatchGUID": "abc"},
                              upload_token="g/token")
            kwargs = sent(m)
            assert kwargs["headers"]["Authorization"] == "g/token"
            assert kwargs["data"] == {"title": "Finals, game 3"}
            assert kwargs["files"]["match"] == (None, '{"MatchGUID": "abc"}', "application/json")

    def test_create_group_dedup(self, api):
        with patch.object(api._session, "request", return_value=make_mock_response(201, json_data={"id": "g"})) as m:
            api.create_group(name="grp", player_identification="by-id", team_identification="by-player-clusters",
                             dedup=False)
            assert sent(m)["json"]["dedup"] is False

    @pytest.mark.parametrize("dedup, expected", [(True, "on"), (False, "off"), (None, None)])
    def test_get_group_dedup(self, api, dedup, expected):
        with patch.object(api._session, "request", return_value=make_mock_response(json_data={"id": "g"})) as m:
            api.get_group("g", dedup=dedup)
            assert sent(m)["params"]["dedup"] == expected

    def test_patch_group_splits_replay_lists_at_api_limits(self, api):
        assign = [f"a{i}" for i in range(320)]
        unassign = [f"u{i}" for i in range(301)]
        with patch.object(api._session, "request", return_value=make_mock_response(204)) as m:
            api.patch_group("g", dedup=True, assign_replays=assign, unassign_replays=unassign)
            payloads = [c[1]["json"] for c in m.call_args_list]
        assert [len(p.get("assign_replays", [])) for p in payloads] == [150, 150, 20]
        assert [len(p.get("unassign_replays", [])) for p in payloads] == [300, 1, 0]
        assert payloads[0]["dedup"] is True and "dedup" not in payloads[1]
        assert sum((p.get("assign_replays", []) for p in payloads), []) == assign


class TestNewEndpoints:
    def test_duplicate_replays_paginates(self, api):
        page1 = make_mock_response(json_data={
            "list": [{"replay_id": "a", "same_game_as": "x"}],
            "next": "https://ballchasing.com/api/groups/g/duplicate-replays?after=a&count=1000"})
        page2 = make_mock_response(json_data={"list": [{"replay_id": "b", "same_game_as": "x"}]})
        with patch.object(api._session, "request", side_effect=[page1, page2]) as m:
            rows = list(api.get_group_duplicate_replays("g"))
        assert [r["replay_id"] for r in rows] == ["a", "b"]
        assert sent(m, 0)["url"].endswith("/groups/g/duplicate-replays")
        assert sent(m, 0)["params"]["count"] == 1000
        assert sent(m, 1)["params"]["after"] == "a"

    def test_get_group_upload_token_none_on_204(self, api):
        with patch.object(api._session, "request", return_value=make_mock_response(204)):
            assert api.get_group_upload_token("g") is None

    def test_create_group_upload_token(self, api):
        token = {"token": "g/abc", "created_at": "2026-11-25T00:00:00Z", "generation": 1}
        with patch.object(api._session, "request", return_value=make_mock_response(201, json_data=token)) as m:
            assert api.create_group_upload_token("g") == token
            assert sent(m)["method"] == "POST"


class TestQuotas:
    def test_daily_download_limit_raises_without_retrying(self, api):
        body = {"error": "Too many requests", "limit": 50, "count": 50, "reset": "2026-11-26T00:00:00Z"}
        resp = make_mock_response(429, json_data=body, headers={"Retry-After": "3600"})
        with patch.object(api._session, "request", return_value=resp) as m, patch("time.sleep") as sleep:
            with pytest.raises(DailyDownloadLimitError) as e:
                api.download_replay("r", Path("unused.replay"))
        assert m.call_count == 1 and sleep.call_count == 0
        assert (e.value.limit, e.value.reset, e.value.retry_after) == (50, "2026-11-26T00:00:00Z", 3600)
        assert isinstance(e.value, HTTPError)

    def test_upload_quota_raises_without_retrying(self, api):
        body = {"error": "You have reached your daily upload quota", "max_uploads": 10, "window": "day"}
        with patch.object(api._session, "request", return_value=make_mock_response(429, json_data=body)) as m:
            with pytest.raises(UploadQuotaError) as e:
                api.upload_replay(io.BytesIO(b"data"))
        assert m.call_count == 1
        assert (e.value.max_uploads, e.value.window) == (10, "day")

    def test_plain_rate_limit_still_retries(self, api):
        rate_limited = make_mock_response(429, json_data={"error": "Too many requests"}, headers={"Retry-After": "1"})
        with patch.object(api._session, "request", side_effect=[rate_limited, make_mock_response(json_data={})]), \
                patch("time.sleep"):
            assert api.get_maps() == {}

    def test_download_group_skips_lost_files(self, api, tmp_path):
        replays = make_mock_response(json_data={"list": [{"id": "lost"}, {"id": "ok"}]})
        gone = make_mock_response(410, json_data={"error": "replay file lost"})
        ok = make_mock_response(content=b"replay-bytes")
        with patch.object(api, "get_groups", return_value=iter([])), \
                patch.object(api._session, "request", side_effect=[replays, gone, ok]):
            api.download_group("g", tmp_path)
        assert sorted(p.name for p in (tmp_path / "g").iterdir()) == ["ok.replay"]

    def test_download_group_still_raises_quota(self, api, tmp_path):
        replays = make_mock_response(json_data={"list": [{"id": "r"}]})
        limit = make_mock_response(429, json_data={"error": "x", "limit": 1, "count": 1, "reset": "t"})
        with patch.object(api, "get_groups", return_value=iter([])), \
                patch.object(api._session, "request", side_effect=[replays, limit]):
            with pytest.raises(QuotaExceededError):
                api.download_group("g", tmp_path)


class TestAccountRestrictions:
    """403s with a ``code``: restrictions put on the account, which must not be retried."""
    CODES = (AccountRestrictedError.ACCOUNT_BANNED, AccountRestrictedError.API_ACCESS_BLOCKED,
             AccountRestrictedError.FILES_SUSPENDED)

    def test_codes_match_spec(self):
        schema = SPEC["components"]["schemas"]["RestrictedError"]
        assert enum_values(properties(schema)["code"]) == set(self.CODES)

    def test_every_endpoint_documents_restrictions(self):
        for path, item in SPEC["paths"].items():
            for method, op in item.items():
                if method in ("get", "post", "put", "patch", "delete"):
                    response = resolve(op["responses"]["403"])
                    schema = json.dumps(response["content"]["application/json"]["schema"])
                    assert "RestrictedError" in schema, f"{method.upper()} {path}"

    @pytest.mark.parametrize("code", CODES)
    def test_restriction_raises_without_retrying(self, api, code):
        body = {"code": code, "error": "Do not retry these requests while this restriction is active."}
        with patch.object(api._session, "request", return_value=make_mock_response(403, json_data=body)) as m, \
                patch("time.sleep") as sleep:
            with pytest.raises(AccountRestrictedError) as e:
                api.get_maps()
        assert m.call_count == 1 and sleep.call_count == 0
        assert e.value.code == code and isinstance(e.value, HTTPError)
        assert code in str(e.value) and body["error"] in str(e.value)

    def test_upload_restriction_raises(self, api):
        body = {"code": "account_banned", "error": "banned"}
        with patch.object(api._session, "request", return_value=make_mock_response(403, json_data=body)):
            with pytest.raises(AccountRestrictedError):
                api.upload_replay(io.BytesIO(b"data"))

    def test_403_without_code_is_plain_http_error(self, api):
        resp = make_mock_response(403, json_data={"error": "this account is deleted"})
        with patch.object(api._session, "request", return_value=resp):
            with pytest.raises(HTTPError) as e:
                api.upload_replay(io.BytesIO(b"data"))
        assert not isinstance(e.value, AccountRestrictedError)

    def test_download_group_skips_suspended_files(self, api, tmp_path, caplog):
        api._ping_result = {"steam_id": "me"}
        listing = [{"id": "theirs1", "uploader": {"steam_id": "other"}}, {"id": "mine1", "uploader": {"steam_id": "me"}},
                   {"id": "theirs2", "uploader": {"steam_id": "other"}}, {"id": "mine2", "uploader": {"steam_id": "me"}}]
        replays = make_mock_response(json_data={"list": listing})
        suspended = make_mock_response(403, json_data={"code": "files_suspended", "error": "x"})
        ok1, ok2 = make_mock_response(content=b"1"), make_mock_response(content=b"2")
        with patch.object(api, "get_groups", return_value=iter([])), \
                patch.object(api._session, "request", side_effect=[replays, suspended, ok1, ok2]) as m:
            api.download_group("g", tmp_path)
        # theirs2 is skipped without a request: it would be refused too
        assert m.call_count == 4
        assert "theirs2" not in str(m.call_args_list)
        assert sorted(p.name for p in (tmp_path / "g").iterdir()) == ["mine1.replay", "mine2.replay"]
        assert "Skipped 2 replays" in caplog.text

    def test_download_group_without_ping_stops_requesting_after_suspension(self, api, tmp_path):
        replays = make_mock_response(json_data={"list": [{"id": "a"}, {"id": "b"}, {"id": "c"}]})
        suspended = make_mock_response(403, json_data={"code": "files_suspended", "error": "x"})
        with patch.object(api, "get_groups", return_value=iter([])), \
                patch.object(api._session, "request", side_effect=[replays, suspended]) as m:
            api.download_group("g", tmp_path)  # Own replays can't be told apart without the ping's steam_id
        assert m.call_count == 2

    def test_unreadable_error_body_is_plain_http_error(self, api):
        from requests.exceptions import ChunkedEncodingError
        resp = make_mock_response(403)
        with patch.object(api._session, "request", return_value=resp) as m, \
                patch.object(type(resp), "json", side_effect=ChunkedEncodingError("dropped")):
            with pytest.raises(HTTPError) as e:
                api.get_maps()
            assert not isinstance(e.value, AccountRestrictedError) and m.call_count == 1
            assert BallchasingApi._raise_for_quota(make_mock_response(429)) is None  # Then a plain rate limit

    @pytest.mark.parametrize("code", ["account_banned", "api_access_blocked"])
    def test_download_group_stops_on_other_restrictions(self, api, tmp_path, code):
        replays = make_mock_response(json_data={"list": [{"id": "r"}, {"id": "s"}]})
        restricted = make_mock_response(403, json_data={"code": code, "error": "x"})
        with patch.object(api, "get_groups", return_value=iter([])), \
                patch.object(api._session, "request", side_effect=[replays, restricted]) as m:
            with pytest.raises(AccountRestrictedError):
                api.download_group("g", tmp_path)
        assert m.call_count == 2


class TestRateLimitTiers:
    @pytest.mark.parametrize("tier", ["legend", "org", "bot"])
    def test_new_tiers_get_gc_limits(self, tier):
        limiter = RateLimiter(patron_type_getter=lambda: tier)
        assert limiter.get_category_sleep_time(RateLimitCategory.CORE) == 1 / 16
        assert limiter.get_category_sleep_time(RateLimitCategory.DOWNLOAD) == 1 / 2

    def test_upload_is_not_paced(self):
        limiter = RateLimiter(patron_type_getter=lambda: "regular")
        assert limiter.get_category_sleep_time(RateLimitCategory.UPLOAD) == 0.0


def test_deep_typed_get_replays_on_typed_api():
    api = BallchasingApi("dummy_key", do_initial_ping=False, typed=True)
    listing = make_mock_response(json_data={"list": [{"id": "r"}]})
    full = make_mock_response(json_data={"id": "r", "title": "t", "play_duration": 300})
    with patch.object(api._session, "request", side_effect=[listing, full]):
        replays = list(api.get_replays(count=1, deep=True))
    assert isinstance(replays[0], DeepReplay) and replays[0].play_duration == 300


class TestGeneratedModels:
    def test_models_py_is_up_to_date(self):
        import importlib.util
        path = Path(__file__).parent.parent / "scripts" / "generate_models.py"
        module_spec = importlib.util.spec_from_file_location("generate_models", path)
        generator = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(generator)
        assert generator.OUTPUT.read_text(encoding="utf-8") == generator.generate(SPEC), \
            "models.py is out of date: run python scripts/generate_models.py"

    def test_hierarchy_kept(self):
        from ballchasing.typed import models
        from ballchasing.typed.shared import BasePlayer, BaseReplay, BaseTeam, BasicGroup, BaseGroup
        replay = DeepReplay(blue={"players": [{"name": "a"}]}, groups=[{"id": "g"}])
        assert isinstance(replay, BaseReplay) and isinstance(ShallowReplay(), BaseReplay)
        assert isinstance(replay.blue, BaseTeam) and isinstance(replay.blue, models.ReplayTeam)
        assert isinstance(replay.blue.players[0], BasePlayer)
        assert isinstance(replay.groups[0], BasicGroup)
        assert isinstance(DeepGroup(), BaseGroup) and isinstance(ShallowGroup(), BasicGroup)
        assert isinstance(models.GroupPlayerStats(), models.GroupPlayer)  # From allOf in the spec
        assert isinstance(models.TeamCore(), models.CoreCounters)

    def test_old_names_still_work(self):
        from ballchasing.typed.deep_replay import TeamCoreStatsDR, PlayerDR
        from ballchasing.typed.deep_group import PlayerWithStatsDG, TeamAverageDemoStatsDG, CreatorDG
        from ballchasing.typed.shallow_replay import TeamSR
        from ballchasing.typed.shared import PlayerID
        from ballchasing.typed import models
        assert TeamCoreStatsDR is models.TeamCore and PlayerDR is models.ReplayPlayer
        assert PlayerWithStatsDG is models.GroupPlayerStats and TeamAverageDemoStatsDG is models.Demo
        assert CreatorDG is models.User and TeamSR is models.ReplaySummaryTeam
        assert repr(PlayerID(platform="steam", id="1")) == "steam:1"

    def test_methods_and_equality(self):
        from ballchasing.typed.shared import Rank
        replay = DeepReplay(id="a", blue={"stats": {"core": {"goals": 2}}})
        assert replay.scoreline() == (2, 0)  # Missing values default to 0, an int
        assert ShallowReplay(blue={"goals": 1}).scoreline() == (1, 0)
        assert Rank.from_id("diamond-2") < Rank.from_id("champion-1")
        assert DeepReplay(blue={"players": [{"name": "x"}]}).blue.players[0].pro is False  # Kept for compatibility


class TestEqualityAsBeforeGeneration:
    """Subclasses compare all their fields (dataclass __eq__), as before; the mixins' __eq__ is for the bases."""

    def test_replays_with_different_ids_differ(self):
        assert DeepReplay(id="a", status="pending") != DeepReplay(id="b", status="pending")
        assert DeepReplay(id="a") not in [DeepReplay(id="b")]
        assert DeepReplay(id="a", title="x") != DeepReplay(id="a", title="y")
        assert ShallowReplay(id="a") != ShallowReplay(id="b")

    def test_players_teams_groups(self):
        from ballchasing.typed.deep_replay import PlayerDR, TeamDR
        from ballchasing.typed.shallow_replay import TeamSR
        assert PlayerDR(name="a") != PlayerDR(name="b")  # Two bots
        assert TeamDR(name="A", color="blue") != TeamDR(name="B", color="orange")
        assert TeamSR(name="A") == TeamSR(name="B")  # TeamSR had BaseTeam's __eq__: same players
        assert DeepGroup(id="g") != ShallowGroup(id="g")
        groups = [DeepReplay(groups=[{"id": "g", "name": n}]).groups[0] for n in "xy"]
        assert groups[0] == groups[1]  # Replay groups were BasicGroup: compared by id

    def test_positional_order_kept(self):
        from ballchasing.typed.shared import Rank, BasePlayer
        assert (Rank(5, 2).tier, Rank(5, 2).division) == (5, 2)
        player = BasePlayer(0.0, 1.0, "n", None, True)
        assert player.pro is True and player.mvp is False

    def test_rank_from_name(self):
        from ballchasing.typed.shared import Rank
        rank = Rank.from_name("Champion II Division 3")
        assert (rank.id, rank.division) == ("champion-2", 3)


class TestLimitsMatchSpec:
    def test_limits(self):
        from ballchasing import api as api_module
        patch_props = SPEC["components"]["schemas"]["GroupPatch"]["properties"]
        assert api_module.MAX_ASSIGN_REPLAYS == patch_props["assign_replays"]["maxItems"]
        assert api_module.MAX_UNASSIGN_REPLAYS == patch_props["unassign_replays"]["maxItems"]
        assert api_module.PAGE_SIZE == resolve(query_param("/replays", "get", "count"))["maximum"]
        assert api_module.PAGE_SIZE == resolve(query_param("/groups", "get", "count"))["maximum"]
        assert api_module.DUPLICATE_REPLAYS_PAGE_SIZE == \
            resolve(query_param("/groups/{id}/duplicate-replays", "get", "count"))["maximum"]


class TestReviewFixes:
    def test_stream_upload_gets_a_replay_file_name(self, api):
        resp = make_mock_response(201, json_data={"id": "r"})
        with patch.object(api._session, "request", return_value=resp) as m:
            api.upload_replay(io.BytesIO(b"data"))
            assert sent(m)["files"]["file"][0] == "upload.replay"

    def test_retried_upload_resends_the_whole_file(self, api):
        bodies = []

        def request(**kwargs):
            bodies.append(kwargs["files"]["file"][1].read())
            return make_mock_response(502) if len(bodies) == 1 else make_mock_response(201, json_data={"id": "r"})

        with patch.object(api._session, "request", side_effect=request), patch("time.sleep"):
            api.upload_replay(io.BytesIO(b"x" * 1000))
        assert [len(b) for b in bodies] == [1000, 1000]

    def test_download_group_on_typed_api(self, tmp_path):
        api = BallchasingApi("dummy_key", do_initial_ping=False, typed=True)
        replays = make_mock_response(json_data={"list": [{"id": "r"}]})
        with patch.object(api, "get_groups", return_value=iter([])), \
                patch.object(api._session, "request", side_effect=[replays, make_mock_response(content=b"x")]):
            api.download_group("g", tmp_path)
        assert (tmp_path / "g" / "r.replay").exists()

    def test_single_replay_id_to_assign(self, api):
        with patch.object(api._session, "request", return_value=make_mock_response(204)) as m:
            api.patch_group("g", assign_replays="replay-id")
            assert sent(m)["json"]["assign_replays"] == ["replay-id"]

    def test_empty_upload_token_is_not_replaced_by_the_api_key(self, api):
        with patch.object(api._session, "request", return_value=make_mock_response(201, json_data={})) as m:
            api.upload_replay(io.BytesIO(b"data"), upload_token="")
            assert sent(m)["headers"]["Authorization"] == ""

    def test_sort_helpers_accept_both_names(self):
        from ballchasing.util.iterators import ensure_sorted
        replays = [{"id": "a", "created": "2020-01-01T00:00:00Z"}, {"id": "b", "created": "2021-01-01T00:00:00Z"}]
        for sort_by in ("upload-date", "created"):
            assert [r["id"] for r in ensure_sorted(iter(replays), sort_by=sort_by)] == ["b", "a"]


def load_generator():
    import importlib.util
    module_spec = importlib.util.spec_from_file_location(
        "generate_models", Path(__file__).parent.parent / "scripts" / "generate_models.py")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


class TestGeneratorOnFutureSpecs:
    """Spec changes that must either generate working code or fail loudly when generating."""

    @staticmethod
    def generate(mutate):
        import copy
        spec = copy.deepcopy(SPEC)
        mutate(spec["components"]["schemas"])
        code = load_generator().generate(spec)
        namespace = {}
        exec(compile(code, "models.py", "exec"), namespace)
        return namespace

    def test_untyped_object_union(self):
        def mutate(schemas):
            schemas["Replay"]["allOf"][1]["properties"]["server"] = {"oneOf": [
                {"$ref": "#/components/schemas/Server"}, {"$ref": "#/components/schemas/User"}]}
        models = self.generate(mutate)
        assert models["DeepReplay"](server={"name": "x"}).server == {"name": "x"}  # Kept as a dict, no crash

    def test_array_field_after_a_field_named_list(self):
        def mutate(schemas):
            schemas["ReplayList"]["properties"]["more"] = {"type": "array", "items": {"type": "string"}}
        models = self.generate(mutate)
        assert models["ReplayList"](list=[]).more == []

    @pytest.mark.parametrize("mutate, message", [
        (lambda s: s["Replay"]["allOf"][1]["properties"].update(teams={"type": "array", "items": {}}),
         "shadow methods"),
        (lambda s: s["Server"]["properties"].update(field={"type": "string"}), "can't be a dataclass field"),
        (lambda s: s["Server"]["properties"].update({"class": {"type": "string"}}), "can't be a dataclass field"),
        (lambda s: s.update(BaseTeam={"type": "object", "properties": {"x": {"type": "string"}}}) or
         s["Server"]["properties"].update(team={"$ref": "#/components/schemas/BaseTeam"}), "name of BASES"),
        (lambda s: s["Server"]["properties"].update(parent={"$ref": "#/components/schemas/Server"}), "Cyclic"),
        (lambda s: s["GroupPlayer"]["properties"].update(stats={"type": "object", "properties": {
            "x": {"type": "integer"}}}), "Two different schemas"),
    ])
    def test_fails_loudly(self, mutate, message):
        with pytest.raises(ValueError, match=message):
            self.generate(mutate)

    def test_backslash_in_description(self):
        models = self.generate(lambda s: s["Server"].update(description=r"Path like C:\Users or \d+"))
        assert "C:\\Users" in models["Server"].__doc__


class TestVerificationFollowUps:
    def test_upload_from_a_pipe(self, api):
        import os
        read_fd, write_fd = os.pipe()
        os.write(write_fd, b"x" * 100)
        os.close(write_fd)
        with os.fdopen(read_fd, "rb") as pipe, \
                patch.object(api._session, "request", return_value=make_mock_response(201, json_data={"id": "r"})) as m:
            api.upload_replay(pipe)
            assert m.call_count == 1

    def test_upload_requests_style_tuple(self, api):
        with patch.object(api._session, "request", return_value=make_mock_response(201, json_data={})) as m:
            api.upload_replay(("mine.replay", io.BytesIO(b"data")))
            assert sent(m)["files"]["file"][0] == "mine.replay"

    def test_assign_replays_from_an_array_like(self, api):
        class ArrayLike(list):
            def __bool__(self):
                raise ValueError("ambiguous truth value")  # Like numpy arrays and pandas Series
        with patch.object(api._session, "request", return_value=make_mock_response(204)) as m:
            api.patch_group("g", assign_replays=ArrayLike(["a", "b"]))
            assert sent(m)["json"]["assign_replays"] == ["a", "b"]

    def test_rank_compared_to_none(self):
        from ballchasing.typed.deep_replay import PlayerDR
        pid = {"platform": "steam", "id": "1"}
        assert PlayerDR(id=pid, rank={"tier": 1}) != PlayerDR(id=pid)

    def test_new_fields_go_after_field_order(self):
        def mutate(schemas):
            schemas["Rank"]["properties"]["new_field"] = {"type": "integer"}
        models = TestGeneratorOnFutureSpecs.generate(mutate)
        assert [f for f in models["Rank"].__dataclass_fields__] == ["tier", "division", "name", "id", "new_field"]
