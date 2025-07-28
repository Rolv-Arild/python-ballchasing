import os
import time

import ballchasing as bc
from ballchasing import ShallowReplay, DeepReplay, ShallowGroup, DeepGroup

if __name__ == '__main__':
    # Basic tests
    token = os.environ.get("BALLCHASING_API_KEY")
    api = bc.Api(token)
    print(api)
    # api.get_replays(season="123")

    replays_response = list(api.get_replays(uploader=api.steam_id, season="f14", count=1000))
    print(f"Successfully fetched {len(replays_response)} replays")
    typed_replays_response = [ShallowReplay(**replay) for replay in replays_response]
    print(f"Succcessfully converted {len(typed_replays_response)} replays to typed objects")
    replay_response = api.get_replay(replays_response[0]["id"])
    print(f"Successfully fetched deep replay {replay_response['id']}")
    typed_replay_response = DeepReplay(**replay_response)
    print(f"Succcessfully converted replay {replay_response['id']} to typed object")

    api.download_replay(replay_response["id"], "./")
    print(f"Successfully downloaded replay {replay_response['id']} to current directory")
    api.delete_replay(replay_response["id"])
    print(f"Successfully deleted replay {replay_response['id']}")
    upload_response = api.upload_replay("./" + replay_response["id"] + ".replay")
    print(f"Successfully uploaded replay {upload_response['id']}")

    groups_response = list(api.get_groups())
    print(f"Successfully fetched {len(groups_response)} groups")
    typed_groups_response = [ShallowGroup(**group) for group in groups_response]
    print(f"Succcessfully converted {len(typed_groups_response)} groups to typed objects")
    group_response = api.get_group(groups_response[0]["id"])
    print(f"Successfully fetched group {group_response['id']}")
    typed_group_response = DeepGroup(**group_response)
    print(f"Succcessfully converted deep group {group_response['id']} to typed object")

    create_group_response = api.create_group(name=f"test-{time.time()}",
                                             player_identification=bc.PlayerIdentification.BY_ID,
                                             team_identification=bc.TeamIdentification.BY_DISTINCT_PLAYERS)
    print(f"Successfully created group {create_group_response['id']}")
    api.patch_group(create_group_response["id"],
                    team_identification=bc.TeamIdentification.BY_PLAYER_CLUSTERS)
    print(f"Successfully patched group {create_group_response['id']}")

    api.patch_replay(upload_response["id"], group=create_group_response["id"])
    print(f"Successfully patched replay {upload_response['id']} with group {create_group_response['id']}")

    api.delete_group(create_group_response["id"])
    print(f"Successfully deleted group {create_group_response['id']}")
    print("Nice")
