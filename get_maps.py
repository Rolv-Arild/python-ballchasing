import json
import os
import re
from collections import Counter
from itertools import chain

import requests
from tqdm import tqdm

import ballchasing as bc

key = os.environ.get("BALLCHASING_API_KEY")

api = bc.Api(key)

all_maps = api.get_maps()

if "uf_day_p" not in all_maps:
    print("Adding Futura Garden map to the list")
    all_maps["uf_day_p"] = "Futura Garden"
if "stadium_10a_p" not in all_maps:
    print("Adding 10th Anniversary Stadium map to the list")
    all_maps["stadium_10a_p"] = "DFH Stadium (10th Anniversary)"
for map_code, map_name in all_maps.items():
    if "(" in map_name and ")" not in map_name:
        # Fix maps with missing closing parenthesis
        print(f"Adding missing parenthesis for map {map_code}: {map_name}")
        all_maps[map_code] = map_name + ")"

rlbot_map_list = requests.get(
    "https://raw.githubusercontent.com/RLBot/gui/refs/heads/master/frontend/src/arena-names.ts"
).text
standard_maps_rlbot = re.search(r"MAPS_STANDARD\s*=\s*(\{[^}]+\})", rlbot_map_list)
if standard_maps_rlbot:
    standard_maps_rlbot = eval(standard_maps_rlbot.group(1))
    standard_maps_rlbot = {v.lower(): k for k, v in standard_maps_rlbot.items()}
else:
    standard_maps_rlbot = {}

nonstandard_maps_rlbot = re.search(r"MAPS_NON_STANDARD\s*=\s*(\{[^}]+\})", rlbot_map_list)
if nonstandard_maps_rlbot:
    nonstandard_maps_rlbot = eval(nonstandard_maps_rlbot.group(1))
    nonstandard_maps_rlbot = {v.lower(): k for k, v in nonstandard_maps_rlbot.items()}
else:
    nonstandard_maps_rlbot = {}

# Some corrections:
# if "farm_hw_p" in standard_maps_rlbot:
#     standard_maps_rlbot["farm_hw_p"] = nonstandard_maps_rlbot["farm_hw_p"]
#     del nonstandard_maps_rlbot["farm_hw_p"]
standard_maps_rlbot["woods_night_p"] = all_maps["woods_night_p"]
standard_maps_rlbot["farm_upsidedown_p"] = all_maps["farm_upsidedown_p"]

# Update all_maps with any missing maps that are in the RLBot list
for map_code, map_name in chain(standard_maps_rlbot.items(), nonstandard_maps_rlbot.items()):
    if map_code not in all_maps:
        all_maps[map_code] = map_name


# for seasons in bc.Season.ALL[::-1]:
#     # Check start and end of season in case of removals
#     for sort_dir in (bc.SortDir.ASCENDING, bc.SortDir.DESCENDING):
#         for replay in api.get_replays(season=seasons, sort_dir=sort_dir, count=200):
#             map_code = replay.get("map_code")
#             if map_code is None:
#                 print(f"Replay {replay['id']} has no map code!")
#                 continue
#             map_name = replay.get("map_name")  # Likely missing
#             if map_code not in all_maps:
#                 print(f"Map {map_code} ({map_name}) not in the list of maps!")
# print()


def print_maps(maps: dict):
    print(", ".join(f'"{m}"' for m in sorted(maps.keys())))
    print(", ".join(f'{m.upper()}' for m in sorted(maps.keys())))
    print(", ".join(f'"{maps[m]}"' for m in sorted(maps.keys())))
    print()


print_maps(all_maps)

standard_playlists = bc.Playlist.RANKED + bc.Playlist.UNRANKED
non_standard_playlists = [bc.Playlist.RANKED_HOOPS, bc.Playlist.RANKED_DROPSHOT,
                          bc.Playlist.HOOPS, bc.Playlist.DROPSHOT,
                          bc.Playlist.GRIDIRON, bc.Playlist.ROCKETLABS]


def check_map(code):
    map_name = all_maps.get(code, None)
    if map_code in standard_maps_rlbot or map_name in standard_maps_rlbot.values():
        return True
    if map_code in nonstandard_maps_rlbot or map_name in nonstandard_maps_rlbot.values():
        return False
    # return None
    # First, check playlists with only non-standard maps
    for replay in api.get_replays(map_id=code, playlist=non_standard_playlists, count=100):
        if replay["playlist_id"] in non_standard_playlists:
            return False

    # Check both casual and ranked
    for playlists in (bc.Playlist.RANKED + (bc.Playlist.RANKED_SNOWDAY,),
                      bc.Playlist.UNRANKED):
        # Start with later seasons since it can include more maps, but do them individually in case of changing maps
        # Do only f2p since a few early seasons had non-standard maps
        for seasons in bc.Season.FREE_TO_PLAY[::-1]:
            # Check start and end of season in case of removals
            for sort_dir in (bc.SortDir.ASCENDING, bc.SortDir.DESCENDING):
                for replay in api.get_replays(season=seasons, map_id=code, playlist=playlists, sort_dir=sort_dir,
                                              count=200):
                    if replay["playlist_id"] in bc.Playlist.RANKED:
                        return True
                    elif replay["playlist_id"] in bc.Playlist.UNRANKED:
                        return None
    return False


standard_maps = {}
uncertain_maps = {}
non_standard_maps = {}
for map_code, map_name in tqdm(all_maps.items()):
    res = check_map(map_code)
    if res:
        standard_maps[map_code] = map_name
    elif res is None:
        uncertain_maps[map_code] = map_name
    else:
        non_standard_maps[map_code] = map_name

print_maps(standard_maps)
print_maps(uncertain_maps)
print_maps(non_standard_maps)
print_maps({**non_standard_maps, **uncertain_maps})
print("Done!")
