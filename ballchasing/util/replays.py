import logging
from copy import deepcopy

from ballchasing.constants import Playlist, Map

# Timers
KICKOFF_START_TO_TOUCH = 2  # Approximately
SPAWN_TO_KICKOFF_START = 4
GOAL_TO_SPAWN = 3

# Keys
TEAMS = ("blue", "orange")
ID_KEYS = ("id", "rocket_league_id", "match_guid")


def get_scoreline(replay):
    """Returns the scoreline of the replay as a tuple (blue_goals, orange_goals)."""
    goals = [0, 0]
    for i, team in enumerate(TEAMS):
        team_data = replay.get(team, {})
        if "goals" in team_data:
            # Shallow replays
            goals[i] += team_data["goals"]
        elif "stats" in team_data:
            # Deep replays
            goals[i] += team_data["stats"].get("core", {}).get("goals", 0)
    return tuple(goals)


def get_players(replay):
    players = []
    for team in TEAMS:
        team_data = replay.get(team, {})
        if "players" in team_data:
            players.extend(team_data["players"])
    return players


def get_pid(player):
    pid = player.get("id", {})
    return f"{pid.get('platform', '')}:{pid.get('id', '')}" if pid else None


def get_gameplay_duration(replay, count_kickoffs=False):
    duration = replay.get("duration", 0)
    goals = sum(get_scoreline(replay))

    if count_kickoffs:
        kickoff_time = 0  # Don't subtract kickoff time
    else:
        kickoff_time = KICKOFF_START_TO_TOUCH
    duration -= SPAWN_TO_KICKOFF_START + kickoff_time  # Initial kickoff
    duration -= goals * (GOAL_TO_SPAWN + SPAWN_TO_KICKOFF_START + kickoff_time)

    return max(0, duration)  # Ensure non-negative duration


