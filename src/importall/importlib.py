import __future__
import importlib
import inspect
import subprocess
import sys
import warnings
from functools import partial
from typing import Optional

from lazy_object_proxy import Proxy

from .stdlib_list import IMPORTABLE_STDLIB_MODULES, STDLIB_MODULES
from .typing import SymbolTable
from .utils import deprecated_names, profile, singleton_class, stdlib_public_names


__all__ = [
    "import_public_names",
    "deduce_public_interface",
    "import_name_from_module",
    "wildcard_import_module",
    "from_stdlib",
    "clean_up_import_cache",
]


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


def import_name_from_module(name: str, module: str) -> object:
    """Programmatically import a name from a module"""

    try:
        return getattr(importlib.import_module(module), name)
    except AttributeError:
        raise ImportError(f"cannot import name '{name}' from '{module}'") from None


@profile
def wildcard_import_module(module_name: str) -> SymbolTable:
    """
    Programmatically wildcard import a module.

    Could raise `ModuleNotFoundError` or `ImportError`.
    """

    # The __future__ module is a special case.
    # Wildcard-importing the __future__ library yields SyntaxError.
    if module_name == "__future__":
        return {name: getattr(__future__, name) for name in __future__.__all__}

    symtab: SymbolTable = {}
    exec(f"from {module_name} import *", {}, symtab)
    return symtab


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


def clean_up_import_cache(module_name: str) -> None:
    """
    Clean up the cache entries related to the given module, in caches populated by the
    import mechanism.

    Useful when module-level behaviors is desired to re-happen, such as the emission of
    the `DeprecationWarning` on import.
    """

    # Reference: Import cache mechanism https://docs.python.org/3.9/reference/import.html#the-module-cache

    def clean_cache_of_alias(module_name: str) -> None:

        # Detect alias
        # Reference: source of test.support.CleanImport https://github.com/python/cpython/blob/v3.9.0/Lib/test/support/__init__.py#L1241

        module = sys.modules[module_name]
        if module.__name__ != module_name:
            del sys.modules[module.__name__]

    def clean_cache_of_submodules(module_name: str) -> None:

        # When a module is imported, its submodules are possibly also implicitly
        # imported.

        submodules = []

        for mod in sys.modules:
            if mod.startswith(module_name + "."):
                submodules.append(mod)

        for mod in submodules:
            del sys.modules[mod]

    def clean_cache_of_ascendants(module_name: str) -> None:

        # When a module is imported, its ascendant modules are also implicitly imported.
        # We need to evict their corresponding cache entries as well.
        #
        # Reference: https://docs.python.org/3.9/reference/import.html#searching

        idx = module_name.rfind(".")
        while idx != -1:
            module_name = module_name[:idx]

            # Use pop() instead of del, because it's not out of possibility that
            # sys.modules could have been tampered with by other code.

            sys.modules.pop(module_name, None)
            idx = module_name.rfind(".")

    if module_name not in sys.modules:
        return

    clean_cache_of_alias(module_name)

    clean_cache_of_submodules(module_name)

    clean_cache_of_ascendants(module_name)

    del sys.modules[module_name]
