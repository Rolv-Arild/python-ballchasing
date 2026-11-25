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
from ballchasing.exceptions import DailyDownloadLimitError, QuotaExceededError, UploadQuotaError
from ballchasing.rate_limit import RateLimiter, RateLimitCategory, CATEGORY_HOURLY_SLEEP_TIMES
from ballchasing.typed import DeepReplay, ShallowReplay, DeepGroup, ShallowGroup
from ballchasing.util.stats import get_stats_info, parse_replay_stats
from tests.test_fixes import make_mock_response

SPEC = json.loads((Path(__file__).parent / "data" / "openapi.json").read_text())


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
        assert "aerial_hits" in get_stats_info()

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
