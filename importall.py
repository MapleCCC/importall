"""
`importall` is a lightweight and robust library to import every available names from standard
libraries to the current namespace, i.e., a Python equivalent to C++'s `<bits/stdc++.h>`.

Two major ways of usage:

1. *Wild card import*.

    Wild card import the `importall` module, then all names are imported to the current namespace.

    ```python
    from importall import *

    log2(2)
    # 1.0

    bisect_right([24, 35, 38, 38, 46, 47, 52, 54, 54, 57, 87, 91], 53)
    # 7
    ```

2. *Invoke function*

    Call the `importall()` function, with the `globals()` passed in as argument, then
    all names are imported to the current namespace.

    ```python
    from importall import importall

    importall(globals())

    list(combinations("ABCD", 2))
    # [("A", "B"), ("A", "C"), ("A", "D"), ("B", "C"), ("B", "D"), ("C", "D")]

    nlargest(4, [48, 5, 21, 38, 65, 12, 27, 18])
    # [65, 48, 38, 27]
    ```

    Note that `local()` should not be passed to `importall()`, as `locals()` is
    intended as readonly [per doc](https://docs.python.org/3.9/library/functions.html#locals).

    The `importall()` function also provides several parameters for finer-grained
    configuration, making it more flexible and customizable than the wild-card-import approach.

    More than likely, names imported from different standard libraries might collides.
    The name collision is resolvable by tuning the `prioritized` and `ignore` parameters.

    Say, a user finds that he wants to use `compress` from the `lzma` module instead of
    that from the `zlib` module. He could either set higher priority for the `lzma`
    module through the `prioritized` parameter, or ignore the `zlib` module altogether
    through the `ignore` parameter.

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

If one prefers getting all importable names stored as a variable instead of importing
them into the current namespace, so as to avoid cluttering the `globals()` namespace,
there is also a programmatic interface for doing so:

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
"""


import builtins
import importlib
import inspect
import os
import sys
import warnings
from collections import defaultdict
from collections.abc import Iterable, Mapping, MutableMapping
from typing import Any, NoReturn, TYPE_CHECKING, TypeVar, Union

import regex
from stdlib_list import stdlib_list


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


if sys.version_info < (3, 9):
    raise RuntimeError("importall library is intended to run with Python 3.9 or higher")


T = TypeVar("T")


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


# Below is a list of deprecated modules who emit DeprecationWarning when imported:
#
# binhex 3.9
# parser 3.9
# symbol 3.9
# formatter 3.4
# imp 3.4

# Below is a list of deprecated modules who don't emit DeprecationWarning when imported:
#
# asynchat 3.6
# asyncore 3.6
# tkinter.tix 3.6
# xml.etree.ElementTree 3.3
# optparse 3.2
# email.encoders 3.0

# Below is a list of deprecated names each of which is one of the names inserted into
# the current namespace when its parent module is wild-card-imported.
#
# ast.ExtSlice 3.9
# ast.Index 3.9
# binascii.a2b_hqx 3.9
# binascii.b2a_hqx 3.9
# binascii.rlecode_hqx 3.9
# binascii.rledecode_hqx 3.9
# typing.Tuple/Callable/Type 3.9
# typing.Dict/List/Set/FrozenSet 3.9
# typing.DefaultDict/OrderedDict/ChainMap/Counter/Deque 3.9
# typing.Pattern/Match 3.9
# typing.AbstractSet/ByteString/Collection/Container/ItemsView/KeysView/Mapping/MappingView/MutableMapping/MutableSequence/MutableSet/Sequence/ValuesView 3.9
# typing.Iterable/Iterator/Generator/Reversible 3.9
# typing.Coroutine/AsyncGenerator/AsyncIterable/AsyncIterator/Awaitable 3.9
# typing.ContextManager/AsyncContextManager 3.9
# ast.Bytes 3.8
# ast.Ellipsis 3.8
# ast.NameConstant 3.8
# ast.Num 3.8
# ast.Str 3.8
# asyncio.coroutine 3.8
# gettext.bind_textdomain_codeset 3.8
# gettext.ldngettext 3.8
# grp.getgrgid 3.6
# inspect.formatargspe 3.5
# inspect.getcallargs 3.5
# abc.abstractclassmethod 3.3
# abc.abstractproperty 3.3
# abc.abstractstaticmethod 3.3
# pkgutil.ImpImporter 3.3
# pkgutil.ImpLoader 3.3
# urllib.request.FancyURLopener 3.3
# urllib.request.URLopener 3.3
# zipfile.BadZipfile 3.2
# turtle.settiltangle 3.1
# inspect.getargspec 3.0
# tempfile.mktemp 2.3

