"""
`importall` is a lightweight and robust library to import every available names from
standard libraries to the current namespace, i.e., a Python equivalent to C++'s
`<bits/stdc++.h>`.

Call the `importall()` function, with the `globals()` passed in as argument, then all
names are imported to the current namespace.

```python3
from importall import importall

importall(globals())

list(combinations("ABCD", 2))
# [("A", "B"), ("A", "C"), ("A", "D"), ("B", "C"), ("B", "D"), ("C", "D")]

nlargest(4, [48, 5, 21, 38, 65, 12, 27, 18])
# [65, 48, 38, 27]
```

Note that `local()` should not be passed to `importall()`, as `locals()` is intended as
readonly [per doc](https://docs.python.org/3.9/library/functions.html#locals).

The `importall()` function also provides several parameters for finer-grained
configuration, enabling more flexible and customizable options.

More than likely, names imported from different standard libraries might collides.
The name collision is resolvable by tuning the `prioritized` and `ignore` parameters.

Say, a user finds that he wants to use `compress` from the `lzma` module instead of that
from the `zlib` module. He could either set higher priority for the `lzma` module
through the `prioritized` parameter, or ignore the `zlib` module altogether through the
`ignore` parameter.

```python3
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

If one prefers getting all importable names stored as a variable instead of importing
them into the current namespace, so as to avoid cluttering the `globals()` namespace,
there is also a programmatic interface for doing so:

```python3
from importall import get_all_symbols

symbol_table = get_all_symbols()

symbol_table["python_implementation"]()
# "CPython"

symbol_table["getrecursionlimit"]()
# 1000

symbol_table["log2"](2)
# 1.0
```

To recover the `globals()` and de-import all imported names, use the `deimportall()`
function:

```python3
from importall import deimportall, importall

importall(globals())

log2(2)
# 1.0

deimportall(globals())

log2(2)
# NameError
```
"""


from collections.abc import Iterable, Mapping
from typing import Union

from .importlib import clean_up_import_cache, from_stdlib, import_public_names
from .stdlib_list import BUILTINS_NAMES, IMPORTABLE_STDLIB_MODULES
from .typing import SymbolTable
from .utils import (
    deprecated_modules,
    getcallerframe,
    is_called_at_module_level,
    profile,
)


__all__ = ["importall", "deimportall", "get_all_symbols"]


def importall(
    globals: SymbolTable = None,
    *,
    lazy: bool = True,
    protect_builtins: bool = True,
    include_deprecated: bool = False,
    prioritized: Union[Iterable[str], Mapping[str, int]] = (),
    ignore: Iterable[str] = (),
) -> None:
    """
    Import every available names from standard libraries to the current namespace.
    Python equivalent to C++'s <bits/stdc++.h>.

    Name collision is likely. One can resolve name collisions by tuning the `prioritized`
    and/or the `ignore` parameter. Names from the module with higher priority value will
    override names from the module with lower priority value.

    The `importall()` function is only allowed to be called at the module level.
    Attempting to invoke `importall()` in class or function definitions will raise a
    RuntimeError.

    The `globals` parameter accepts a symbol table to populate. Usually the caller passes
    in `globals()`.

    By default, names are lazily imported, to avoid the overhead of eager import.
    Set the `lazy` parameter to `False` to switch to eager import mode.

    By default, built-in names are protected from overriding. The protection can be switched
    off by setting the `protect_builtins` parameter to `False`.

    By default, deprecated modules and deprecated names are not imported. It is designed
    so because deprecated modules and names hopefully should not be used anymore,
    their presence only for easing the steepness of API changes and providing a progressive
    cross-version migration experience. If you are sure you know what you are doing, override
    the default behavior by setting the `include_deprecated` parameter to `True` (**NOT RECOMMENDED!**).

    The `prioritized` parameter accepts either an iterable of strings specifying modules
    whose priorities are set to 1, or a mapping object with string keys and integer values,
    specifying respective priority values for corresponding modules. Valid priority value
    is always integer. All modules default to priority values of 0. It's possible to specify
    negative priority value.

    The `ignore` parameter accepts an iterable of strings specifying modules that should
    be skipped and not imported.

    Despite imported, features in the `__future__` module are not enabled, as they are
    not imported in the form of future statements (See the production rule for the
    nonterminal `future_stmt` in https://docs.python.org/3/reference/simple_stmts.html#future-statements).
    """

    # Check against invocation at non-module level
    if not is_called_at_module_level():
        raise RuntimeError("importall() function is only allowed to be invoked at the module level")

    globals = globals or getcallerframe().f_globals

    symtab = get_all_symbols(
        lazy=lazy,
        include_deprecated=include_deprecated,
        prioritized=prioritized,
        ignore=ignore,
    )

    if protect_builtins:
        for name in BUILTINS_NAMES:
            symtab.pop(name, None)

    globals.update(symtab)


