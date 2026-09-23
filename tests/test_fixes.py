import io
import logging
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from requests import Response
from requests.exceptions import ConnectionError as RequestsConnectionError, HTTPError, Timeout

from ballchasing.api import BallchasingApi, PATRON_RATE_LIMIT_SLEEP_TIMES
from ballchasing.constants import Map
from ballchasing.rate_limit import RateLimiter, RateLimitCategory, resolve_category, rate_limited
from ballchasing.typed.shared import PlayerID, BasePlayer, BaseReplay
from ballchasing.typed.deep_replay import DeepReplay, TeamCoreStatsDR, PlayerCoreStatsDR
from ballchasing.util.replays import is_standard_replay


def make_mock_response(status_code=200, json_data=None, headers=None, content=None):
    resp = Response()
    resp.status_code = status_code
    if content is not None:
        resp._content = content
        resp.raw = io.BytesIO(content)
    elif json_data is not None:
        raw_bytes = bytes(__import__("json").dumps(json_data), "utf-8")
        resp._content = raw_bytes
        resp.raw = io.BytesIO(raw_bytes)
    else:
        resp._content = b"{}"
        resp.raw = io.BytesIO(b"{}")
    if headers:
        resp.headers.update(headers)
    return resp


class TestInitialPingBypass:
    def test_do_initial_ping_false_makes_no_requests(self):
        with patch.object(BallchasingApi, "_request") as mock_request:
            api = BallchasingApi("dummy_key", do_initial_ping=False)
            mock_request.assert_not_called()
            assert api._ping_result is None

    def test_sleep_time_on_rate_limit_defaults_to_regular_when_not_pinged(self):
        with patch.object(BallchasingApi, "_request") as mock_request:
            api = BallchasingApi("dummy_key", do_initial_ping=False)
            assert api.sleep_time_on_rate_limit == PATRON_RATE_LIMIT_SLEEP_TIMES["regular"]
            mock_request.assert_not_called()

    def test_sleep_time_on_rate_limit_explicit(self):
        api = BallchasingApi("dummy_key", sleep_time_on_rate_limit=1.5, do_initial_ping=False)
        assert api.sleep_time_on_rate_limit == 1.5

    def test_sleep_time_updates_after_ping(self):
        api = BallchasingApi("dummy_key", do_initial_ping=False)
        assert api.sleep_time_on_rate_limit == PATRON_RATE_LIMIT_SLEEP_TIMES["regular"]

        # Simulate ping result later
        api._ping_result = {"type": "gold", "name": "TestUser"}
        assert api.sleep_time_on_rate_limit == PATRON_RATE_LIMIT_SLEEP_TIMES["gold"]