# The dict keys are since which versions they are deprecated.
DEPRECATED_MODULES = {
    (3, 9): {"binhex", "parser", "symbol"},
    (3, 6): {"asynchat", "asyncore", "tkinter.tix"},
    (3, 4): {"formatter", "imp"},
    (3, 3): {"xml.etree.ElementTree"},
    (3, 2): {"optparse"},
    (3, 0): {"email.encoders"},
}

# Not all deprecated names are included, that would be too much and too tedious.
# Only those deprecated names each of which is one of the names inserted into the
# current namespace when its parent module is wild-card-imported.
# The dict keys are since which versions they are deprecated.
DEPRECATED_NAMES = {
    (3, 9): {
        "ast.ExtSlice",
        "ast.Index",
        "binascii.a2b_hqx",
        "binascii.b2a_hqx",
        "binascii.rlecode_hqx",
        "binascii.rledecode_hqx",
        "typing.AbstractSet",
        "typing.AsyncContextManager",
        "typing.AsyncGenerator",
        "typing.AsyncIterable",
        "typing.AsyncIterator",
        "typing.Awaitable",
        "typing.ByteString",
        "typing.Callable",
        "typing.ChainMap",
        "typing.Collection",
        "typing.Container",
        "typing.ContextManager",
        "typing.Coroutine",
        "typing.Counter",
        "typing.DefaultDict",
        "typing.Deque",
        "typing.Dict",
        "typing.FrozenSet",
        "typing.Generator",
        "typing.ItemsView",
        "typing.Iterable",
        "typing.Iterator",
        "typing.KeysView",
        "typing.List",
        "typing.Mapping",
        "typing.MappingView",
        "typing.Match",
        "typing.MutableMapping",
        "typing.MutableSequence",
        "typing.MutableSet",
        "typing.OrderedDict",
        "typing.Pattern",
        "typing.Reversible",
        "typing.Sequence",
        "typing.Set",
        "typing.Tuple",
        "typing.Type",
        "typing.ValuesView",
    },
    (3, 8): {
        "ast.Bytes",
        "ast.Ellipsis",
        "ast.NameConstant",
        "ast.Num",
        "ast.Str",
        "asyncio.coroutine",
        "gettext.bind_textdomain_codeset",
        "gettext.ldngettext",
    },
    (3, 6): {"grp.getgrgid"},
    (3, 5): {"inspect.formatargspe", "inspect.getcallargs"},
    (3, 3): {
        "abc.abstractclassmethod",
        "abc.abstractproperty",
        "abc.abstractstaticmethod",
        "pkgutil.ImpImporter",
        "pkgutil.ImpLoader",
        "urllib.request.FancyURLopener",
        "urllib.request.URLopener",
    },
    (3, 2): {"zipfile.BadZipfile"},
    (3, 1): {"turtle.settiltangle"},
    (3, 0): {"inspect.getargspec"},
    (2, 3): {"tempfile.mktemp"},
}

CURR_VER_DEPRECATED_MODULES: set[str] = set()
for version, modules in DEPRECATED_MODULES.items():
    if sys.version_info >= version:
        CURR_VER_DEPRECATED_MODULES |= modules

CURR_VER_DEPRECATED_NAMES: set[str] = set()
for version, names in DEPRECATED_NAMES.items():
    if sys.version_info >= version:
        CURR_VER_DEPRECATED_NAMES |= names