def is_standard_replay(replay, allow_bots=False, allow_splitscreen=False) -> tuple[bool, str]:
    """
    Checks if a replay appears to be a standard competitive replay.
    It checks the following:
    - Playlist is a standard competitive playlist (not extra or other modes)
    - Map is a standard competitive map (not extra or other modes)
    - Scoreline is not a draw
    - Teams are the same size and are 1v1, 2v2 or 3v3
    - All players are present for the entire game and have reasonable stats (if a deep replay is input)
    - Gameplay duration is close to 5 minutes (with some leeway for forfeits and 0 second play attempts)
    """
    playlist_id = replay.get("playlist_id")
    # if playlist_id in bc.Playlist.RANKED:
    #     return True
    if playlist_id in Playlist.EXTRA_MODES + Playlist.OTHER_MODES:
        return False, f"Playlist is not standard: {playlist_id}"

    # Map needs to be standard
    map_id = replay.get("map_code")
    if map_id is None or map_id not in Map.STANDARD_MAPS + (Map.NEOTOKYO_TOON_P,):
        if playlist_id.startswith("ranked"):
            logging.warning("Replay %s has non-standard map %s in ranked playlist %s",
                            replay.get("id", "<unknown>"), map_id, playlist_id)
        return False, f"Map is not standard: {map_id}"
    if map_id in (Map.PARK_SNOWY_P, Map.UTOPIASTADIUM_SNOW_P, Map.EUROSTADIUM_SNOWNIGHT_P):
        if playlist_id not in Playlist.RANKED:
            return False, f"Replay uses snowy map"

    # Draw
    scoreline = get_scoreline(replay)
    if scoreline[0] == scoreline[1]:
        return False, f"Scoreline is a draw: {scoreline[0]}-{scoreline[1]}"

    # Same-size teams
    blue = replay.get("blue", {})
    orange = replay.get("orange", {})
    bp = blue.get("players", [])
    op = orange.get("players", [])
    if len(bp) != len(op):
        return False, f"Teams are not the same size: {len(bp)} vs {len(op)}"
    if len(bp) not in (1, 2, 3):
        return False, f"Replay is not 1v1, 2v2 or 3v3: {len(bp)}v{len(op)}"

    # Nonstandard timer check
    gameplay_duration = get_gameplay_duration(replay)
    if gameplay_duration < 90:  # Forfeits can only happen after 3:30 left (1:30 elapsed)
        return False, f"Gameplay duration is too short: {gameplay_duration}s"
    overtime_seconds = replay.get("overtime_seconds", 0)
    if overtime_seconds:
        regulation_time = gameplay_duration - overtime_seconds
        if not (270 < regulation_time <= 360):
            return False, f"Regulation time is not close to 5 minutes in replay with overtime: {regulation_time}+{overtime_seconds}"
    elif gameplay_duration > 360:
        # We only check above because there may be forfeits, and allow up to a minute for 0 second play attempts
        return False, f"Regulation time is above 5 minutes in replay without overtime: {gameplay_duration}s"

    duration = replay.get("duration", 0)
    for i, player in enumerate(bp + op):
        # Check that they're there for the entire game
        name = player.get("name", "")
        if player["start_time"] > SPAWN_TO_KICKOFF_START:  # Kickoff countdown is 4s
            return False, f"Player {name} did not start at the beginning of the game"
        if player["end_time"] < duration - 10:  # A little bit of leeway for leaving right before game ends
            return False, f"Player {name} did not finish the game"

        if player.get("player_number", 0) != 0:
            return False, f"Player {name} has non-zero player number: {player['player_number']}"

        # Bots get an empty ID dictionary
        pid = player.get("id")
        if not pid and not allow_bots:
            return False, f"Player {name} has no ID"
        # Split screen players get a "player_number" that is not 0
        player_number = (pid or {}).get("player_number", 0)
        if player_number != 0 and not allow_splitscreen:
            return False, f"Player {name} has player number {player_number}, indicating split-screen"

        # Check that the stats are reasonable
        if "stats" in player:
            all_stats = {k: v for stat in player["stats"].values() for k, v in stat.items()}
            # Using absolute bounds for these stats
            stats_bounds = {
                "bpm": (0, 2000),
                "bcpm": (0, 2000),
                "avg_amount": (1, 99),  # 100 boost average would indicate infinite boost match
                "avg_speed": (0, 2300),
            }
            for stat, (lo, hi) in stats_bounds.items():
                if stat not in all_stats:
                    return False, f"Player {name} has no stat: {stat}"
                value = all_stats[stat]
                if not (lo <= value <= hi):
                    return False, f"Player {name} has invalid stat {stat}: {value} (expected between {lo} and {hi})"
            percents = [
                ("percent_defensive_third", "percent_neutral_third", "percent_offensive_third"),
                ("percent_defensive_half", "percent_offensive_half"),
                ("percent_behind_ball", "percent_infront_ball"),
                ("percent_slow_speed", "percent_boost_speed", "percent_supersonic_speed"),
                ("percent_ground", "percent_low_air", "percent_high_air"),
                ("percent_boost_0_25", "percent_boost_25_50", "percent_boost_50_75", "percent_boost_75_100"),
            ]
            for keys in percents:
                total = 0
                for key in keys:
                    val = all_stats.get(key, 0.0)
                    if not (0 <= val <= 100):
                        return False, (f"Player {name} has invalid percent stat {key}: {val} "
                                       f"(expected between 0 and 100)")
                    total += val
                if abs(total - 100) > 1:
                    return False, f"Player {name} has invalid percent stats: {keys} sum to {total:.2f}%"

    if "stats" in blue or "stats" in orange:
        for team in (blue, orange):
            core_stats = deepcopy(team.get("stats", {}).get("core", {}))
            for key in ("shooting_percentage", "goals_against", "shots_against"):
                # These stats are not additive, so we remove them from the core stats
                core_stats.pop(key, None)
            # Sum of player stats should equal team stats
            for player in team.get("players", []):
                player_stats = player.get("stats", {}).get("core", {})
                for stat in core_stats.keys():
                    core_stats[stat] -= player_stats.get(stat, 0)
            for stat, value in core_stats.items():
                if value != 0:
                    return False, f"Player stats do not match team stats for {stat}. Difference is {value}"

    return True, "No issues found"
