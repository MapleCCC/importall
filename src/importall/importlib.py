import __future__

import sys
from collections.abc import Sequence
from typing import Literal, overload

from .typing import SymbolTable
from .utils import profile, provide_lazy_version


__all__ = ["import_name_from_module", "wildcard_import_module", "clean_up_import_cache"]


MODULE_STR_VALUED_ATTRIBUTES = Literal[
    "__cached__", "__doc__", "__file__", "__name__", "__package__"
]


@overload
def import_name_from_module(
    name: Literal["__all__"], module: str, lazy: bool = ...
) -> Sequence[str]:
    ...


@overload
def import_name_from_module(
    name: MODULE_STR_VALUED_ATTRIBUTES, module: str, lazy: bool = ...
) -> str:
    ...


@overload
def import_name_from_module(name: str, module: str, lazy: bool = ...) -> object:
    ...


@provide_lazy_version
def import_name_from_module(name: str, module: str) -> object:
    """
    Programmatically import a name from a module.

    Such a name could be of a top level symbol defined or imported by that module, or a
    submodule of that module.

    Setting the keyword argument `lazy` to `True` to enable lazy import mode. The return
    result looks like the normal result, but it's only when the result is used by
    external code that the actual import happens. Useful when importing a module is
    considered expensive.
    """

    # The __future__ module is a special case.
    # `from __future__ import xxx` is a special syntax, called future statement. And the
    # precedence of future statement is higher than that of import statement.
    # See the production rule for the nonterminal `future_stmt` in https://docs.python.org/3/reference/simple_stmts.html#future-statements.
    if module == "__future__":
        return getattr(__future__, name)

    # The builtins module is a special case.
    # Some names from builtins module are reserve keywords in Python syntax, such as
    # `True`, `False`, and `None`.
    # Also, some special names are unassignable, such as `__debug__`.
    if module == "builtins" and name in {"True", "False", "None", "__debug__"}:
        return eval(name)

    exec(f"from {module} import {name}")
    return eval(name)


@profile
def wildcard_import_module(module_name: str) -> SymbolTable:
    """
    Programmatically wildcard import a module.

    Raise `ModuleNotFoundError` if the module with given name can't be found.
    """

    # The __future__ module is a special case.
    # Wildcard-importing the __future__ library yields SyntaxError.
    if module_name == "__future__":
        return {name: getattr(__future__, name) for name in __future__.__all__}

    symtab: SymbolTable = {}
    # NOTE it's more robust to use the `locals` argument instead of the `globals`
    # argument to collect symbols, because the `globals` argument could have been
    # implicitly and surprisingly altered, such as being inserted a `__builtins__` key.
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
            if mod.split(".")[0] == module_name:
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
