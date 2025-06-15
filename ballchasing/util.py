from datetime import datetime
from distutils.util import strtobool
from pathlib import Path


def rfc3339(dt):
    if dt is None:
        return dt
    elif isinstance(dt, str):
        return dt
    elif isinstance(dt, datetime):
        return dt.isoformat("T") + "Z"
    else:
        raise ValueError("Date must be either string or datetime")


def _get_stats_info():
    cur_path = Path(__file__).parent
    with open(cur_path / "stats_info.tsv") as stats_info:
        stats_info = [line.strip().split("\t") for line in stats_info]

    header = stats_info[0]
    stats = {}
    for row in stats_info[1:]:
        stat_info = {}
        for k, v in zip(header, row):
            if k.startswith("is_"):
                v = bool(strtobool(v))
            elif k == "dtype":
                v = {
                    "str": str,
                    "int": int,
                    "float": float,
                    "bool": bool,
                    "datetime": datetime,
                }[v]
            stat_info[k] = v
        stats[stat_info["name"]] = stat_info
    return stats


stats_info = _get_stats_info()


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

    if dtype == datetime:
        return rfc3339(tree)

    return dtype(tree)


def parse_replay_stats(replay: dict):
    replay_stats = {}
    team_stats = {}
    player_stats = {}

    for stat in stats_info.values():
        is_replay = stat["is_replay"]
        is_team = stat["is_team"]
        is_player = stat["is_player"]
        name = stat["name"]
        path = stat["path"]
        dtype = stat["dtype"]

        if is_replay:
            v = get_value(replay, path, dtype)
            replay_stats[name] = v

        if is_team:
            for team in ("blue", "orange"):
                ts = team_stats.setdefault(team, {})
                v = get_value(replay, path, dtype, team)
                ts[name] = v

        if is_player:
            for team in "blue", "orange":
                for n, p in enumerate(replay[team]["players"]):
                    pid = p["id"]
                    pid = pid["platform"] + ":" + pid["id"]
                    ps = player_stats.setdefault(pid, {})
                    v = get_value(replay, path, dtype, team, n)
                    ps[name] = v

    return {
        "replay": replay_stats,
        "teams": team_stats,
        "players": player_stats
    }
