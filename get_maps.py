import os
from collections import Counter

from tqdm import tqdm

import ballchasing as bc

key = os.environ.get("BALLCHASING_API_KEY")

api = bc.Api(key)

all_maps = api.get_maps()
counts = Counter()


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
    # First, check playlists with only non-standard maps
    for replay in api.get_replays(map_id=code, playlist=non_standard_playlists, count=100):
        if replay["playlist_id"] in non_standard_playlists:
            return False

    # Check both casual and ranked
    for playlists in (bc.Playlist.RANKED, bc.Playlist.UNRANKED):
        # Start with later seasons since it can include more maps, but do them individually in case of changing maps
        # Do only f2p since a few early seasons had non-standard maps
        for seasons in bc.Season.FREE_TO_PLAY[::-1]:
            # Check start and end of season in case of removals
            for sort_dir in (bc.SortDir.ASCENDING, bc.SortDir.DESCENDING):
                for replay in api.get_replays(season=seasons, map_id=code, playlist=playlists, sort_dir=sort_dir,
                                              count=100):
                    if replay["playlist_id"] in bc.Playlist.RANKED:
                        return True
                    elif replay["playlist_id"] in bc.Playlist.UNRANKED:
                        return None
    return False


standard_maps = {}
uncertain_maps = {}
non_standard_maps = {}
for kind in "standard", "non_standard":
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
