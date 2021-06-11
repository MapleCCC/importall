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


import builtins
import functools
import inspect
import os
import sys
import warnings
from collections.abc import Iterable, Mapping, MutableMapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from stdlib_list import stdlib_list

from .deprecated import deprecated_modules, deprecated_names


__all__ = ["importall", "deimportall", "get_all_symbols"]


T = TypeVar("T")


# A decorator to transform a class into a singleton
singleton_class = functools.cache


def nulldecorator(fn: T) -> T:
    """Similar to contextlib.nullcontext, except for decorator"""
    return fn


# The name `profile` will be injected into builtins in runtime by line-profiler.
profile = getattr(builtins, "profile", None) or nulldecorator

if TYPE_CHECKING:
    profile = nulldecorator


BUILTINS_NAMES = set(dir(builtins)) - {
    "__doc__",
    "__loader__",
    "__name__",
    "__package__",
    "__spec__",
}


# We use the lists maintained by the `stdlib-list` library instead of that by the `isort`
# library or that of `sys.stdlib_module_names`, for they don't include sub-packages and
# sub-modules, such as `concurrent.futures`.
#
# One can compare the two lists:
#
# 1. List maintained by the `isort` library:
# https://github.com/PyCQA/isort/blob/main/isort/stdlibs/py39.py
#
# 2. List maintained by the `stdlib-list` library:
# https://github.com/jackmaney/python-stdlib-list/blob/master/stdlib_list/lists/3.9.txt

IMPORTABLE_MODULES = set(stdlib_list())

# Don't import some special standard library modules
#
# The `__main__` module is meta.
# Names from the `__main__` module should not be considered standard library utilities.
#
# No need to import names from `builtins`, since they are always available anyway.
#
# Importing `__phello__.foo` module will cause "Hello world!" to be printed
# on the console, and we don't yet know why.
#
# The `antigravity` and `this` modules are easter eggs.
IMPORTABLE_MODULES -= {"__main__", "__phello__.foo", "antigravity", "builtins", "this"}

# lib2to3 package contains Python 2 code, which is unrunnable under Python 3.
IMPORTABLE_MODULES -= {mod for mod in IMPORTABLE_MODULES if mod.startswith("lib2to3")}

if os.name == "nt":
    # On Windows OS, UNIX-specific modules are ignored.
    IMPORTABLE_MODULES -= {
        "multiprocessing.popen_fork",
        "multiprocessing.popen_forkserver",
        "multiprocessing.popen_spawn_posix",
    }


SymbolTable = MutableMapping[str, Any]


