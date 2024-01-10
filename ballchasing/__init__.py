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
from __future__ import absolute_import

__author__       = 'Rolv-Arild Braaten'
__email__        = 'rolv_arild@hotmail.com'
__copyright__    = 'Copyright (c) 2020 Rolv-Arild Braaten'
__license__      = 'Apache License 2.0'
__version__      = '0.1.22'
__url__          = 'https://github.com/Rolv-Arild/python-ballchasing'
__download_url__ = 'https://pypi.python.org/pypi/python-ballchasing'
__description__  = 'A Python wrapper around the Ballchasing API'

from .api import Api                        # noqa
from .constants import (                    # noqa
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
