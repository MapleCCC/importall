# Importall - A Python Equivalent to C++'s <bits/stdc++.h>

[![License](https://img.shields.io/github/license/MapleCCC/importall?color=00BFFF)](LICENSE)
[![LOC](https://sloc.xyz/github/MapleCCC/importall)](https://sloc.xyz/github/MapleCCC/importall)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

## Table of Content

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->


- [Overview](#overview)
- [Quick Start](#quick-start)
- [Development](#development)
- [Testing](#testing)
- [Advanced Tricks](#advanced-tricks)
- [Miscellaneous](#miscellaneous)
- [Contribution](#contribution)
- [Other Similar Projects](#other-similar-projects)
- [License](#license)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

## Overview

`importall` is a lightweight and robust<!--reliable--> library to import every<!--all--> available names from standard libraries to the current module, i.e., a Python equivalent to C++'s `<bits/stdc++.h>`.

It's definitely not intended for serious software engineering situations. It's useful and convenient for some niche scenarios, such as competitive programming contests, under which situation saving some typing strokes and hence precious time is highly desirable. Also convenient when just prototyping, testing back-of-envelop thoughts, or tinkering with ideas on playground. Save the time and tedious chores spent on typing all the necessary modules, which could be annoying, boring and typo-prone.

## Quick Start

Two kinds of usage:

1. *Wild card import*.

    Wild card import the `importall` module, then all names are imported to the current module.

    ```python
    from importall import *

    log2(2)
    # 1.0

    bisect_right([24, 35, 38, 38, 46, 47, 52, 54, 54, 57, 87, 91], 53)
    # 7
    ```

2. *Invoke function*

    Call the `importall()` function, and pass in `globals()` as argument, then all names are imported to the current module.

    ```python
    from importall import importall

    importall(globals())

    list(combinations("ABCD", 2))
    # [("A", "B"), ("A", "C"), ("A", "D"), ("B", "C"), ("B", "D"), ("C", "D")]

    nlargest(4, [48, 5, 21, 38, 65, 12, 27, 18])
    # [65, 48, 38, 27]
    ```

    Note that `local()` should not be passed to `importall()`, as `locals()` is intended as readonly [per doc](https://docs.python.org/3.9/library/functions.html#locals).

    The `importall()` function also provides several parameters for finer-grained configuration, making it more flexible and customizable than the wild-card-import approach.

    More than likely, names imported from different standard libraries might collides. The name collision is resolved by tuning the `prioritized` and `ignore` parameters.

    Say, a user finds that he wants to use `compress` from the `lzma` module instead of that from the `zlib` module. He could either set higher priority for the `lzma` module through the `prioritized` parameter, or ignore the `zlib` module altogether through the `ignore` parameter.

    ```python
    importall(globals())

    compress.__module__
    # "zlib"

    importall(globals(), prioritized=["lzma"])
    # Alternatives:
    # importall(globals(), prioritized={"lzma": 1, "zlib": -1})
    # importall(globals(), ignore=["zlib"])

    compress.__module__
    # "lzma"
    ```

If one prefers getting all importable names stored as a variable instead of importing them into the current module to avoid cluttering<!--polluting--> `globals()`, there is also a programmatic interface for doing so:

```python
from importall import get_all_symbols

symbol_table = get_all_symbols()

symbol_table["python_implementation"]()
# "CPython"

symbol_table["getrecursionlimit"]()
# 1000

symbol_table["log2"](2)
# 1.0
```

To recover<!--restore--> the `globals()` and de-import all imported names, use the `deimportall()` function:

```python
from importall import deimportall, importall

importall(globals())

log2(2)
# 1.0

deimportall(globals())

log2(2)
# NameError
```

The doc and API of the `importall()` function:

```python
def importall(
    globals: SymbolTable,
    *,
    protect_builtins: bool = True,
    include_deprecated: bool = False,
    prioritized: Union[Iterable[str], Mapping[str, int]] = (),
    ignore: Iterable[str] = (),
) -> None:
    """
    Import every available names from standard libraries to the current module.
    Python equivalent to C++'s <bits/stdc++.h>.

    Name collision is likely. One can resolve name collisions by tuning the `prioritized`
    and/or the `ignore` parameter. Names from the module with higher priority value will
    override names from the module with lower priority value.

    The `globals` parameter accepts a symbol table to operate on. Usually the caller passes
    in `globals()`.

    By default, built-in names are protected from overriding. The protection can be switched
    off by setting the `protect_builtins` parameter to `False`.

    By default, deprecated modules and deprecated names are not imported. It is designed
    so because deprecated modules and names hopefully should not be used anymore,
    their presence only for easing the steepness of API changes and providing a progressive
    cross-version migration experience. If you are sure you know what you are doing, override
    the default behavior by setting the `include_deprecated` parameter to `True` (**not recommended**).

    The `prioritized` parameter accepts either an iterable of strings specifying modules
    whose priorities are set to 1, or a mapping object with string keys and integer values,
    specifying respective priority values for corresponding modules. Valid priority value
    is always integer. All modules default to 0 priority values. It's possible to specify
    negative priority value.

    The `ignore` parameter accepts an iterable of strings specifying modules that should
    be skipped and not imported.
    """

    ...
```

## Development

```bash
$ git clone https://github.com/MapleCCC/importall.git

$ cd importall

# Optionally create a virtual environment for isolation purpose
$ python3 -m virtualenv .venv
$ source .venv/bin/activate

# Install dependenies
$ python3 -m pip install -r requirements.txt
# Install dev dependenies
$ python3 -m pip install -r requirements-dev.txt

# Deploy pre-commit hooks
$ pre-commit install

$ python3 -m pip install -e .
```

## Testing

`importall` project uses [pytest](https://pytest.org/) for unit testing.

```bash
# Install test dependenies
$ python3 -m pip install -r requirements-test.txt
$ python3 -m pytest
```

## Advanced Tricks

To provide names thorough the wild card import, internally the `importall` module will eagerly import every names from standard libraries at the time of module loading and initialization, even when the user only intend to use `importall()`, `get_all_symbols()`, or `deimportall()` functions. However, the overhead of calling `importall()` is not cheap, rendering it undesirable for performance-sensitive applications. If one is certain that he won't use the wild card import, and would like to discard the unnecessary overhead, one could preemptively set the environment variable `IMPORTALL_DISABLE_WILD_CARD_IMPORT` (its presence suffices, its value doesn't matter), so as to disable the functionality.

## Miscellaneous

We use the lists maintained by the [`stdlib-list`](https://github.com/jackmaney/python-stdlib-list) library instead of that by the [`isort`](https://github.com/PyCQA/isort) library or that of [`sys.stdlib_module_names`](https://docs.python.org/3.10/library/sys.html#sys.stdlib_module_names), because the lists maintained by the `isort` library and that of `sys.stdlib_module_names` don't include sub-packages and sub-modules, such as `concurrent.futures`.

One can compare the two lists:

1. [List maintained by the `isort` library](https://github.com/PyCQA/isort/blob/main/isort/stdlibs/py39.py).

2. [List maintained by the `stdlib-list` library](https://github.com/jackmaney/python-stdlib-list/blob/master/stdlib_list/lists/3.9.txt).

## Contribution

Contributions are welcome. Open [pull requests](https://github.com/MapleCCC/importall/pulls) or [issues](https://github.com/MapleCCC/importall/issues).

## Other Similar Projects

- [no-one-left-behind](https://github.com/Zalastax/no-one-left-behind), by [Zalastax](https://github.com/Zalastax).
- ...

## License

[MIT](LICENSE).
