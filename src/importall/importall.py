from collections.abc import Iterable, Mapping
from typing import Union, cast
from uuid import uuid4

from .inspect import getcallerframe, is_called_at_module_level
from .stdlib_list import BUILTINS_NAMES, IMPORTABLE_STDLIB_MODULES
from .stdlib_utils import deprecated_modules, import_stdlib_public_names
from .typing import SymbolTable
from .utils import profile


__all__ = ["importall", "deimportall", "get_all_symbols"]


KEY_TRACKING_INJECTED_SYMBOLS = uuid4().hex


def importall(
    namespace: SymbolTable = None,
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

    The `namespace` parameter accepts a symbol table to populate. Usually the caller
    passes in `globals()`.

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
    if namespace is None and not is_called_at_module_level():
        raise RuntimeError(
            "importall() function with default namespace argument is only allowed to be invoked at the module level"
        )

    namespace = namespace or getcallerframe().f_globals

    symtab = get_all_symbols(
        lazy=lazy,
        include_deprecated=include_deprecated,
        prioritized=prioritized,
        ignore=ignore,
    )

    if protect_builtins:
        for name in BUILTINS_NAMES:
            symtab.pop(name, None)

    namespace.update(symtab)

    namespace[KEY_TRACKING_INJECTED_SYMBOLS] = symtab


def deimportall(namespace: SymbolTable = None) -> None:
    """
    De-import all imported names. Recover/restore the namespace.

    The `deimportall()` function is only allowed to be called at the module level.
    Attempting to invoke `deimportall()` in class or function definitions will raise a
    RuntimeError.
    """

    # Check against invocation at non-module level
    if namespace is None and not is_called_at_module_level():
        raise RuntimeError(
            "deimportall() function with default namespace argument is only allowed to be invoked at the module level"
        )

    namespace = namespace or getcallerframe().f_globals

    injected_symbols = cast(
        SymbolTable, namespace.pop(KEY_TRACKING_INJECTED_SYMBOLS, {})
    )

    sentinel = object()

    for name, symbol in injected_symbols.items():
        if getattr(namespace, name, sentinel) is symbol:
            del namespace[name]


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
        symtab |= import_stdlib_public_names(
            module_name, lazy=lazy, include_deprecated=include_deprecated
        )

    return symtab
