# pyright: reportUndefinedVariable=false

import builtins
import os
import platform as platform_module
import sys
from typing import Any

import pytest


@pytest.fixture(scope="function", autouse=True)
def isolate_environement():

    # Reference: test.support.CleanImport() function implementation
    # https://github.com/python/cpython/blob/v3.9.0/Lib/test/support/__init__.py#L1241

    globals_dict = globals()

    # Backup environement
    original_globals = dict(globals_dict)
    original_sys_modules = dict(sys.modules)
    original_os_environ = dict(os.environ)

    yield

    # Restore environment
    globals_dict.clear()
    globals_dict |= original_globals
    sys.modules.clear()
    sys.modules |= original_sys_modules
    os.environ.clear()
    os.environ |= original_os_environ


# Unfortunately, for now we can't test the import inteface. Because wild card import
# is not allowed within function `test_import_interface()`, we have to put the
# `from importall import *` to top level, which causes pytest to collect strange things,
# the nature of which awaits further investigation.
@pytest.mark.skip(
    reason="Unfortunately, for now we can't test the import inteface. Because wild card import"
    "is not allowed within function `test_import_interface()`, we have to put the"
    "`from importall import *` to top level, which causes pytest to collect strange things,"
    "the nature of which awaits further investigation."
)
def test_import_interface() -> None:
    # from importall import *
    pass


def test_function_interface() -> None:
    from importall import importall

    importall(globals())

    assert log2(2) == 1

    assert list(combinations("ABCD", 2)) == [
        ("A", "B"),
        ("A", "C"),
        ("A", "D"),
        ("B", "C"),
        ("B", "D"),
        ("C", "D"),
    ]

    assert getrecursionlimit() == sys.getrecursionlimit()

    assert python_implementation() == platform_module.python_implementation()

    assert nlargest(4, [48, 5, 21, 38, 65, 12, 27, 18]) == [65, 48, 38, 27]

    assert bisect_right([24, 35, 38, 38, 46, 47, 52, 54, 54, 57, 87, 91], 53) == 7

    assert reduce(xor, [58, 37, 96, 115, 20, 15, 8]) == 31

    assert defaultdict(int)[""] == 0

    assert not truth(itemgetter(0)(attrgetter("maps")(ChainMap())))


def test_get_all_symbols() -> None:
    from importall import get_all_symbols

    symtab = get_all_symbols()

    assert symtab["log2"](2) == 1

    assert list(symtab["combinations"]("ABCD", 2)) == [
        ("A", "B"),
        ("A", "C"),
        ("A", "D"),
        ("B", "C"),
        ("B", "D"),
        ("C", "D"),
    ]

    assert symtab["getrecursionlimit"]() == sys.getrecursionlimit()

    assert symtab["python_implementation"]() == platform_module.python_implementation()

    assert [65, 48, 38, 27] == symtab["nlargest"](4, [48, 5, 21, 38, 65, 12, 27, 18])

    assert 7 == symtab["bisect_right"](
        [24, 35, 38, 38, 46, 47, 52, 54, 54, 57, 87, 91], 53
    )

    assert 31 == symtab["reduce"](symtab["xor"], [58, 37, 96, 115, 20, 15, 8])

    assert symtab["defaultdict"](int)[""] == 0

    assert not symtab["truth"](
        symtab["itemgetter"](0)(symtab["attrgetter"]("maps")(symtab["ChainMap"]()))
    )


def test_deimportall() -> None:
    from importall import deimportall, importall

    importall(globals())

    assert log2(2) == 1

    assert list(combinations("ABCD", 2)) == [
        ("A", "B"),
        ("A", "C"),
        ("A", "D"),
        ("B", "C"),
        ("B", "D"),
        ("C", "D"),
    ]

    assert getrecursionlimit() == sys.getrecursionlimit()

    assert python_implementation() == platform_module.python_implementation()

    assert nlargest(4, [48, 5, 21, 38, 65, 12, 27, 18]) == [65, 48, 38, 27]

    assert bisect_right([24, 35, 38, 38, 46, 47, 52, 54, 54, 57, 87, 91], 53) == 7

    assert reduce(xor, [58, 37, 96, 115, 20, 15, 8]) == 31

    assert defaultdict(int)[""] == 0

    assert not truth(itemgetter(0)(attrgetter("maps")(ChainMap())))

    deimportall(globals())

    with pytest.raises(NameError):
        assert log2(2) == 1

    with pytest.raises(NameError):
        assert list(combinations("ABCD", 2)) == [
            ("A", "B"),
            ("A", "C"),
            ("A", "D"),
            ("B", "C"),
            ("B", "D"),
            ("C", "D"),
        ]

    with pytest.raises(NameError):
        assert getrecursionlimit() == sys.getrecursionlimit()

    with pytest.raises(NameError):
        assert python_implementation() == platform_module.python_implementation()

    with pytest.raises(NameError):
        assert nlargest(4, [48, 5, 21, 38, 65, 12, 27, 18]) == [65, 48, 38, 27]

    with pytest.raises(NameError):
        assert bisect_right([24, 35, 38, 38, 46, 47, 52, 54, 54, 57, 87, 91], 53) == 7

    with pytest.raises(NameError):
        assert reduce(xor, [58, 37, 96, 115, 20, 15, 8]) == 31

    with pytest.raises(NameError):
        assert defaultdict(int)[""] == 0

    with pytest.raises(NameError):
        assert not truth(itemgetter(0)(attrgetter("maps")(ChainMap())))


def test_protect_builtins_parameter() -> None:
    from importall import importall

    importall(globals(), protect_builtins=True)

    BUILTINS_NAMES = set(dir(builtins)) - {
        "__doc__",
        "__loader__",
        "__name__",
        "__package__",
        "__spec__",
    }

    for name in BUILTINS_NAMES:
        assert eval_name(name) is getattr(builtins, name)


def test_import_deprecated_parameter() -> None:

    # Disable wild card import because wild card import internally eagerly import every
    # names from standard libraries, populating the sys.modules cache. Importing modules
    # who is already in the sys.mdoules cache would reuse the cache entry, instead of
    # actually executing the module file again, which maens module-level behaviors won't
    # re-happen, such as the emission of the DeprecationWarning on import.
    os.environ["IMPORTALL_DISABLE_WILD_CARD_IMPORT"] = "1"

    from importall import importall

    # This unit test makes a reasonable assumption that there are very likely always
    # some deprecations going on in Python's codebase.

    with pytest.deprecated_call():
        importall(globals(), include_deprecated=True)


def test_prioritized_parameter_iterable_argument() -> None:
    from importall import importall

    importall(globals())

    assert compress.__module__ == "zlib"

    importall(globals(), prioritized=["lzma"])

    assert compress.__module__ == "lzma"


def test_prioritized_parameter_mapping_argument() -> None:
    from importall import importall

    importall(globals())

    assert compress.__module__ == "zlib"

    importall(globals(), prioritized={"lzma": 1, "zlib": -1})

    assert compress.__module__ == "lzma"


def test_ignore_parameter() -> None:
    from importall import importall

    importall(globals())

    assert compress.__module__ == "zlib"

    importall(globals(), ignore=["zlib"])

    assert compress.__module__ == "lzma"


def eval_name(name: str) -> Any:
    """
    The use of `eval()` on arbitrary string has been considered dangerous practice.
    `eval_name()` is a safer and specialized alternative to `eval()`.
    It only evaluates expression consisting of a single name.
    """

    if not name.isidentifier():
        raise ValueError(f"Invalid name: {name}")

    return eval(name)
