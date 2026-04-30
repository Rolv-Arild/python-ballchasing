from datetime import datetime
from typing import Optional

# Start of free-to-play
F2P_START = datetime(2020, 9, 22)


def to_rfc3339(dt: Optional[datetime]):
    """
    Convert a datetime object to an RFC3339 formatted string.
    """
    if dt is None:
        return dt
    elif isinstance(dt, str):
        return dt
    elif isinstance(dt, datetime):
        s = dt.isoformat("T")
        if dt.utcoffset() is None:
            s += "Z"
        return s
    else:
        raise ValueError("Date must be either string or datetime")


def from_rfc3339(s: str):
    """
    Convert an RFC3339 formatted string to a datetime object.
    """
    s = s.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        # Handle cases with sub-second precision and timezone
        dt = datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%f%z")
    return dt
