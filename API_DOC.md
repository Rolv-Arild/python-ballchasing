# ballchasing.com API

This is the [ballchasing.com](https://ballchasing.com?utm_source=gemini) API documentation.

## Table of Contents

* [Overview](#top)

  * [Authentication](#header-authentication)

  * [Rate Limiting](#header-rate-limiting)

* [Ping](#ping)

  * [Ping](#ping-ping)

    * [Ping](#ping-ping-get)

* [Upload](#upload)

  * [Upload](#upload-upload)

    * [Replay Upload API](#upload-upload-post)

* [Replays](#replays)

  * [Replays](#replays-replays)

    * [List/Filter replays](#replays-replays-get)

  * [Replay](#replays-replay)

    * [Get a specific replay](#replays-replay-get)

    * [Delete a replay](#replays-replay-delete)

    * [Patch a replay](#replays-replay-patch)

    * [Download replay file](#replays-replay-get-1)

* [Replay Groups](#replay-groups)

  * [Groups](#replay-groups-groups)

    * [Create a group](#replay-groups-groups-post)

    * [List/Filter groups](#replay-groups-groups-get)

  * [Group](#replay-groups-group)

    * [Get a specific group](#replay-groups-group-get)

    * [Delete a group](#replay-groups-group-delete)

    * [Patch a group](#replay-groups-group-patch)

* [Misc](#misc)

  * [Maps](#misc-maps)

## Authentication 

All API calls **must** be authenticated using an API token [which can be retrieved/generated here](/upload).

To authenticate an API call, you must pass the API token as the value of the `Authorization` header:

```
Authorization: $token

```

For example, using curl:

```
# With shell, you can just pass the correct header with each request
curl "api_endpoint_here" \
  -H "Authorization: $token"

```

## Rate Limiting 

Many of the APIs are rate limited to avoid abuse/buggy clients hogging down all the server resources.

When you hit the rate limit, the server will respond with a `429` status code, in which case your client should cool down for a bit before retrying.

Please refer to each API documentation for the recommended number of requests/second.

## Ping 

### Ping 

#### Ping 

**GET** `/`

Use this API to:

* check if your API key is correct

* check if ballchasing API is reachable

cURL example:

```
curl -v \
    -H Authorization:$token \
    'https://ballchasing.com/api/'

```

**Example URI**
`GET https://ballchasing.com/api/`

**Response 200**
**Response 401**
**Response 500**

## Upload 

### Upload 

#### Replay Upload API 

**POST** `/v2/upload{?visibility}`

Use this API to upload a replay file to [ballchasing.com](http://ballchasing.com?utm_source=gemini).
Upload replay file as a single part named `file` using `multipart/form-data`.
This API returns 201 on success (with the id of the created replay) or 409 in case of a duplicate replay (with the id of the existing replay).

cURL example:

```
curl -v \
    -F file=@intense-game-with-ballchasing-team-mates.replay \
    -H Authorization:$token \
    'https://ballchasing.com/api/v2/upload?visibility=private'

```

Python example (using [requests](https://requests.readthedocs.io/en/master/?utm_source=gemini)):

```
import requests

upload_url = "https://ballchasing.com/api/v2/upload?visibility=public"

def upload(path, token):
    files = {'file': open(path, 'rb')}
    r = requests.post(upload_url, headers={
                      'Authorization': token}, files=files)

    if r.status_code == 201:
        # replay successfully created, return it's id
        return r.json()['id']
    elif r.status_code == 409:  # duplicate replay
        # you have the choice: either raise an error, or return the existing replay id
        return r.json()['id']
    else:
        # raise an error for other status codes (50x, ...)
        r.raise_for_status()

```

**Example URI**
`POST https://ballchasing.com/api/v2/upload?visibility=`

**URI Parameters**

* **`visibility`** `enum<string>` (optional) **Default:** `public`
  to set the visibility of the uploaded replay
  **Choices:** `public`, `unlisted`, `private`

* **`group`** `string` (optional)
  the id of the group where to assign the uploaded replay

**Request**
*Headers*

```
Content-Type: multipart/form-data; boundary=---BOUNDARY

```

*Body*

```
-----BOUNDARY
Content-Disposition: form-data; name="file"; filename="super-game.replay"
Content-Type: binary/octet-stream

<replay file contents>
-----BOUNDARY

```

**Response 201**
**Response 409**
**Response 400**
**Response 500**

## Replays 

### Replays 

#### List/Filter replays 

**GET** `/replays`

This endpoint lets you filter and retrieve replays.

> **Warning**
> This endpoint is rate limited to:
>
> * **GC patrons**: 16 calls/second
>
> * **Champion patrons**: 8 calls/second
>
> * **Diamond patrons**: 4 calls/second, 2000/hour
>
> * **Gold patrons**: 2 calls/second, 1000/hour
>
> * **All others**: 2 calls/second, 500/hour

**Example URI**
`GET https://ballchasing.com/api/replays`

**URI Parameters**

* **`title`** `string` (optional)
  filter replays by title

* **`player-name`** `string` (required)
  filter replays by a player’s name. You can filter replays by multiple player ids, e.g `?player-name=name1&player-name=name2`

* **`player-id`** `string` (required)
  filter replays by a player’s platform id in the `$platform:$id`, e.g. `steam:76561198141161044`, `ps4:gamertag`, … You can filter replays by multiple player ids, e.g `?player-id=steam:1&player-id=steam:2`

* **`playlist`** `enum` (optional)
  filter replays by one or more playlists
  **Choices:** `unranked-duels`, `unranked-doubles`, `unranked-standard`, `unranked-chaos`, `private`, `season`, `offline`, `ranked-duels`, `ranked-doubles`, `ranked-solo-standard`, `ranked-standard`, `snowday`, `rocketlabs`, `hoops`, `rumble`, `tournament`, `dropshot`, `ranked-hoops`, `ranked-rumble`, `ranked-dropshot`, `ranked-snowday`, `dropshot-rumble`, `heatseeker`

* **`season`** `string` (optional)
  filter replays by season. Must be a number between 1 and 14 (for old seasons) or f1, f2, … for the new free to play seasons

* **`match-result`** `enum` (optional)
  filter your replays by result
  **Choices:** `win`, `loss`

* **`min-rank`** `enum` (optional)
  filter your replays based on players minimum rank
  **Choices:** `unranked`, `bronze-1`, `bronze-2`, `bronze-3`, `silver-1`, `silver-2`, `silver-3`, `gold-1`, `gold-2`, `gold-3`, `platinum-1`, `platinum-2`, `platinum-3`, `diamond-1`, `diamond-2`, `diamond-3`, `champion-1`, `champion-2`, `champion-3`, `grand-champion`

* **`max-rank`** `enum` (optional)
  filter your replays based on players maximum rank
  **Choices:** `unranked`, `bronze-1`, `bronze-2`, `bronze-3`, `silver-1`, `silver-2`, `silver-3`, `gold-1`, `gold-2`, `gold-3`, `platinum-1`, `platinum-2`, `platinum-3`, `diamond-1`, `diamond-2`, `diamond-3`, `champion-1`, `champion-2`, `champion-3`, `grand-champion`

* **`pro`** `bool` (optional)
  only include replays containing at least one pro player

* **`uploader`** `SteamID64` (optional)
  only include replays uploaded by the specified user. Accepts either the numerical `76*************44` steam id, or the special value `me`

* **`group`** `id` (optional)
  only include replays belonging to the specified group. This only include replays immediately under the specified group, but not replays in child groups.

* **`map`** `enum` (optional)
  only include replays in the specified map. Check the `GET /maps` API for the list of valid map codes

* **`created-before`** `date` (optional)
  only include replays created (uploaded) before some date. `RFC3339` format, e.g. `2020-01-02T15:00:05+01:00`

* **`created-after`** `date` (optional)
  only include replays created (uploaded) after some date. `RFC3339` format, e.g. `2020-01-02T15:00:05+01:00`

* **`replay-date-after`** `date` (optional)
  only include replays for games that happened after some date. `RFC3339` format, e.g. `2020-01-02T15:00:05+01:00`

* **`replay-date-before`** `date` (optional)
  only include replays for games that happened before some date. `RFC3339` format, e.g. `2020-01-02T15:00:05+01:00`

* **`count`** `numeric` (optional) **Default:** `150`
  returns at most count replays. Between 1 and 200

* **`sort-by`** `enum` (optional) **Default:** `upload-date`
  Sort replays according the selected field
  **Choices:** `replay-date`, `upload-date`

* **`sort-dir`** `enum` (optional) **Default:** `desc`
  Sort direction
  **Choices:** `asc`, `desc`

**Response 200**

### Replay 

#### Get a specific replay 

**GET** `/replays/{id}`

Retrieve a given replay’s details and stats.

> **Warning**
> This endpoint is rate limited to:
>
> * **GC patrons**: 16 calls/second
>
> * **Champion patrons**: 8 calls/second
>
> * **Diamond patrons**: 4 calls/second, 5000/hour
>
> * **Gold patrons**: 2 calls/second, 2000/hour
>
> * **All others**: 2 calls/second, 1000/hour

**Example URI**
`GET https://ballchasing.com/api/replays/56889c3e-c420-45db-92fd-47ce2a3604b0`

**URI Parameters**

* **`id`** `string` (required) **Example:** `56889c3e-c420-45db-92fd-47ce2a3604b0`
  the replay id

**Request: `get a successfully converted replay`**
**Response 200**

**Request: `get a pending replay, e.g. not processed yet`**
**Response 200**

**Request: `get a failed replay, e.g. could not be parsed`**
**Response 200**

#### Delete a replay 

**DELETE** `/replays/{id}`

This endpoint deletes the specified replay.

> **Warning**
> Careful with this one: this operation is permanent and undoable

> **Warning**
> This endpoint is rate limited to:
>
> * **GC patrons**: 16 calls/second
>
> * **Champion patrons**: 8 calls/second
>
> * **Diamond patrons**: 4 calls/second, 5000/hour
>
> * **Gold patrons**: 2 calls/second, 2000/hour
>
> * **All others**: 2 calls/second, 1000/hour

**Example URI**
`DELETE https://ballchasing.com/api/replays/56889c3e-c420-45db-92fd-47ce2a3604b0`

**URI Parameters**

* **`id`** `string` (required) **Example:** `56889c3e-c420-45db-92fd-47ce2a3604b0`
  the replay id

**Response 204**

#### Patch a replay 

**PATCH** `/replays/{id}`

This endpoint can patch one or more fields of the specified replay.

> **Warning**
> Careful with this one: this operation is permanent and undoable

> **Warning**
> This endpoint is rate limited to:
>
> * **GC patrons**: 16 calls/second
>
> * **Champion patrons**: 8 calls/second
>
> * **Diamond patrons**: 4 calls/second, 5000/hour
>
> * **Gold patrons**: 2 calls/second, 2000/hour
>
> * **All others**: 2 calls/second, 1000/hour

**Example URI**
`PATCH https://ballchasing.com/api/replays/56889c3e-c420-45db-92fd-47ce2a3604b0`

**URI Parameters**

* **`id`** `string` (required) **Example:** `56889c3e-c420-45db-92fd-47ce2a3604b0`
  the replay id

**Request: `set replay title`**
*Headers*

```
Content-Type: application/json

```

*Body*

```
{
  "title": "this game was nuts"
}

```

**Request: `set replay visibility`**
*Headers*

```
Content-Type: application/json

```

*Body*

```
{
  "visibility": "private"
}

```

**Request: `set replay group`**
*Headers*

```
Content-Type: application/json

```

*Body*

```
{
  "group": "rlcs-s6-day1-xxd"
}

```

**Request: `unassign replay from group`**
*Headers*

```
Content-Type: application/json

```

*Body*

```
{
  "group": ""
}

```

**Request: `multiple fields`**
*Headers*

```
Content-Type: application/json

```

*Body*

```
{
  "title": "this game was nuts",
  "visibility": "private",
  "group": "rlcs-s6-day1-xxd"
}

```

**Response 204**

#### Download replay file 

**GET** `/replays/{id}/file`

Download a replay file.

> **Warning**
> Serving largish (binary) files like replays is costly (server CPU/io time, object storage access costs, network egress costs), which is why this endpoint has lower rate limits than usual:
>
> * **GC patrons**: 2 calls/second
>
> * **Champion patrons**: 2 calls/second, 2000/hour
>
> * **Diamond patrons**: 2 calls/second, 1000/hour
>
> * **Gold patrons**: 2 calls/second, 400/hour
>
> * **All others**: 1 call/second, 200/hour

**Example URI**
`GET https://ballchasing.com/api/replays/56889c3e-c420-45db-92fd-47ce2a3604b0/file`

**URI Parameters**

* **`id`** `string` (required) **Example:** `56889c3e-c420-45db-92fd-47ce2a3604b0`
  the replay id

**Response 200**

## Replay Groups 

### Groups 

Replay groups allow you to group multiple replays in a tree like structure, to organise them and to get access to multi-game stats.

#### Create a group 

**POST** `/groups`

Use this API to create a new replay group.

> **Warning**
> This endpoint is rate limited to:
>
> * **GC patrons**: 16 calls/second
>
> * **Champion patrons**: 8 calls/second
>
> * **Diamond patrons**: 4 calls/second, 5000/hour
>
> * **Gold patrons**: 2 calls/second, 2000/hour
>
> * **All others**: 2 calls/second, 1000/hour

Sample cURL command to create a replay group:

```
curl -v \
    -X POST
    -H Authorization:$token \
    --data '{"name":"xxx","player_identification":"by-id","team_identification":"by-player-clusters"}'
    'https://ballchasing.com/api/groups'

```

**Payload Fields**

* **`name`** `string` (required)
  The new group name

* **`parent`** `id` (optional)
  If set, the new group will be created as a child of the specified group

* **`player_identification`** `enum` (required)
  How to identify the same player across multiple replays. Some tournaments (e.g. RLCS) make players use a pool of generic Steam accounts, meaning the same player could end up using 2 different accounts in 2 series. That's when the `by-name` comes in handy.
  **Choices:** `by-id`, `by-name`

* **`team_identification`** `enum` (required)
  How to identify the same team across multiple replays. Set to `by-distinct-players` if teams have a fixed roster of players for every single game. In some tournaments/leagues, teams allow player rotations, or a sub can replace another player, in which case use `by-player-clusters`.
  **Choices:** `by-distinct-players`, `by-player-clusters`

**Example URI**
`POST https://ballchasing.com/api/groups`

**Request: `create a new top level group`**
*Headers*

```
Content-Type: application/json

```

*Body*

```
{
  "name": "RLCS S9",
  "player_identification": "by-id",
  "team_identification": "by-distinct-players"
}

```

**Request: `create a new child group`**
*Headers*

```
Content-Type: application/json

```

*Body*

```
{
  "name": "Final day",
  "parent": "rlcs-s9-xdhit",
  "player_identification": "by-id",
  "team_identification": "by-distinct-players"
}

```

**Response 201**

#### List/Filter groups 

**GET** `/groups`

This endpoint lets you filter and retrieve replay groups.

> **Warning**
> This endpoint is rate limited to:
>
> * **GC patrons**: 16 calls/second
>
> * **Champion patrons**: 8 calls/second
>
> * **Diamond patrons**: 4 calls/second, 2000/hour
>
> * **Gold patrons**: 2 calls/second, 1000/hour
>
> * **All others**: 2 calls/second, 500/hour

**Example URI**
`GET https://ballchasing.com/api/groups`

**URI Parameters**

* **`name`** `string` (optional)
  filter groups by name

* **`creator`** `SteamID64` (optional)
  only include groups created by the specified user. Accepts either the numerical 76\*\*\*\*\*\*\*\*\*\*\*\*\*44 steam id, or the special value `me`

* **`group`** `id` (optional)
  only include children of the specified group

* **`created-before`** `date` (optional)
  only include groups created (uploaded) before some date. `RFC3339` format, e.g. `2020-01-02T15:00:05+01:00`

* **`created-after`** `date` (optional)
  only include groups created (uploaded) after some date. `RFC3339` format, e.g. `2020-01-02T15:00:05+01:00`

* **`count`** `numeric` (optional) **Default:** `150`
  returns at most count groups. Between 1 and 200

* **`sort-by`** `enum` (optional) **Default:** `created`
  Sort groups according the selected field
  **Choices:** `created`, `name`

* **`sort-dir`** `enum` (optional) **Default:** `desc`
  Sort direction
  **Choices:** `asc`, `desc`

**Response 200**

### Group 

#### Get a specific group 

**GET** `/groups/{id}`

This endpoint retrieves a specific replay group info and stats given its id.

> **Warning**
> This endpoint is rate limited to:
>
> * **GC patrons**: 16 calls/second
>
> * **Champion patrons**: 8 calls/second
>
> * **Diamond patrons**: 4 calls/second, 5000/hour
>
> * **Gold patrons**: 2 calls/second, 2000/hour
>
> * **All others**: 2 calls/second, 1000/hour

**Example URI**
`GET https://ballchasing.com/api/groups/id`

**URI Parameters**

* **`id`** `string` (required)
  the group id

**Request: `get a group`**
**Response 200**

**Request: `get a group with still unprocessed replays`**
**Response 200**

**Request: `get a group with failed replays`**
**Response 200**

#### Delete a group 

**DELETE** `/groups/{id}`

This endpoint deletes the specified group.

> **Warning**
> Careful with this one: this operation is permanent and undoable

> **Warning**
> This endpoint is rate limited to:
>
> * **GC patrons**: 16 calls/second
>
> * **Champion patrons**: 8 calls/second
>
> * **Diamond patrons**: 4 calls/second, 5000/hour
>
> * **Gold patrons**: 2 calls/second, 2000/hour
>
> * **All others**: 2 calls/second, 1000/hour

**Example URI**
`DELETE https://ballchasing.com/api/groups/id`

**URI Parameters**

* **`id`** `string` (required)
  the group id

**Response 204**

#### Patch a group 

**PATCH** `/groups/{id}`

This endpoint can patch one or more fields of the specified group.

> **Warning**
> Careful with this one: this operation is permanent and undoable

> **Warning**
> This endpoint is rate limited to:
>
> * **GC patrons**: 16 calls/second
>
> * **Champion patrons**: 8 calls/second
>
> * **Diamond patrons**: 4 calls/second, 5000/hour
>
> * **Gold patrons**: 2 calls/second, 2000/hour
>
> * **All others**: 2 calls/second, 1000/hour

**Example URI**
`PATCH https://ballchasing.com/api/groups/id`

**URI Parameters**

* **`id`** `string` (required)
  the group id

**Request: `set group player identification`**
*Headers*

```
Content-Type: application/json

```

*Body*

```
{
  "player_identification": "by-name"
}

```

**Request: `set group team identification`**
*Headers*

```
Content-Type: application/json

```

*Body*

```
{
  "team_identification": "by-player-clusters"
}

```

**Request: `change group parent`**
*Headers*

```
Content-Type: application/json

```

*Body*

```
{
  "parent": "new-parent-group-id"
}

```

**Request: `mark a group as shared`**
*Headers*

```
Content-Type: application/json

```

*Body*

```
{
  "shared": true
}

```

**Request: `multiple fields`**
*Headers*

```
Content-Type: application/json

```

*Body*

```
{
  "player_identification": "by-name",
  "parent": "new-parent-group-id",
  "shared": true
}

```

**Response 204**

## Misc 

### Maps 

#### Maps 

**GET** `/maps`

Use this API to get the list of map codes to map names (map as in stadium).

cURL example:

```
curl -v \
    -H Authorization:$token \
    'https://ballchasing.com/api/maps'

```

**Example URI**
`GET https://ballchasing.com/api/maps`

**Response 200**