class TestHttpRetryAndLogging:
    @pytest.mark.parametrize("status_code", [502, 503, 504])
    def test_retry_transient_gateway_errors(self, status_code):
        api = BallchasingApi("dummy_key", do_initial_ping=False)
        err_resp = make_mock_response(status_code=status_code)
        ok_resp = make_mock_response(status_code=200, json_data={"success": True})

        with patch.object(api._session, "request", side_effect=[err_resp, ok_resp]) as mock_req, \
             patch("time.sleep") as mock_sleep:
            res = api._request("/test", "GET")
            assert res.status_code == 200
            assert mock_req.call_count == 2
            mock_sleep.assert_called_once_with(1)  # 2 ** 0

    def test_retry_timeout(self):
        api = BallchasingApi("dummy_key", do_initial_ping=False)
        ok_resp = make_mock_response(status_code=200, json_data={"success": True})

        with patch.object(api._session, "request", side_effect=[Timeout("timed out"), ok_resp]) as mock_req, \
             patch("time.sleep") as mock_sleep:
            res = api._request("/test", "GET")
            assert res.status_code == 200
            assert mock_req.call_count == 2
            mock_sleep.assert_called_once_with(1)

    def test_retry_exhaustion_raises(self):
        api = BallchasingApi("dummy_key", do_initial_ping=False)
        err_resp = make_mock_response(status_code=502)

        with patch.object(api._session, "request", return_value=err_resp), \
             patch("time.sleep"):
            with pytest.raises(RequestsConnectionError):
                api._request("/test", "GET")

    def test_rate_limit_backoff_retry_after(self):
        api = BallchasingApi("dummy_key", do_initial_ping=False)
        rl_resp = make_mock_response(status_code=429, headers={"Retry-After": "3"})
        ok_resp = make_mock_response(status_code=200, json_data={"ok": True})

        with patch.object(api._session, "request", side_effect=[rl_resp, ok_resp]), \
             patch("time.sleep") as mock_sleep:
            res = api._request("/test", "GET")
            assert res.status_code == 200
            mock_sleep.assert_called_once_with(3.0)

    def test_rate_limit_backoff_default_when_unset(self):
        api = BallchasingApi("dummy_key", sleep_time_on_rate_limit=0, do_initial_ping=False)
        rl_resp = make_mock_response(status_code=429)
        ok_resp = make_mock_response(status_code=200, json_data={"ok": True})

        with patch.object(api._session, "request", side_effect=[rl_resp, ok_resp]), \
             patch("time.sleep") as mock_sleep:
            res = api._request("/test", "GET")
            assert res.status_code == 200
            assert mock_sleep.call_count == 1
            assert mock_sleep.call_args[0][0] >= 1.0

    def test_initial_ping_with_rate_limiter(self):
        # Ensure that do_initial_ping=True does not raise AttributeError: no attribute rate_limiter
        mock_resp = make_mock_response(status_code=200, json_data={"name": "TestUser", "type": "champion"})
        with patch("requests.sessions.Session.request", return_value=mock_resp):
            api = BallchasingApi("dummy_key", do_initial_ping=True, proactive_rate_limit=True)
            assert api.steam_name == "TestUser"
            assert api.patron_type == "champion"
            assert hasattr(api, "rate_limiter")

    def test_rate_limit_retries_indefinitely(self):
        api = BallchasingApi("dummy_key", sleep_time_on_rate_limit=0.125, do_initial_ping=False)
        # Simulate 10 consecutive 429s followed by a 200 OK
        rl_resps = [make_mock_response(status_code=429) for _ in range(10)]
        ok_resp = make_mock_response(status_code=200, json_data={"ok": True})

        with patch.object(api._session, "request", side_effect=rl_resps + [ok_resp]), \
             patch("time.sleep") as mock_sleep:
            res = api._request("/test", "GET")
            assert res.status_code == 200
            assert mock_sleep.call_count == 10

    def test_logging_used_on_retry(self, caplog):
        api = BallchasingApi("dummy_key", do_initial_ping=False, print_on_rate_limit=True)
        rl_resp = make_mock_response(status_code=429)
        ok_resp = make_mock_response(status_code=200, json_data={"ok": True})

        with caplog.at_level(logging.WARNING, logger="ballchasing"), \
             patch.object(api._session, "request", side_effect=[rl_resp, ok_resp]), \
             patch("time.sleep"):
            api._request("/test", "GET")
            assert any("Rate limited" in record.message for record in caplog.records)


class TestDeduplicationBeforeDeepFetch:
    def test_get_replays_deduplicates_before_deep_call(self):
        api = BallchasingApi("dummy_key", do_initial_ping=False)
        replays_batch = [
            {"id": "rep1", "rocket_league_id": "rl1"},
            {"id": "rep1", "rocket_league_id": "rl1"},  # duplicate id
            {"id": "rep2", "rocket_league_id": "rl2"},
        ]

        def fake_iterable(*args, **kwargs):
            yield from replays_batch

        with patch.object(api, "_iterable_from_request", side_effect=fake_iterable), \
             patch.object(api, "get_replay", side_effect=lambda rid: {"id": rid, "deep": True}) as mock_get_replay:
            results = list(api.get_replays(deep=True, deduplicate=True))
            assert len(results) == 2
            assert [r["id"] for r in results] == ["rep1", "rep2"]
            # get_replay should only have been called twice (for rep1 and rep2), NOT 3 times
            assert mock_get_replay.call_count == 2
            mock_get_replay.assert_any_call("rep1")
            mock_get_replay.assert_any_call("rep2")


