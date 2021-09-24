# This file serves as an entry for line profiling.
# Usage: `kernprof --line-by-line --view profile_entry.py > profile_output.txt`

from importall import importall


importall(lazy=False)
