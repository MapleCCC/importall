# Importall - A Python Equivalent to C++'s <bits/stdc++.h>

## Overview

`importall` is a Python equivalent to C++'s `<bits/stdc++.h>`. Basically, it tries to import every available names from standard libraries to the current module. Useful for some niche scenarios, such as competitive programming.

## Usage

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

The doc and API of the `importall()` function:

```python
def importall(globals: MutableMapping[str, Any], ignore: Iterable[str] = None) -> None:
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

    ...
```

## Miscellaneous

We use the lists maintained by the [`stdlib-list`](https://github.com/jackmaney/python-stdlib-list) library instead of that by the [`isort`](https://github.com/PyCQA/isort) library or that of [`sys.stdlib_module_names`](https://docs.python.org/3.10/library/sys.html#sys.stdlib_module_names), because the lists maintained by the `isort` library and that of `sys.stdlib_module_names` don't contain sub-packages and sub-modules, such as `concurrent.futures`.

One can compare the two lists:

1. [List maintained by the `isort` library](https://github.com/PyCQA/isort/blob/main/isort/stdlibs/py39.py).

2. [List maintained by the `stdlib-list` library](https://github.com/jackmaney/python-stdlib-list/blob/master/stdlib_list/lists/3.9.txt).

## Other Similar Projects

- [no-one-left-behind](https://github.com/Zalastax/no-one-left-behind), [Zalastax](https://github.com/Zalastax).
- ...

## License

[MIT](./LICENSE).
