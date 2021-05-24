# Importall - A Python Equivalent to C++'s <bits/stdc++.h>

[![License](https://img.shields.io/github/license/MapleCCC/importall?color=00BFFF)](LICENSE)
[![LOC](https://sloc.xyz/github/MapleCCC/importall)](https://sloc.xyz/github/MapleCCC/importall)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Overview

`importall` is a lightweight and robust<!--reliable--> library to import every<!--all--> available names from standard libraries to the current module, i.e., a Python equivalent to C++'s `<bits/stdc++.h>`.

It's definitely not intended for serious software engineering situations. It's useful and convenient for some niche scenarios, such as competitive programming contests, under which situation saving some typing strokes and hence precious time is highly desirable. Also convenient when just prototyping, testing back-of-envelop thoughts, or tinkering with ideas on playground. Save the time and tedious chores spent on typing all the necessary modules, which could be annoying, boring and typo-prone.

## Usage

Two kinds of usage:

1. _Import interface_

    Wild card import the `importall` module, then all names are imported to the current module.

    ```python
    from importall import *

    log2(2)
    # 1.0

    bisect_right([24, 35, 38, 38, 46, 47, 52, 54, 54, 57, 87, 91], 53)
    # 7
    ```

2. _Function interface_

    Call the `importall()` function, and pass in `globals()` as argument, then all names are imported to the current module.

    ```python
    from importall import importall

    importall(globals())

    list(combinations("ABCD", 2))
    # [("A", "B"), ("A", "C"), ("A", "D"), ("B", "C"), ("B", "D"), ("C", "D")]

    nlargest(4, [48, 5, 21, 38, 65, 12, 27, 18])
    # [65, 48, 38, 27]
    ```

The doc and API of the `importall()` function:

```python
def importall(
    globals: SymbolTable,
    *,
    protect_builtins: bool = True,
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

Say, a user finds that he wants to use `Iterable` from the `collections.abc` module instead of that from the `typing` module. He could either set higher priority for the `collections.abc` module through the `prioritized` parameter, or ignore the `typing` module altogether through the `ignore` parameter.

```python
importall(globals())

inspect.isabstract(Iterable)
# False

importall(globals(), prioritized=["collections.abc"])
# Alternatives:
# importall(globals(), prioritized={"collections.abc": 1, "typing": -1})
# importall(globals(), ignore=["typing"])

inspect.isabstract(Iterable)
# True
```

If one prefers getting all importable names as a variable instead of importing them into the current module, there is also a programmatic interface for doing so:

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

To recover the `globals()` and de-import all imported names, use the `deimportall()` function:

```python
from importall import deimportall, importall

importall(globals())

log2(2)
# 1.0

deimportall(globals())

log2(2)
# NameError
```

## Advanced Tricks

To provide the wild card import interface, internally the `importall` module will eagerly import every names from standard libraries on module loading and initialization time, even when the user only intend to use `importall()`, `get_all_symbols()`, or `deimportall()` functions. If one is certain that he doesn't need the wild card import functionality, and would like to discard the unnecessary cost, one could preemptively set the environment variable `IMPORTALL_NO_INIT_IMPORT` to true value to disable the functionality.

## Contribution

Contributions are welcome. Open [pull requests](https://github.com/MapleCCC/importall/pulls) or [issues](https://github.com/MapleCCC/importall/issues).

## Miscellaneous

We use the lists maintained by the [`stdlib-list`](https://github.com/jackmaney/python-stdlib-list) library instead of that by the [`isort`](https://github.com/PyCQA/isort) library or that of [`sys.stdlib_module_names`](https://docs.python.org/3.10/library/sys.html#sys.stdlib_module_names), because the lists maintained by the `isort` library and that of `sys.stdlib_module_names` don't include sub-packages and sub-modules, such as `concurrent.futures`.

One can compare the two lists:

1. [List maintained by the `isort` library](https://github.com/PyCQA/isort/blob/main/isort/stdlibs/py39.py).

2. [List maintained by the `stdlib-list` library](https://github.com/jackmaney/python-stdlib-list/blob/master/stdlib_list/lists/3.9.txt).

## Other Similar Projects

- [no-one-left-behind](https://github.com/Zalastax/no-one-left-behind), by [Zalastax](https://github.com/Zalastax).
- ...

## License

[MIT](LICENSE).
