# Importall - A Python Equivalent to C++'s <bits/stdc++.h>

## Overview

`importall` is a Python equivalent to C++'s `<bits/stdc++.h>`. Basically, it tries to import every available names from standard libraries to the current module.

It's definitely not intended for serious software engineering situations. It's useful and convenient for some niche scenarios, such as competitive programming contests, under which situation saving some typing strokes and hence precious time is highly desirable. Also convenient when just prototyping, testing back-of-envelop thoughts, or tinkering with ideas on playground. Save the time and tedious chores spent on typing all the necessary modules, which could be annoying, boring and typo-prone.

## Usage

Two kinds of usage:

1. Wild card import the `importall` module, then all names are imported to the current module.

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
def importall(
    globals: MutableMapping[str, Any],
    *,
    protect_builtins: bool = True,
    prioritized: Union[Iterable[str], Mapping[str, int]] = (),
    ignore: Iterable[str] = (),
) -> None:
    """
    Python equivalent to C++'s <bits/stdc++.h>.

    Name collision is likely. One can prevent name collisions by tuning the `prioritized`
    and/or the `ignore` parameter.

    The `globals` parameter accepts a symbol table to operate on. Usually the caller passes
    in `globals()`.

    By default, built-in names are protected from overriding. The protection can be switched
    off by setting `protect_builtins` parameter to `False`.

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
importall(prioritized=["collections.abc"])

importall(prioritized={"collections.abc": 1, "typing": -1})

importall(ignore=["typing"])
```

If one prefers getting all importable names as a variable instead of importing them into the current module, there is also a programmatic interface for doing so:

```python
from importall import get_all_symbols

symbol_table = get_all_symbols()

print(symbol_table["python_implementation"]())
# "CPython"

print(symbol_table["getrecursionlimit"]())
# 1000
```

## Miscellaneous

We use the lists maintained by the [`stdlib-list`](https://github.com/jackmaney/python-stdlib-list) library instead of that by the [`isort`](https://github.com/PyCQA/isort) library or that of [`sys.stdlib_module_names`](https://docs.python.org/3.10/library/sys.html#sys.stdlib_module_names), because the lists maintained by the `isort` library and that of `sys.stdlib_module_names` don't include sub-packages and sub-modules, such as `concurrent.futures`.

One can compare the two lists:

1. [List maintained by the `isort` library](https://github.com/PyCQA/isort/blob/main/isort/stdlibs/py39.py).

2. [List maintained by the `stdlib-list` library](https://github.com/jackmaney/python-stdlib-list/blob/master/stdlib_list/lists/3.9.txt).

## Other Similar Projects

- [no-one-left-behind](https://github.com/Zalastax/no-one-left-behind), by [Zalastax](https://github.com/Zalastax).
- ...

## License

[MIT](./LICENSE).
