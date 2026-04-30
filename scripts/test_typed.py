import os
import random
from datetime import datetime, timedelta

import ballchasing as bc
from ballchasing.typed.deep_group import DeepGroup
from ballchasing.typed.deep_replay import DeepReplay
from ballchasing.typed.shallow_replay import ShallowReplay

# from ballchasing.typed import Replay, Group

key = os.environ.get("BALLCHASING_API_KEY")

api = bc.Api(key)

playlists = bc.Playlist.ALL

min_date = datetime(2015, 7, 7)
max_date = datetime.now()


def deep_equals(d1, d2) -> tuple[bool, str]:
    """Recursively compare two dicts, returning (True, "") if they match or (False, "reason") if not."""
    if type(d1) != type(d2):
        return False, f"Type mismatch: {type(d1)} vs {type(d2)}"

    if isinstance(d1, dict):
        keys1 = set(d1.keys())
        keys2 = set(d2.keys())
        if keys1 != keys2:
            return False, f"Key mismatch: {keys1.symmetric_difference(keys2)}"
        for k in keys1:
            eq, msg = deep_equals(d1[k], d2[k])
            if not eq:
                return False, f"Key '{k}': {msg}"
        return True, ""

    if isinstance(d1, list):
        if len(d1) != len(d2):
            return False, f"List length mismatch: {len(d1)} vs {len(d2)}"
        for i in range(len(d1)):
            eq, msg = deep_equals(d1[i], d2[i])
            if not eq:
                return False, f"Index {i}: {msg}"
        return True, ""

    # For other types (int, str, etc.), use equality
    if d1 != d2:
        return False, f"Value mismatch: {d1} vs {d2}"
    return True, ""


while True:
    playlist = random.choice(playlists)
    date = datetime.fromtimestamp(random.randint(int(min_date.timestamp()), int(max_date.timestamp())))

    for replay in api.get_replays(replay_after=date,
                                  replay_before=date + timedelta(days=1),
                                  playlist=playlists,
                                  count=10):
        deep_replay = api.get_replay(replay["id"])
        typed_replay = ShallowReplay(**replay)
        reconstructed_replay = typed_replay.to_dict()
        typed_deep_replay = DeepReplay(**deep_replay)
        reconstructed_deep_replay = typed_deep_replay.to_dict()

        de, msg = deep_equals(replay, reconstructed_replay)
        if not de:
            print(f"Shallow replay mismatch: {msg}")
            print("Original:", replay)
            print("Reconstructed:", reconstructed_replay)

        de, msg = deep_equals(deep_replay, reconstructed_deep_replay)
        if not de:
            print(f"Deep replay mismatch: {msg}")
            print("Original:", deep_replay)
            print("Reconstructed:", reconstructed_deep_replay)

        for group in typed_deep_replay.groups:
            deep_group = api.get_group(group.id)
            deep_typed_group = DeepGroup(**deep_group)
            reconstructed_group = deep_typed_group.to_dict()

            de, msg = deep_equals(deep_group, reconstructed_group)
            if not de:
                print(f"Group mismatch: {msg}")
                print("Original:", deep_group)
                print("Reconstructed:", reconstructed_group)
