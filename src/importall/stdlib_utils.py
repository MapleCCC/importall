"""
A collection of utilities related to standard libraries.
"""


import __future__
import importlib
import inspect
import subprocess
import sys
import warnings
from functools import partial
from typing import Optional

from lazy_object_proxy import Proxy

from .importlib import import_name_from_module, wildcard_import_module
from .stdlib_list import IMPORTABLE_STDLIB_MODULES, STDLIB_MODULES
from .typing import SymbolTable
from .utils import deprecated_names, singleton_class, stdlib_public_names


__all__ = ["import_public_names", "deduce_public_interface", "from_stdlib"]


def import_public_names(
    module_name: str, *, lazy: bool = False, include_deprecated: bool = False
) -> SymbolTable:
    """
    Return a symbol table containing all public names defined in the module.

    By default, names are eagerly imported. One can reduce the overhead by setting the
    `lazy` parameter to `True` to enable lazy import mode.

    By default, deprecated names are not included. It is designed so because
    deprecated names hopefully should not be used anymore, their presence only for
    easing the steepness of API changes and providing a progressive cross-version
    migration experience. If you are sure you know what you are doing, override the default
    behavior by setting the `include_deprecated` parameter to `True` (**NOT RECOMMENDED!**).
    """

    public_names = stdlib_public_names(module_name)

    if not include_deprecated:
        public_names -= deprecated_names(module=module_name)

    eager = not lazy

    if eager:
        module = importlib.import_module(module_name)
        return {name: getattr(module, name) for name in public_names}

    else:

        def eager_import(name: str) -> object:
            return import_name_from_module(name, module_name)

        return {name: Proxy(partial(eager_import, name)) for name in public_names}


def deduce_public_interface(module_name: str) -> set[str]:
    """Try best effort to heuristically determine public names exported by a module"""

    # The __future__ module is a special case
    # Wildcard importing the __future__ module yields SyntaxError
    if module_name == "__future__":
        return set(__future__.__all__)

    # Use a separate clean interpreter to retrieve public names.
    #
    # This is to workaround the problem that a preceding importing of submodules could
    # lead to inadvertent and surprising injection of such submodules into the namespace
    # of the parent module. Such problem would have led to nondeterministic result from
    # the `deduce_public_interface()` function if not taken good care of.

    # TODO create a subinterpreter within the same process to reduce performance overhead

    executable = sys.executable or "python"
    source = (
        "symtab = {}\n"
        f"exec('from {module_name} import *', dict(), symtab)\n"
        "for symbol in symtab: print(symbol)\n"
    )
    public_names = set(
        subprocess.check_output([executable, "-c", source], text=True).splitlines()
    )

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

    for name, symbol in dict(symtab).items():
        if is_another_stdlib(symbol) or from_another_stdlib(symbol):
            public_names.remove(name)

    return public_names


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

        for module_name in IMPORTABLE_STDLIB_MODULES:
            self._gather_info(module_name)

    def _gather_info(self, module_name: str) -> None:

        # Suppress DeprecationWarning, because we know for sure that we are not intended
        # to use the deprecated names here.
        #
        # `contextlib.suppress` is not used because it won't suppress warnings.

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            module = importlib.import_module(module_name)

            self._stdlib_symbols.add(module)

            symbol_table = import_public_names(module_name, include_deprecated=True)

            for symbol in symbol_table.values():
                try:
                    self._stdlib_symbols.add(symbol)

                except TypeError:
                    self._stdlib_symbol_ids.add(id(symbol))

    def check(self, obj: object) -> bool:
        try:
            return obj in self._stdlib_symbols
        except TypeError:
            return id(obj) in self._stdlib_symbol_ids


# Convenient function for handy invocation of `StdlibChecker().check()`
def from_stdlib(symbol: object) -> bool:
    """Check if a symbol comes from standard libraries. Try best effort."""
    return StdlibChecker().check(symbol)
