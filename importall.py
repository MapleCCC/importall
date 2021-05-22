"""
`importall` is a Python equivalent to C++'s `<bits/stdc++.h>`.

Two kinds of usage:

1. Import the `importall` module, then all names are imported to the current module.

```python
from importall import *
```

2. Call the `importall()` function, and pass in `globals()` as argument, then all names are imported to the current module.

```python
from importall import importall

importall(globals())
```
"""


import builtins
import importlib
import os
from collections.abc import Iterable
from typing import Any, MutableMapping

from stdlib_list import stdlib_list


# We use the lists maintained by the `stdlib-list` library instead of that by the `isort` library or that of `sys.stdlib_module_names`,
# because the lists maintained by the `isort` library and that of `sys.stdlib_module_names` don't contain sub-packages and sub-modules, such as `concurrent.futures`.
#
# One can compare the two lists:
#
# 1. List maintained by the `isort` library:
# https://github.com/PyCQA/isort/blob/main/isort/stdlibs/py39.py
#
# 2. List maintained by the `stdlib-list` library:
# https://github.com/jackmaney/python-stdlib-list/blob/master/stdlib_list/lists/3.9.txt


BUILTINS_NAMES = set(dir(builtins)) - {
    "__doc__",
    "__loader__",
    "__name__",
    "__package__",
    "__spec__",
}

IMPORTABLE_MODULES = set(stdlib_list())

# Some standard library modules are too meta to import.
IMPORTABLE_MODULES -= {"__main__", "__phello__.foo", "antigravity", "builtins", "this"}

# lib2to3 package contains Python 2 code, which is unrunnable under Python 3.
IMPORTABLE_MODULES = {
    mod for mod in IMPORTABLE_MODULES if not mod.startswith("lib2to3")
}

if os.name == "nt":
    # On Windows OS, UNIX-specific modules are ignored.
    IMPORTABLE_MODULES -= {
        "multiprocessing.popen_fork",
        "multiprocessing.popen_forkserver",
        "multiprocessing.popen_spawn_posix",
    }


def importall(
    globals: MutableMapping[str, Any],
    protect_builtins: bool = True,
    ignore: Iterable[str] = None,
) -> None:
    """
    Python equivalent to C++'s <bits/stdc++.h>.

    Name collision is likely. One can prevent name collisions by specifying the `ignore`
    parameter.

    The `globals` parameter accepts a symbol table to operate on. Usually the caller passes
    in `globals()`.

    By default, built-in names are protected from overriding. The protection can be switched
    off by setting `protect_builtins` parameter to `True`.

    The `ignore` parameter accepts an iterable of strings specifying modules that should
    be skipped and not imported.
    """

    ignore = set(ignore) if ignore is not None else set()

    # Ignore user-specified modules.
    module_names = IMPORTABLE_MODULES - ignore

    for module_name in module_names:
        try:
            module = importlib.import_module(module_name)
        except (ImportError, ModuleNotFoundError):
            continue

        try:
            attrs = getattr(module, "__all__")
        except AttributeError:
            # Fallback to try the best effort
            attrs = (attr for attr in dir(module) if not attr.startswith("_"))

        if protect_builtins:
            attrs = set(attrs) - BUILTINS_NAMES

        for attr in attrs:
            try:
                globals[attr] = getattr(module, attr)
            except AttributeError:
                continue


importall(globals())
