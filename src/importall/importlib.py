import __future__
import importlib
import sys

from .typing import SymbolTable
from .utils import profile


__all__ = ["import_name_from_module", "wildcard_import_module", "clean_up_import_cache"]


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