class TestCountZeroIterable:
    def test_count_zero_makes_no_requests(self):
        api = BallchasingApi("dummy_key", do_initial_ping=False)
        with patch.object(api, "_request") as mock_req:
            replays = list(api.get_replays(count=0))
            assert replays == []
            mock_req.assert_not_called()

            groups = list(api.get_groups(count=0))
            assert groups == []
            mock_req.assert_not_called()

    def test_next_url_missing_after_param_handled_defensively(self):
        api = BallchasingApi("dummy_key", do_initial_ping=False)
        # First page has 'next' without 'after' query param
        page1 = {"list": [{"id": "r1"}], "next": "https://ballchasing.com/api/replays?other=val"}

        with patch.object(api, "_request") as mock_req:
            mock_req.return_value = make_mock_response(200, json_data=page1)
            replays = list(api.get_replays(count=10, disable_prefetch=True))
            assert len(replays) == 1
            assert replays[0]["id"] == "r1"


class TestToDictPreservesFalsyValues:
    def test_preserves_zero_and_false(self):
        pid = PlayerID(platform="steam", id="12345", player_number=0)
        d = pid.to_dict()
        assert d["player_number"] == 0
        assert d["id"] == "12345"
        assert d["platform"] == "steam"

        player = BasePlayer(name="Test", id=pid, pro=False, mvp=False)
        pd = player.to_dict()
        assert pd["pro"] is False
        assert pd["mvp"] is False

        core = PlayerCoreStatsDR(goals=0, assists=0, saves=0, score=0, mvp=False)
        cd = core.to_dict()
        assert cd["goals"] == 0
        assert cd["assists"] == 0
        assert cd["saves"] == 0
        assert cd["score"] == 0
        assert cd["mvp"] is False

        replay = BaseReplay(duration=300, overtime=False, overtime_seconds=0)
        rd = replay.to_dict()
        assert rd["overtime"] is False
        assert rd["overtime_seconds"] == 0
        assert rd["duration"] == 300

    def test_drops_none(self):
        player = BasePlayer(name="Test", rank=None)
        pd = player.to_dict()
        assert "rank" not in pd


class TestNonePlayerIdFixes:
    def test_base_player_is_bot_with_none_id(self):
        player = BasePlayer(name="BotPlayer", id=None)
        assert player.is_bot() is True

    def test_base_player_is_bot_with_empty_id(self):
        player = BasePlayer(name="BotPlayer", id=PlayerID(platform="", id=""))
        assert player.is_bot() is True

    def test_base_player_is_not_bot(self):
        player = BasePlayer(name="Human", id=PlayerID(platform="steam", id="123"))
        assert player.is_bot() is False

    def test_is_standard_replay_with_none_player_id(self):
        # Construct a replay where a player has id: None
        replay = {
            "id": "rep123",
            "playlist_id": "ranked-doubles",
            "map_code": Map.STADIUM_P,
            "duration": 300,
            "blue": {
                "goals": 2,
                "players": [
                    {"name": "P1", "start_time": 0, "end_time": 300, "id": {"platform": "steam", "id": "1", "player_number": 0}},
                    {"name": "Bot1", "start_time": 0, "end_time": 300, "id": None},
                ]
            },
            "orange": {
                "goals": 1,
                "players": [
                    {"name": "P2", "start_time": 0, "end_time": 300, "id": {"platform": "steam", "id": "2", "player_number": 0}},
                    {"name": "P3", "start_time": 0, "end_time": 300, "id": {"platform": "steam", "id": "3", "player_number": 0}},
                ]
            }
        }
        # With allow_bots=True, should not crash with AttributeError and should be valid
        valid, reason = is_standard_replay(replay, allow_bots=True)
        assert valid is True
        assert reason == "No issues found"

        # With allow_bots=False, should return False because Bot1 has no ID, without crashing
        valid_nobots, reason_nobots = is_standard_replay(replay, allow_bots=False)
        assert valid_nobots is False
        assert "Bot1 has no ID" in reason_nobots


