"""
`importall` is a lightweight and robust script to import every available names from standard
libraries to the current module, i.e., a Python equivalent to C++'s `<bits/stdc++.h>`.

Two kinds of usage:

1. [_Import interface_]

    Wild card import the `importall` module, then all names are imported to the current module.

    ```python
    from importall import *

    log2(2)
    # 1.0

    bisect_right([24, 35, 38, 38, 46, 47, 52, 54, 54, 57, 87, 91], 53)
    # 7
    ```

2. [_Function interface_]

    Call the `importall()` function, and pass in `globals()` as argument, then all names are imported to the current module.

    ```python
    from importall import importall

    importall(globals())

    list(combinations("ABCD", 2))
    # [("A", "B"), ("A", "C"), ("A", "D"), ("B", "C"), ("B", "D"), ("C", "D")]

    nlargest(4, [48, 5, 21, 38, 65, 12, 27, 18])
    # [65, 48, 38, 27]
    ```
"""


import builtins
import importlib
import os
from collections.abc import Iterable, Mapping, MutableMapping
from typing import Any, Union

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


SymbolTable = MutableMapping[str, Any]


def wild_card_import_module(module_name: str) -> SymbolTable:
    # Python official doc about "wild card import" mechanism:
    #
    # "If the list of identifiers is replaced by a star ('*'), all public names
    # defined in the module are bound in the local namespace for the scope
    # where the import statement occurs."
    #
    # "The public names defined by a module are determined by checking the
    # module’s namespace for a variable named __all__; if defined, it must be a
    # sequence of strings which are names defined or imported by that module.
    # The names given in __all__ are all considered public and are required to
    # exist. If __all__ is not defined, the set of public names includes all
    # names found in the module’s namespace which do not begin with an
    # underscore character ('_'). __all__ should contain the entire public API.
    # It is intended to avoid accidentally exporting items that are not part of
    # the API (such as library modules which were imported and used within the
    # module)."

    try:
        module = importlib.import_module(module_name)
    except (ImportError, ModuleNotFoundError):
        return {}

    symtab: SymbolTable = {}

    try:
        attrs = getattr(module, "__all__")
    except AttributeError:
        # Fallback to try the best effort
        attrs = (attr for attr in dir(module) if not attr.startswith("_"))

    for attr in attrs:
        try:
            symtab[attr] = getattr(module, attr)
        except AttributeError:
            continue

    return symtab


def importall(
    globals: SymbolTable,
    *,
    protect_builtins: bool = True,
    prioritized: Union[Iterable[str], Mapping[str, int]] = (),
    ignore: Iterable[str] = (),
) -> None:
    """
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

    symtab = get_all_symbols(prioritized=prioritized, ignore=ignore)

    if protect_builtins:
        for name in BUILTINS_NAMES:
            symtab.pop(name, None)

    globals.update(symtab)


def deimportall(globals: SymbolTable) -> None:

    stdlib_symbols: set[int] = set()

    for module_name in IMPORTABLE_MODULES:
        symbol_table = wild_card_import_module(module_name)
        stdlib_symbols.update(map(id, symbol_table.values()))

    for name, symbol in dict(globals).items():
        if id(symbol) in stdlib_symbols:
            del globals[name]


def get_all_symbols(
    *,
    prioritized: Union[Iterable[str], Mapping[str, int]] = (),
    ignore: Iterable[str] = (),
) -> SymbolTable:

    if not isinstance(prioritized, Mapping):
        prioritized = {module: 1 for module in prioritized}

    # Ignore user-specified modules.
    module_names = IMPORTABLE_MODULES - set(ignore)

    # When priority score ties, choose the one whose name has higher lexicographical order.
    module_names = sorted(
        module_names, key=lambda name: (prioritized.get(name, 0), name)
    )

    symtab: SymbolTable = {}
    for module_name in module_names:
        symtab |= wild_card_import_module(module_name)

    return symtab


importall(globals())
