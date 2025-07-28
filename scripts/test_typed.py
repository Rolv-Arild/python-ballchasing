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

while True:
    playlist = random.choice(playlists)
    date = datetime.fromtimestamp(random.randint(int(min_date.timestamp()), int(max_date.timestamp())))

    for replay in api.get_replays(replay_after=date,
                                  replay_before=date + timedelta(days=1),
                                  playlist=playlists,
                                  count=10):
        deep_replay = api.get_replay(replay["id"])
        typed_replay = ShallowReplay(**replay)
        typed_deep_replay = DeepReplay(**deep_replay)

        for group in typed_deep_replay.groups:
            deep_group = api.get_group(group.id)
            deep_typed_group = DeepGroup(**deep_group)