class TestApiDocReflections:
    def test_upload_replay_returns_id_on_duplicate_409_when_not_raising(self):
        api = BallchasingApi("dummy_key", do_initial_ping=False)
        resp_409 = make_mock_response(409, json_data={"id": "existing-replay-id", "error": "duplicate replay"})

        with patch.object(api._session, "request", return_value=resp_409):
            result = api.upload_replay(io.BytesIO(b"dummy_replay_data"), raise_on_duplicate=False)
            assert result["id"] == "existing-replay-id"

    def test_upload_replay_raises_on_duplicate_409_when_configured(self):
        api = BallchasingApi("dummy_key", do_initial_ping=False)
        resp_409 = make_mock_response(409, json_data={"id": "existing-replay-id", "error": "duplicate replay"})

        with patch.object(api._session, "request", return_value=resp_409):
            with pytest.raises(HTTPError):
                api.upload_replay(io.BytesIO(b"dummy_replay_data"), raise_on_duplicate=True)

    def test_create_group_omits_parent_when_none(self):
        api = BallchasingApi("dummy_key", do_initial_ping=False)
        ok_resp = make_mock_response(201, json_data={"id": "grp1", "name": "Top Level"})

        with patch.object(api._session, "request", return_value=ok_resp) as mock_req:
            res = api.create_group(name="Top Level", player_identification="by-id", team_identification="by-distinct-players")
            assert res["id"] == "grp1"
            assert mock_req.call_count == 1
            payload = mock_req.call_args[1]["json"]
            assert "parent" not in payload
            assert payload == {
                "name": "Top Level",
                "player_identification": "by-id",
                "team_identification": "by-distinct-players"
            }

    def test_create_group_includes_parent_when_provided(self):
        api = BallchasingApi("dummy_key", do_initial_ping=False)
        ok_resp = make_mock_response(201, json_data={"id": "grp2", "name": "Child Group"})

        with patch.object(api._session, "request", return_value=ok_resp) as mock_req:
            api.create_group(name="Child Group", player_identification="by-id", team_identification="by-distinct-players", parent="parent-grp")
            payload = mock_req.call_args[1]["json"]
            assert payload["parent"] == "parent-grp"

    def test_patch_replay_explicit_kwargs(self):
        api = BallchasingApi("dummy_key", do_initial_ping=False)
        ok_resp = make_mock_response(204)

        with patch.object(api._session, "request", return_value=ok_resp) as mock_req:
            api.patch_replay("rep-123", title="New Title", visibility="private", group="")
            payload = mock_req.call_args[1]["json"]
            assert payload == {"title": "New Title", "visibility": "private", "group": ""}

    def test_patch_group_explicit_kwargs(self):
        api = BallchasingApi("dummy_key", do_initial_ping=False)
        ok_resp = make_mock_response(204)

        with patch.object(api._session, "request", return_value=ok_resp) as mock_req:
            api.patch_group("grp-123", player_identification="by-name", team_identification="by-player-clusters", parent="new-parent", shared=True)
            payload = mock_req.call_args[1]["json"]
            assert payload == {
                "player_identification": "by-name",
                "team_identification": "by-player-clusters",
                "parent": "new-parent",
                "shared": True
            }

    def test_get_groups_url_no_trailing_slash(self):
        api = BallchasingApi("dummy_key", do_initial_ping=False)
        ok_resp = make_mock_response(200, json_data={"list": []})

        with patch.object(api._session, "request", return_value=ok_resp) as mock_req:
            list(api.get_groups(count=10, disable_prefetch=True))
            called_url = mock_req.call_args[1]["url"]
            assert called_url == f"{api.base_url}/groups"

    def test_download_replay_supports_pathlib(self, tmp_path):
        api = BallchasingApi("dummy_key", do_initial_ping=False)
        ok_resp = make_mock_response(200, content=b"PK\x03\x04fake_replay_binary")

        with patch.object(api._session, "request", return_value=ok_resp):
            dest = api.download_replay("rep-123", tmp_path)
            assert dest == tmp_path / "rep-123.replay"
            assert dest.read_bytes() == b"PK\x03\x04fake_replay_binary"


