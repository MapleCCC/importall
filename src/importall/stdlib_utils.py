"""
A collection of utilities related to standard libraries.
"""

import __future__

import importlib
import inspect
import json
import re
import subprocess
import sys
import warnings
from functools import cache
from pathlib import Path
from typing import Optional, cast

import commentjson
import regex
from lazy_object_proxy import Proxy

from .importlib import import_name_from_module, wildcard_import_module
from .stdlib_list import BUILTINS_NAMES, IMPORTABLE_STDLIB_MODULES, STDLIB_MODULES
from .typing import SymbolTable
from .utils import raises


__all__ = [
    "import_stdlib_public_names",
    "DeducePublicInterfaceError",
    "deduce_stdlib_public_interface",
    "from_stdlib",
    "deprecated_modules",
    "deprecated_names",
    "stdlib_public_names",
]


VersionTuple = tuple[int, int]


def import_stdlib_public_names(
    module_name: str, *, lazy: bool = False, include_deprecated: bool = False
) -> SymbolTable:
    """
    Return a symbol table containing all public names defined in the standard library
    module.

    By default, names are eagerly imported. One can reduce the overhead by setting the
    `lazy` parameter to `True` to enable lazy import mode.

    By default, deprecated names are not included. It is designed so because
    deprecated names hopefully should not be used anymore, their presence only for
    easing the steepness of API changes and providing a progressive cross-version
    migration experience. If you are sure you know what you are doing, override the default
    behavior by setting the `include_deprecated` parameter to `True` (**NOT RECOMMENDED!**).
    """

    if module_name not in IMPORTABLE_STDLIB_MODULES:
        raise ValueError(f"{module_name} is not importable stdlib module")

    public_names = stdlib_public_names(module_name)

    if not include_deprecated:
        public_names -= deprecated_names(module_name)

    # TODO check to see if the laziness persists until actual use
    return {
        name: import_name_from_module(name, module_name, lazy=lazy)
        for name in public_names
    }


class DeducePublicInterfaceError(Exception):
    """
    Raised when `deduce_stdlib_public_interface()` fails to deduce the public interface
    of a given module.
    """


@raises(RuntimeError, "Fail to deduce public interface of module '{module_name}'")
def deduce_stdlib_public_interface(module_name: str) -> set[str]:
    """
    Try best effort to heuristically determine public names exported by a stdlib module.

    Raise `DeducePublicInterfaceError` on failure.
    """

    if module_name not in IMPORTABLE_STDLIB_MODULES:
        raise ValueError(f"{module_name} is not importable stdlib module")

    # The builtins module is a special case
    # Some exported public names from builtins module are prefixed with underscore,
    # hence ignored by the standard wildcard import mechanism. Examples are `__import__`
    # and `__debug__`.
    if module_name == "builtins":
        return set(BUILTINS_NAMES)

    try:
        return set(import_name_from_module("__all__", module_name))
    except ImportError:
        pass

    # Use a separate clean interpreter to retrieve public names.
    #
    # This is to workaround the problem that a preceding importing of submodules could
    # lead to inadvertent and surprising injection of such submodules into the namespace
    # of the parent module. Such problem would have led to nondeterministic result from
    # the `deduce_stdlib_public_interface()` function if not taken good care of.
    #
    # An example is the `distutils` module. Whether `msvccompiler` appears in the
    # result of `from distutils import *` is affected by whether
    # `distutils.msvccompiler` has been imported before.

    # TODO create a subinterpreter within the same process to reduce performance overhead

    # TODO maybe we can just use test.support.CleanImport instead of the heavy solution
    # - subprocess to launch another interpreter instance ?

    # TODO rewrite in functional programming style

    python_executable = sys.executable or "python"
    source = (
        "symtab = {}\n"
        f"exec('from {module_name} import *', dict(), symtab)\n"
        "for symbol in symtab: print(symbol)\n"
    )
    command = [python_executable, "-c", source]
    # Spawn subprocess with stderr captured, so as to avoid cluttering console output
    cmd_output = subprocess.check_output(command, stderr=subprocess.STDOUT, text=True)

    public_names = set(cmd_output.splitlines())

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

    def is_another_stdlib(symbol: object) -> bool:
        """
        Detect if the symbol is possibly another standard library module imported to
        this module, hence should not be considered part of the public names of this
        module.
        """

        return (
            inspect.ismodule(symbol)
            and symbol.__name__ in STDLIB_MODULES
            and not symbol.__name__.startswith(module_name + ".")
        )

    def from_another_stdlib(symbol: object) -> bool:
        """
        Detect if the symbol is possibly a public name from another standard library
        module, imported to this module, hence should not be considered part of the
        public names of this module.
        """

        origin: Optional[str] = getattr(symbol, "__module__", None)
        return (
            origin in STDLIB_MODULES
            and origin != module_name
            and not origin.startswith(module_name + ".")
        )

    symtab = wildcard_import_module(module_name)

    for name, symbol in symtab.items():
        if is_another_stdlib(symbol) or from_another_stdlib(symbol):
            public_names.remove(name)

    return public_names


