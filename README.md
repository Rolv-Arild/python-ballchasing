# Python Ballchasing
Python wrapper for the ballchasing.com API. 

# Installation
```
pip install python-ballchasing
```

# API
The API is exposed via the `ballchasing.Api` class.

Simple example:
```python
import ballchasing
api = ballchasing.Api("Your token here")

# Get a specific replay
replay = api.get_replay("2627e02a-aa46-4e13-b66b-b76a32069a07")
```
