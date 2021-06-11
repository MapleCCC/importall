import sys
from functools import cache

import regex


__all__ = ["deprecated_modules", "deprecated_names"]


Version = tuple[int, int]


@cache
def deprecated_modules(*, version: str = None) -> set[str]:
    """
    Return a set of modules who are deprecated after the given version.

    If no version is given, default to the current version.

    The `version` parameter takes argument of the form `3.6`, `2.7`, etc.
    """

    if version is None:
        version_tuple = sys.version_info[:2]
    else:
        m = regex.fullmatch(r"(?P<major>\d+)\.(?P<minor>\d+)", version)
        version_tuple = (int(m.major), int(m.minor))

    modules: set[str] = set()

    for _version, _modules in DEPRECATED_MODULES.items():
        if version_tuple >= _version:
            modules |= _modules

    return modules


@cache
def deprecated_names(*, version: str = None, module: str = None) -> set[str]:
    """
    Return a set of names who are deprecated after the given version.

    If no version is given, default to the current version.

    The `version` parameter takes argument of the form `3.6`, `2.7`, etc.
    """

    if version is None:
        version_tuple = sys.version_info[:2]
    else:
        m = regex.fullmatch(r"(?P<major>\d+)\.(?P<minor>\d+)", version)
        version_tuple = (int(m.major), int(m.minor))

    names: set[str] = set()

    for _version, _modules in DEPRECATED_NAMES.items():
        if version_tuple < _version:
            continue

        for _module, _names in _modules.items():
            if module is None or module == _module:
                names |= _names

    return names


# The dict keys are since which versions they are deprecated.
#
# Among these modules, binhex, parser, symbol, formatter, and imp emit DeprecationWarning's when imported.
DEPRECATED_MODULES: dict[Version, set[str]] = {
    (3, 9): {"binhex", "parser", "symbol"},
    (3, 6): {"asynchat", "asyncore", "tkinter.tix"},
    (3, 4): {"formatter", "imp"},
    (3, 3): {"xml.etree.ElementTree"},
    (3, 2): {"optparse"},
    (3, 0): {"email.encoders"},
}


# Not all deprecated names are included, that would be too much and too tedious.
#
# Included are only those deprecated names each of which is one of the names inserted into the
# current namespace when its parent module is wildcard-imported.
#
# The dict keys are since which versions they are deprecated.
DEPRECATED_NAMES: dict[Version, dict[str, set[str]]] = {
    (3, 9): {
        "ast": {"ExtSlice", "Index"},
        "binascii": {"a2b_hqx", "b2a_hqx", "rlecode_hqx", "rledecode_hqx"},
        "typing": {
            "AbstractSet",
            "AsyncContextManager",
            "AsyncGenerator",
            "AsyncIterable",
            "AsyncIterator",
            "Awaitable",
            "ByteString",
            "Callable",
            "ChainMap",
            "Collection",
            "Container",
            "ContextManager",
            "Coroutine",
            "Counter",
            "DefaultDict",
            "Deque",
            "Dict",
            "FrozenSet",
            "Generator",
            "ItemsView",
            "Iterable",
            "Iterator",
            "KeysView",
            "List",
            "Mapping",
            "MappingView",
            "Match",
            "MutableMapping",
            "MutableSequence",
            "MutableSet",
            "OrderedDict",
            "Pattern",
            "Reversible",
            "Sequence",
            "Set",
            "Tuple",
            "Type",
            "ValuesView",
        },
    },
    (3, 8): {
        "ast": {"Bytes", "Ellipsis", "NameConstant", "Num", "Str"},
        "asyncio": {"coroutine"},
        "gettext": {"bind_textdomain_codeset"},
        "gettext": {"ldngettext"},
    },
    (3, 6): {"grp": {"getgrgid"}},
    (3, 5): {"inspect": {"formatargspe", "getcallargs"}},
    (3, 3): {
        "abc": {"abstractclassmethod", "abstractproperty", "abstractstaticmethod"},
        "pkgutil": {"ImpImporter", "ImpLoader"},
        "urllib.request": {"FancyURLopener", "URLopener"},
    },
    (3, 2): {"zipfile": {"BadZipfile"}},
    (3, 1): {"turtle": {"settiltangle"}},
    (3, 0): {"inspect": {"getargspec"}},
    (2, 3): {"tempfile": {"mktemp"}},
}
