from datetime import datetime
from pathlib import Path

stats_info = open(Path(__file__).parent / "stats_info.tsv")
stats_info = [line.strip().split("\t") for line in stats_info]

replay_cols = [row[0] for row in stats_info if row[2].lower() == "true"]
team_cols = [row[0] for row in stats_info if row[3].lower() == "true"]
player_cols = [row[0] for row in stats_info if row[4].lower() == "true"]


def get_value(replay, path, dtype, *path_args):
    tree = replay
    for branch in path.format(*path_args).split("."):
        if isinstance(tree, dict):
            tree = tree.get(branch, None)
        elif isinstance(tree, list):
            tree = tree[int(branch)]

        if tree is None:
            return "MISSING"
    if isinstance(tree, (dict, list)):
        return "MISSING"
    if dtype == "str":
        return str(tree)
    elif dtype == "int":
        return int(tree)
    elif dtype == "float":
        return float(tree)
    elif dtype == "bool":
        return bool(tree)

    return tree


def parse_replay(replay: dict):
    replay_stats = []
    team_stats = [[], []]
    player_stats = []

    for name, path, is_replay, is_team, is_player, type_, is_player_sum, dtype in stats_info:
        if is_replay.lower() == "true":
            replay_stats.append(get_value(replay, path, dtype))

        if is_team.lower() == "true":
            for n, team in enumerate(("blue", "orange")):
                ts = team_stats[n]
                ts.append(get_value(replay, path, dtype, team))

        if is_player.lower() == "true":
            n = 0
            for team in "blue", "orange":
                for p in range(len(replay[team]["players"])):
                    if n >= len(player_stats):
                        player_stats.append([])
                    ps = player_stats[n]
                    ps.append(get_value(replay, path, dtype, team, p))
                    n += 1

    yield "replay", replay_stats
    yield from (("team", ts) for ts in team_stats)
    yield from (("player", ps) for ps in player_stats)


def rfc3339(dt):
    if dt is None:
        return dt
    elif isinstance(dt, str):
        return dt
    elif isinstance(dt, datetime):
        return dt.isoformat("T") + "Z"
    else:
        raise ValueError("Date must be either string or datetime")
