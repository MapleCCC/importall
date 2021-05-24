# pyright: reportUndefinedVariable=false

import builtins
import inspect
import os
import platform
import sys
from typing import Any

import pytest


os.environ["IMPORTALL_NO_INIT_IMPORT"] = "1"


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

    assert python_implementation() == platform.python_implementation()

    assert nlargest(4, [48, 5, 21, 38, 65, 12, 27, 18]) == [65, 48, 38, 27]

    assert bisect_right([24, 35, 38, 38, 46, 47, 52, 54, 54, 57, 87, 91], 53) == 7

    assert reduce(xor, [58, 37, 96, 115, 20, 15, 8]) == 31

    assert defaultdict(int)[""] == 0

    assert not truth(itemgetter(0)(attrgetter("maps")(ChainMap())))

    # Recover globals(). Polluted globals() seems to hinder pytest smooth run.
    deimportall(globals())


def test_get_all_symbols() -> None:
    from importall import deimportall, get_all_symbols

    symbol_table = get_all_symbols()

    assert symbol_table["log2"](2) == 1

    assert list(symbol_table["combinations"]("ABCD", 2)) == [
        ("A", "B"),
        ("A", "C"),
        ("A", "D"),
        ("B", "C"),
        ("B", "D"),
        ("C", "D"),
    ]

    assert symbol_table["getrecursionlimit"]() == sys.getrecursionlimit()

    assert symbol_table["python_implementation"]() == platform.python_implementation()

    assert [65, 48, 38, 27] == symbol_table["nlargest"](
        4, [48, 5, 21, 38, 65, 12, 27, 18]
    )

    assert 7 == symbol_table["bisect_right"](
        [24, 35, 38, 38, 46, 47, 52, 54, 54, 57, 87, 91], 53
    )

    assert 31 == symbol_table["reduce"](
        symbol_table["xor"], [58, 37, 96, 115, 20, 15, 8]
    )

    assert symbol_table["defaultdict"](int)[""] == 0

    assert not symbol_table["truth"](
        symbol_table["itemgetter"](0)(
            symbol_table["attrgetter"]("maps")(symbol_table["ChainMap"]())
        )
    )

    # Recover globals(). Polluted globals() seems to hinder pytest smooth run.
    deimportall(globals())


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

    assert python_implementation() == platform.python_implementation()

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
        assert python_implementation() == platform.python_implementation()

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

    # Recover globals(). Polluted globals() seems to hinder pytest smooth run.
    deimportall(globals())


def test_protect_builtins_parameter() -> None:
    from importall import deimportall, importall

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

    # Recover globals(). Polluted globals() seems to hinder pytest smooth run.
    deimportall(globals())


def test_import_deprecated_parameter() -> None:
    from importall import deimportall, importall

    with pytest.raises(DeprecationWarning):
        importall(global(), include_deprecated=True)

    # Recover globals(). Polluted globals() seems to hinder pytest smooth run.
    deimportall(globals())


def test_prioritized_parameter_iterable_argument() -> None:
    from importall import deimportall, importall

    importall(globals())

    assert not inspect.isabstract(Iterable)

    importall(globals(), prioritized=["collections.abc"])

    assert inspect.isabstract(Iterable)

    # Recover globals(). Polluted globals() seems to hinder pytest smooth run.
    deimportall(globals())


def test_prioritized_parameter_mapping_argument() -> None:
    from importall import deimportall, importall

    importall(globals())

    assert not inspect.isabstract(Iterable)

    importall(globals(), prioritized={"collections.abc": 1, "typing": -1})

    assert inspect.isabstract(Iterable)

    # Recover globals(). Polluted globals() seems to hinder pytest smooth run.
    deimportall(globals())


def test_ignore_parameter() -> None:
    from importall import deimportall, importall

    importall(globals())

    assert not inspect.isabstract(Iterable)

    importall(globals(), ignore=["typing"])

    assert inspect.isabstract(Iterable)

    # Recover globals(). Polluted globals() seems to hinder pytest smooth run.
    deimportall(globals())


def eval_name(name: str) -> Any:
    """
    The use of `eval()` on arbitrary string has been considered dangerous practice.
    `eval_name()` is a safer and specialized alternative to `eval()`.
    It only evaluates expression consisting of a single name.
    """

    if not name.isidentifier():
        raise ValueError(f"Invalid name: {name}")

    return eval(name)