def gather_stdlib_symbol_ids() -> set[int]:

    stdlib_symbol_ids: set[int] = set()

    for module_name in IMPORTABLE_STDLIB_MODULES:

        # Suppress DeprecationWarning, because we know for sure that we are not intended
        # to use the deprecated names here.
        #
        # `contextlib.suppress` is not used because it won't suppress warnings.

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            module = importlib.import_module(module_name)

            stdlib_symbol_ids.add(id(module))

            symbol_table = import_stdlib_public_names(
                module_name, include_deprecated=True
            )

            for symbol in symbol_table.values():
                stdlib_symbol_ids.add(id(symbol))

    return stdlib_symbol_ids


STDLIB_SYMBOLS_IDS = cast(set[int], Proxy(gather_stdlib_symbol_ids))


def from_stdlib(symbol: object) -> bool:
    """Check if a symbol comes from standard libraries. Try best effort."""

    # The id() approach could fail if importlib.reload() has been called or sys.modules
    # has been manipulated.
    #
    # So it's a try-best-effort thing.

    return id(symbol) in STDLIB_SYMBOLS_IDS


def convert_version_to_tuple(version: str) -> VersionTuple:
    """
    Convert version info from string representation to tuple representation.
    The tuple representation is convenient for direct comparison.
    """

    m = regex.fullmatch(r"(?P<major>\d+)\.(?P<minor>\d+)", version)

    if not m:
        raise ValueError(f"{version} is not a valid version")

    major, minor = m.group("major", "minor")
    version_tuple = (int(major), int(minor))

    return version_tuple


def load_deprecated_modules() -> dict[VersionTuple, frozenset[str]]:
    """Load DEPRECATED_MODULES from JSON file"""

    json_file = Path(__file__).with_name("deprecated_modules.json")
    json_text = json_file.read_text(encoding="utf-8")
    json_obj = cast(dict[str, list[str]], commentjson.loads(json_text))

    return {
        convert_version_to_tuple(version): frozenset(modules)
        for version, modules in json_obj.items()
    }


def load_deprecated_names() -> dict[VersionTuple, dict[str, frozenset[str]]]:
    """Load DEPRECATED_NAMES from JSON file"""

    json_file = Path(__file__).with_name("deprecated_names.json")
    json_text = json_file.read_text(encoding="utf-8")
    json_obj = cast(dict[str, dict[str, list[str]]], commentjson.loads(json_text))

    res: dict[VersionTuple, dict[str, frozenset[str]]] = {}

    for version, modules in json_obj.items():
        version_tuple = convert_version_to_tuple(version)
        res[version_tuple] = {
            module: frozenset(names) for module, names in modules.items()
        }

    return res


DEPRECATED_MODULES = cast(
    dict[VersionTuple, frozenset[str]], Proxy(load_deprecated_modules)
)

DEPRECATED_NAMES = cast(
    dict[VersionTuple, dict[str, frozenset[str]]], Proxy(load_deprecated_names)
)


def deprecated_modules(version: str = None) -> set[str]:
    """
    Return a set of modules who are deprecated after the given version.

    If no version is given, default to the current version.

    The `version` parameter takes argument of the form `3.9`, `4.7`, etc.
    """

    if version is None:
        version_tuple = sys.version_info[:2]
    else:
        version_tuple = convert_version_to_tuple(version)

    modules: set[str] = set()

    for _version, _modules in DEPRECATED_MODULES.items():
        if version_tuple >= _version:
            modules |= _modules

    return modules


def deprecated_names(module: str, *, version: str = None) -> set[str]:
    """
    Return a set of names from a stdlib module who are deprecated after the given version.

    If no version is given, default to the current version.

    The `version` parameter takes argument of the form `3.9`, `4.7`, etc.
    """

    if module not in IMPORTABLE_STDLIB_MODULES:
        raise ValueError(f"{module} is not importable stdlib module")

    if version is None:
        version_tuple = sys.version_info[:2]
    else:
        version_tuple = convert_version_to_tuple(version)

    names: set[str] = set()

    for _version, _modules in DEPRECATED_NAMES.items():
        if version_tuple < _version:
            continue

        for _module, _names in _modules.items():
            if module is None or module == _module:
                names |= _names

    return names


@cache
def load_stdlib_public_names(version: str) -> dict[str, frozenset[str]]:
    """Load stdlib public names data from JSON file"""

    if not re.fullmatch(r"\d+\.\d+", version):
        raise ValueError(f"{version} is not a valid version")

    try:
        json_file = Path(__file__).with_name("stdlib_public_names") / (
            version + ".json"
        )
        json_text = json_file.read_text(encoding="utf-8")
        json_obj = json.loads(json_text)

        return {module: frozenset(names) for module, names in json_obj.items()}

    except FileNotFoundError:
        raise ValueError(
            f"there is no data of stdlib public names for Python version {version}"
        ) from None


def stdlib_public_names(module: str, *, version: str = None) -> set[str]:
    """
    Return a set of public names of a stdlib module, in specific Python version.

    If no version is given, default to the current version.

    The `version` parameter takes argument of the form `3.9`, `4.7`, etc.
    """

    if module not in IMPORTABLE_STDLIB_MODULES:
        raise ValueError(f"{module} is not importable stdlib module")

    version = version or ".".join(str(c) for c in sys.version_info[:2])

    return set(load_stdlib_public_names(version)[module])