class TestRateLimitingAndTracker:
    def test_initial_state_not_rate_limited(self):
        api = BallchasingApi("dummy_key", do_initial_ping=False)
        assert api.is_rate_limited is False
        assert api.last_rate_limited_at is None
        stats = api.rate_limit_stats
        assert stats["is_rate_limited"] is False
        assert stats["last_rate_limited_at"] is None
        assert stats["category_counts"] == {}

    def test_category_resolution(self):
        assert resolve_category("/replays") == RateLimitCategory.LIST
        assert resolve_category("https://ballchasing.com/api/groups") == RateLimitCategory.LIST
        assert resolve_category("/replays/123/file") == RateLimitCategory.DOWNLOAD
        assert resolve_category("/replays/abc-123") == RateLimitCategory.CORE
        assert resolve_category("/groups/grp-456") == RateLimitCategory.CORE
        assert resolve_category("/v2/upload") == RateLimitCategory.CORE
        assert resolve_category("/maps") == RateLimitCategory.CORE
        assert resolve_category("/") == RateLimitCategory.PING

    def test_record_429_updates_tracker_and_stats(self):
        api = BallchasingApi("dummy_key", do_initial_ping=False)
        rl_resp = make_mock_response(status_code=429, headers={"Retry-After": "5"})
        ok_resp = make_mock_response(status_code=200, json_data={"list": []})

        with patch.object(api._session, "request", side_effect=[rl_resp, ok_resp]), \
             patch("time.sleep"):
            api._request("/replays", "GET")

        assert api.last_rate_limited_at is not None
        assert time.time() - api.last_rate_limited_at < 5.0
        stats = api.rate_limit_stats
        assert stats["category_counts"].get("list") == 1
        assert "list" in stats["last_per_category"]

    def test_category_sleep_times(self):
        limiter = RateLimiter(patron_type_getter=lambda: "regular")
        assert limiter.get_category_sleep_time(RateLimitCategory.LIST) == 3600 / 500  # 7.2s
        assert limiter.get_category_sleep_time(RateLimitCategory.CORE) == 3600 / 1000  # 3.6s
        assert limiter.get_category_sleep_time(RateLimitCategory.DOWNLOAD) == 3600 / 200  # 18.0s

        gold_limiter = RateLimiter(patron_type_getter=lambda: "gold")
        assert gold_limiter.get_category_sleep_time(RateLimitCategory.LIST) == 3600 / 1000  # 3.6s
        assert gold_limiter.get_category_sleep_time(RateLimitCategory.CORE) == 3600 / 2000  # 1.8s
        assert gold_limiter.get_category_sleep_time(RateLimitCategory.DOWNLOAD) == 3600 / 400  # 9.0s

    def test_global_tracker_blocks_concurrent_requests(self):
        # Simulate instance being put into cooldown
        api = BallchasingApi("dummy_key", do_initial_ping=False)
        api.rate_limiter.record_429(RateLimitCategory.CORE, retry_after=5.0)

        assert api.is_rate_limited is True
        # A subsequent call to before_request should sleep for the remaining cooldown
        with patch("time.sleep") as mock_sleep:
            api.rate_limiter.before_request(RateLimitCategory.LIST)
            assert mock_sleep.call_count == 1
            slept = mock_sleep.call_args[0][0]
            assert 0.0 < slept <= 5.0

    def test_proactive_mode_enforces_burst_rate(self):
        api = BallchasingApi("dummy_key", do_initial_ping=False, proactive_rate_limit=True)
        # On proactive mode, 2 calls in immediate succession will sleep for min_interval
        with patch("time.sleep") as mock_sleep:
            api.rate_limiter.before_request(RateLimitCategory.LIST)
            # First call has no elapsed constraint
            assert mock_sleep.call_count == 0
            # Immediate second call should sleep
            api.rate_limiter.before_request(RateLimitCategory.LIST)
            assert mock_sleep.call_count == 1
            slept = mock_sleep.call_args[0][0]
            assert 0.4 <= slept <= 0.6  # 1 / 2.0s = 0.5s interval

    def test_rate_limited_decorator_attaches_to_api_methods(self):
        api = BallchasingApi("dummy_key", do_initial_ping=False)
        assert getattr(api.get_replay, "rate_limit_category", None) == RateLimitCategory.CORE
        assert getattr(api.get_replays, "rate_limit_category", None) == RateLimitCategory.LIST
        assert getattr(api.download_replay, "rate_limit_category", None) == RateLimitCategory.DOWNLOAD
        assert getattr(api.ping, "rate_limit_category", None) == RateLimitCategory.PING
