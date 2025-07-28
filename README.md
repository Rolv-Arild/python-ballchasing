# Python Ballchasing
An easy-to-use and comprehensive Python wrapper for the [ballchasing.com API](https://ballchasing.com/doc/api).

## Installation
You can install the library from PyPI using pip:
```
pip install python-ballchasing
```

## Authentication
Before you can use the library, you need an API authentication key from ballchasing.com.
1. Log in to [ballchasing.com](https://ballchasing.com/).
2. Navigate to the Upload tab.
3. Create an API key and copy it.
   
**Keep your API key secure and do not share it publicly.**

## API
For detailed information, please refer to the docs inside the code. For the most part it follows the API spec closely, but there are some differences.

The API is exposed via the `BallchasingApi` class.

Making the client:
```python
from ballchasing import BallchasingApi
api = BallchasingApi("Your token here")
```
or equivalently
```python
import ballchasing
api = ballchasing.Api("Your token here")
```
By default this will also ping the API to make sure it's working.

---
Some simple examples:
```python
# Get lots of SSL replays

from ballchasing import Rank  # there's also Playlist, Season, Map, and more

replays = api.get_replays(
  min_rank=Rank.SUPERSONIC_LEGEND,
  count=10_000  # The API limits you to 200 replays per request but the library handles this for you
)

for replay in replays:  # (replays is an iterable so you don't need to wait for all the replays to be collected)
  ...  # Do something with the replays
```

```python
# Get a specific replay with more detail than the iterator (including stats!)
replay = api.get_replay("2627e02a-aa46-4e13-b66b-b76a32069a07")
```

```python
# Get groups by the "RLCS Referee" account
groups = api.get_groups(creator="76561199225615730")

for group in groups:
  # Download the group
  api.download_group(
    group_id=group["id"],
    folder="/path/to/destination/"
    recursive=True,  # To download all the replays and retain the group structure with subfolders
  )

  # Get replays from the group
  replays = get_group_replays(
    group_id=group["id"],
    deep=True,  # To get detailed replay info
  )
  for replay in replays:
    api.download_replay(replay_id=replay["id"], folder="/path/to/destination/")  # You could also download like this
```

---
Additionally, there's the option to put responses (replays, groups) into typed objects for better type hinting and validation.
It also attempts to fill in missing variables not returned by ballchasing (e.g. if a team has 0 goals they won't have a "goal" entry in the response)
The classes can also be found under the `typing` folder and used as a reference for what the API returns.

```python
# When creating the API, you can specify a default setting for typing (defaults to False)
api = ballchasing.Api("Your token here", typed=True)

# or you can specify it explicitly
replay = api.get_replay("2627e02a-aa46-4e13-b66b-b76a32069a07", typed=True)
print(replay.blue.players[0].name)  # Example of easy attribute access

group = api.get_group("g2-vs-bds-hwbf2eyolb", typed=True)
print(group.players[0].name)
```