curr_ver_deprecated_names_index = defaultdict(set)
for absolute_name in CURR_VER_DEPRECATED_NAMES:

    # It's difficult to construct a perfect regex to match all valid Python identifiers,
    # because Python 3 extends valid identifier to include non-ASCII characters.
    #
    # Reference:
    # https://docs.python.org/3.9/reference/lexical_analysis.html#identifiers
    # https://www.python.org/dev/peps/pep-3131/
    # https://stackoverflow.com/questions/5474008/regular-expression-to-confirm-whether-a-string-is-a-valid-python-identifier
    # https://stackoverflow.com/questions/49331782/python-3-how-to-check-if-a-string-can-be-a-valid-variable
    #
    # Instead of pursuing a perfect regex, we simply make reasonable assumption
    # that names from standard libraries are ASCII-only.

    pattern = r"(?P<module>.*)\.(?P<name>[_a-zA-Z][_0-9a-zA-Z]*)"
    matchobj = regex.fullmatch(pattern, absolute_name)
    module, name = matchobj.group("module", "name")
    curr_ver_deprecated_names_index[module].add(name)


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
    """

    symtab = get_all_symbols(
        include_deprecated=include_deprecated, prioritized=prioritized, ignore=ignore
    )

    if protect_builtins:
        for name in BUILTINS_NAMES:
            symtab.pop(name, None)

    globals.update(symtab)


def deimportall(globals: SymbolTable, purge_cache: bool = False) -> None:
    """
    De-import all imported names. Recover/restore the globals.

    Set the `purge_cache` parameter to `True` if a cleaner and more thorough revert is preferred.
    Useful when module-level behaviors is desired to re-happen, such as the emission of
    the DeprecationWarning on import.
    """

    stdlib_symbols: set[int] = set()

    # Surpass DeprecationWarning, because we know for sure that we are not intended
    # to use the deprecated names here.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)

        for module_name in IMPORTABLE_MODULES:
            symbol_table = import_public_names(module_name, include_deprecated=True)
            stdlib_symbols.update(map(id, symbol_table.values()))

    for name, symbol in dict(globals).items():
        if id(symbol) in stdlib_symbols:
            del globals[name]

    if purge_cache:
        for module_name in IMPORTABLE_MODULES:
            sys.modules.pop(module_name, None)


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
    """

    if not isinstance(prioritized, Mapping):
        prioritized = {module: 1 for module in prioritized}

    # Ignore user-specified modules.
    module_names = IMPORTABLE_MODULES - set(ignore)

    if not include_deprecated:
        # Ignore deprecated modules
        module_names -= CURR_VER_DEPRECATED_MODULES

    # When priority score ties, choose the one whose name has higher lexicographical order.
    module_names = sorted(
        module_names, key=lambda name: (prioritized.get(name, 0), name)
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

    symtab = wild_card_import_module(module_name, include_deprecated=include_deprecated)

    # Try best effort to filter out only public names

    for name, symbol in dict(symtab).items():

        if inspect.ismodule(symbol):
            # Possibly another standard library module imported to this module
            # Should not be considered part of the public names of this module
            del symtab[name]
            continue

        parent_module_name = getattr(symbol, "__module__", None)
        if (
            parent_module_name != module_name
            and parent_module_name in IMPORTABLE_MODULES
        ):
            # Possibly a public name from another standard library module, imported to this module
            # Should not be considered part of the public names of this module
            del symtab[name]
            continue

    return symtab


@profile
def wild_card_import_module(
    module_name: str, *, include_deprecated: bool = False
) -> SymbolTable:

    try:
        module = importlib.import_module(module_name)
    except (ImportError, ModuleNotFoundError):
        return {}

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
    #
    # Reference: https://docs.python.org/3.9/reference/simple_stmts.html#the-import-statement

    try:
        attrs = module.__all__  # type: ignore
    except AttributeError:
        # Fallback to try the best effort
        attrs = (attr for attr in dir(module) if not attr.startswith("_"))

    if not include_deprecated:
        # Ignore deprecated names in the module
        attrs = set(attrs) - curr_ver_deprecated_names_index[module_name]

    symtab: SymbolTable = {}

    for attr in attrs:
        try:
            symtab[attr] = getattr(module, attr)
        except AttributeError:
            continue

    return symtab


if "IMPORTALL_DISABLE_WILD_CARD_IMPORT" in os.environ:

    class NotIndexable:
        def __init__(self, reason: str) -> None:
            self._reason = reason

        def __getitem__(self, key: Any) -> NoReturn:
            raise RuntimeError(self._reason)

    __all__ = NotIndexable(  # type: ignore
        reason="Wild card importing the importall module is disabled, "
        "due to the presence of the environment variable IMPORTALL_DISABLE_WILD_CARD_IMPORT"
    )

else:
    importall(globals())
