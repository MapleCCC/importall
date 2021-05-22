"""
`importall` is a Python equivalent to C++'s `<bits/stdc++.h>`.

Two kinds of usage:

1. Import the `importall` module, then all names are imported to the current module.

```python
from importall import *
```

2. Call the `importall()` function, then all names are imported to the current module.

```python
from importall import importall

importall()
```
"""


import importlib
from collections.abc import Iterable

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


def importall(ignore: Iterable[str] = None) -> None:
    """
    Python equivalent to C++'s <bits/stdc++.h>.

    Name collision is likely. One can prevent name collisions by specifying the `ignore`
    parameter.

    The `ignore` parameter accepts an iterable of strings specifying modules that should
    be skipped and not imported.
    """

    ignore = set(ignore) if ignore is not None else set()

    libs = stdlib_list()

    for lib in libs:
        if lib in ignore:
            continue

        module = importlib.import_module(lib)
        attr_names = getattr(module, "__all__", None) or dir(module)

        for attr_name in attr_names:

            if attr_name.startswith("_"):
                continue

            globals()[attr_name] = getattr(module, attr_name)


importall()
