#!/usr/bin/env python
# MIT License
#
# Copyright (c) 2020 Rolv-Arild Braaten
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""A library that provides a Python interface to the Ballchasing API."""
import sys

# In Python 3.8+, importlib.metadata is in the standard library.
# For older versions, a backport is available as importlib_metadata.
if sys.version_info >= (3, 8):
    from importlib.metadata import version, metadata
else:
    from importlib_metadata import version, metadata

try:
    # This will read the version from the installed package's metadata
    # (which is defined in pyproject.toml)
    __version__ = version("python-ballchasing")

    # You can also get other metadata in a similar way
    pkg_metadata = metadata("python-ballchasing")
    __author__ = pkg_metadata.get("Author-Email")
    __description__ = pkg_metadata.get("Summary")
except Exception:
    # If the package is not installed (e.g., when running in a development
    # environment without an editable install), you can fall back to defaults.
    __version__ = "0.0.0-dev"
    __description__ = 'A Python wrapper around the Ballchasing API'
    __author__ = 'Rolv-Arild Braaten <rolv_arild@hotmail.com>'

# Import the main classes and constants to make them easily accessible to users.
from .api import BallchasingApi

Api = BallchasingApi  # For importing like `import ballchasing; api = ballchasing.Api`

from .constants import (
    Playlist,
    Rank,
    Season,
    MatchResult,
    ReplaySortBy,
    GroupSortBy,
    SortDir,
    Visibility,
    PlayerIdentification,
    TeamIdentification,
    Map
)