def importall(
    globals: SymbolTable,
    *,
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

    Despite imported, features in the `__future__` module are not enabled, as they are
    not imported in the form of future statements (See the production rule for the
    nonterminal `future_stmt` in https://docs.python.org/3/reference/simple_stmts.html#future-statements).
    """

    symtab = get_all_symbols(
        include_deprecated=include_deprecated, prioritized=prioritized, ignore=ignore
    )

    if protect_builtins:
        for name in BUILTINS_NAMES:
            symtab.pop(name, None)

    globals.update(symtab)


@profile
def get_all_symbols(
    *,
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

    Despite imported, features in the `__future__` module are not enabled, as they are
    not imported in the form of future statements (See the production rule for the
    nonterminal `future_stmt` in https://docs.python.org/3/reference/simple_stmts.html#future-statements).
    """

    if isinstance(prioritized, Mapping):
        priorities = prioritized
    else:
        priorities = {module: 1 for module in prioritized}

    # Ignore user-specified modules.
    module_names = IMPORTABLE_MODULES - set(ignore)

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
            module_name, include_deprecated=include_deprecated
        )

    return symtab


def import_public_names(
    module_name: str, *, include_deprecated: bool = False
) -> SymbolTable:
    """
    Return a symbol table containing all public names defined in the module.

    By default, deprecated names are not included. It is designed so because
    deprecated names hopefully should not be used anymore, their presence only for
    easing the steepness of API changes and providing a progressive cross-version
    migration experience. If you are sure you know what you are doing, override the default
    behavior by setting the `include_deprecated` parameter to `True` (**not recommended**).
    """

    symtab = wildcard_import_module(module_name)

    if not include_deprecated:
        for name in deprecated_names(module=module_name):
            symtab.pop(name, None)

    # Try best effort to filter out only public names

    # There is no easy way to reliably determine all public names exported by a module.
    #
    # Standard libraries export public symbols of various types.
    #
    # Unlike functions and classes, some symbols, whose types being string, integer, etc.,
    # don't have the `__module__` attribute.
    #
    # There is no way we can inspect where they come from, less distinguishing them
    # from public symbols of the module that imports them.
    #
    # The only thing we can do is to try best effort.

    def is_another_stdlib(symbol: Any) -> bool:
        """
        Detect if symbol is possibly another standard library module imported to this
        module, hence should not be considered part of the public names of this module.
        """

        return inspect.ismodule(symbol) and symbol.__name__ in IMPORTABLE_MODULES

    def from_another_stdlib(symbol: Any) -> bool:
        """
        Detect if symbol is possibly a public name from another standard library module,
        imported to this module, hence should not be considered part of the public names
        of this module
        """

        origin = getattr(symbol, "__module__", None)
        return origin in IMPORTABLE_MODULES and origin != module_name

    for name, symbol in dict(symtab).items():
        if is_another_stdlib(symbol) or from_another_stdlib(symbol):
            del symtab[name]

    return symtab


@profile
def wildcard_import_module(module_name: str) -> SymbolTable:

    # The __future__ module is a special case.
    # Wildcard-importing the __future__ library yields SyntaxError.

    if module_name == "__future__":
        import __future__

        return {name: getattr(__future__, name) for name in __future__.__all__}

    symtab: SymbolTable = {}

    try:
        exec(f"from {module_name} import *", {}, symtab)
    except (ImportError, ModuleNotFoundError):
        return {}

    return symtab


def deimportall(globals: SymbolTable, purge_cache: bool = False) -> None:
    """
    De-import all imported names. Recover/restore the globals.

    Set the `purge_cache` parameter to `True` if a cleaner and more thorough revert is preferred.
    Useful when module-level behaviors is desired to re-happen, such as the emission of
    the DeprecationWarning on import.
    """

    for name, symbol in dict(globals).items():
        if from_stdlib(symbol):
            del globals[name]

    if purge_cache:
        for module_name in IMPORTABLE_MODULES:
            clean_up_import_cache(module_name)


@singleton_class
class StdlibChecker:
    """
    Check if a symbol comes from standard libraries. Try best effort.
    """

    # The id() approach could fail if importlib.reload() has been called or sys.modules
    # has been manipulated.
    #
    # The hash() approach could fail if the symbol is unhashable.
    #
    # So it's a try-best-effort thing.

    def __init__(self) -> None:
        self._stdlib_symbols = set()
        self._stdlib_symbol_ids: set[int] = set()

        for module_name in IMPORTABLE_MODULES:
            self._gather_info(module_name)

    def _gather_info(self, module_name: str) -> None:

        # Surpass DeprecationWarning, because we know for sure that we are not intended
        # to use the deprecated names here.
        #
        # `contextlib.suppress` is not used because it won't suppress warnings.

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            symbol_table = import_public_names(module_name, include_deprecated=True)

            for symbol in symbol_table.values():
                try:
                    self._stdlib_symbols.add(symbol)

                except TypeError:
                    self._stdlib_symbol_ids.add(id(symbol))

    def check(self, obj: Any) -> bool:
        try:
            return obj in self._stdlib_symbols
        except TypeError:
            return id(obj) in self._stdlib_symbol_ids


# Convenient function for handy invocation of `StdlibChecker().check()`
def from_stdlib(symbol: Any) -> bool:
    return StdlibChecker().check(symbol)


def clean_up_import_cache(module_name: str) -> None:
    """
    Clean up the cache entries related to the given module, in caches populated by the
    import mechanism.

    Useful when module-level behaviors is desired to re-happen, such as the emission of
    the DeprecationWarning on import.
    """

    # Reference: Import cache mechanism https://docs.python.org/3.9/reference/import.html#the-module-cache

    def clean_cache_of_alias(module_name: str) -> None:

        # Detect alias
        # Reference: source of test.support.CleanImport https://github.com/python/cpython/blob/v3.9.0/Lib/test/support/__init__.py#L1241

        module = sys.modules[module_name]
        if module.__name__ != module_name:
            del sys.modules[module.__name__]

    def clean_cache_of_ascendants(module_name: str) -> None:

        # When a module is imported, its ascendant modules are also implicitly imported.
        # We need to evict their corresponding cache entries as well.
        #
        # Reference: https://docs.python.org/3.9/reference/import.html#searching

        idx = module_name.rfind(".")
        while idx != -1:
            module_name = module_name[:idx]

            # Use pop() instead of del, because it's not out of possibility that
            # sys.modules could have been modified by code out of our control.

            sys.modules.pop(module_name, None)
            idx = module_name.rfind(".")

    if module_name not in sys.modules:
        return

    clean_cache_of_alias(module_name)

    clean_cache_of_ascendants(module_name)

    del sys.modules[module_name]
