"""
`importall` is a lightweight, performant and robust library to import every available
names from standard libraries to the current namespace, i.e., a Python equivalent to
C++'s `<bits/stdc++.h>`.
"""

import sys

from .importall import deimportall, get_all_symbols, importall


if sys.version_info < (3, 9):
    raise RuntimeError("importall library is intended to run with Python 3.9 or higher")


__all__ = ["importall", "deimportall", "get_all_symbols"]