@profile
def get_all_symbols(
    *,
    lazy: bool = True,
    include_deprecated: bool = False,
    prioritized: Union[Iterable[str], Mapping[str, int]] = (),
    ignore: Iterable[str] = (),
) -> SymbolTable:
    """
    Return a symbol table that gathers all available names from standard libraries.
    Python equivalent to C++'s <bits/stdc++.h>.

    Name collision is likely. One can resolve name collisions by tuning the `prioritized`
    and/or the `ignore` parameter. Names from the module with higher priority value will
    override names from the module with lower priority value.

    By default, names are lazily imported, to avoid the overhead of eager import.
    Set the `lazy` parameter to `False` to switch to eager import mode.

    By default, deprecated modules and deprecated names are not imported. It is designed
    so because deprecated modules and names hopefully should not be used anymore,
    their presence only for easing the steepness of API changes and providing a progressive
    cross-version migration experience. If you are sure you know what you are doing, override
    the default behavior by setting the `include_deprecated` parameter to `True` (**NOT RECOMMENDED!**).

    The `prioritized` parameter accepts either an iterable of strings specifying modules
    whose priorities are set to 1, or a mapping object with string keys and integer values,
    specifying respective priority values for corresponding modules. Valid priority value
    is always integer. All modules default to priority values of 0. It's possible to specify
    negative priority value.

    The `ignore` parameter accepts an iterable of strings specifying modules that should
    be skipped and not imported.

    Despite imported, features in the `__future__` module are not enabled, as they are
    not imported in the form of future statements (See the production rule for the
    nonterminal `future_stmt` in https://docs.python.org/3/reference/simple_stmts.html#future-statements).
    """

    if isinstance(prioritized, Mapping):
        priorities = prioritized
    else:
        priorities = {module: 1 for module in prioritized}

    # Ignore user-specified modules.
    module_names = IMPORTABLE_STDLIB_MODULES - set(ignore)

    if not include_deprecated:
        # Ignore deprecated modules
        module_names -= deprecated_modules()

    # When priority score ties, choose the one whose name has higher lexicographical order.
    module_names = sorted(
        module_names, key=lambda name: (priorities.get(name, 0), name)
    )

    symtab: SymbolTable = {}

    for module_name in module_names:
        symtab |= import_public_names(
            module_name, lazy=lazy, include_deprecated=include_deprecated
        )

    return symtab


def deimportall(globals: SymbolTable = None, *, purge_cache: bool = False) -> None:
    """
    De-import all imported names. Recover/restore the globals.

    Set the `purge_cache` parameter to `True` if a cleaner and more thorough revert is preferred.
    Useful when module-level behaviors is desired to re-happen, such as the emission of
    the `DeprecationWarning` on import.

    The `deimportall()` function is only allowed to be called at the module level.
    Attempting to invoke `deimportall()` in class or function definitions will raise a
    RuntimeError.
    """

    # Check against invocation at non-module level
    if not is_called_at_module_level():
        raise RuntimeError("deimportall() function is only allowed to be invoked at the module level")

    globals = globals or getcallerframe().f_globals

    for name, symbol in dict(globals).items():
        if from_stdlib(symbol):
            del globals[name]

    if purge_cache:
        for module_name in IMPORTABLE_STDLIB_MODULES:
            clean_up_import_cache(module_name)
