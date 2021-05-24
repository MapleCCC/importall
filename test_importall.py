import pytest


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

    assert getrecursionlimit() == __import__("sys").getrecursionlimit()

    assert python_implementation() == __import__("platform").python_implementation()

    assert nlargest(4, [48, 5, 21, 38, 65, 12, 27, 18]) == [65, 48, 38, 27]

    assert bisect_right([24, 35, 38, 38, 46, 47, 52, 54, 54, 57, 87, 91], 53) == 7

    assert reduce(xor, [58, 37, 96, 115, 20, 15, 8]) == 31

    assert defaultdict(int)[""] == 0

    assert not truth(itemgetter(0)(attrgetter("maps")(ChainMap())))

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

    assert getrecursionlimit() == __import__("sys").getrecursionlimit()

    assert python_implementation() == __import__("platform").python_implementation()

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
        assert getrecursionlimit() == __import__("sys").getrecursionlimit()

    with pytest.raises(NameError):
        assert python_implementation() == __import__("platform").python_implementation()

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

    BUILTINS_NAMES = set(dir(__import__("builtins"))) - {
        "__doc__",
        "__loader__",
        "__name__",
        "__package__",
        "__spec__",
    }

    for name in BUILTINS_NAMES:
        assert eval(name) is getattr(__import__("builtins"), name)

    # Recover globals(). Polluted globals() seems to hinder pytest smooth run.
    deimportall(globals())


def test_prioritized_parameter_iterable_argument() -> None:
    from importall import deimportall, importall

    importall(globals())

    assert not __import__("inspect").isabstract(Iterable)

    importall(globals(), prioritized=["collections.abc"])

    assert __import__("inspect").isabstract(Iterable)

    # Recover globals(). Polluted globals() seems to hinder pytest smooth run.
    deimportall(globals())


def test_prioritized_parameter_mapping_argument() -> None:
    from importall import deimportall, importall

    importall(globals())

    assert not __import__("inspect").isabstract(Iterable)

    importall(globals(), prioritized={"collections.abc": 1, "typing": -1})

    assert __import__("inspect").isabstract(Iterable)

    # Recover globals(). Polluted globals() seems to hinder pytest smooth run.
    deimportall(globals())


def test_ignore_parameter() -> None:
    from importall import deimportall, importall

    importall(globals())

    assert not __import__("inspect").isabstract(Iterable)

    importall(globals(), ignore=["typing"])

    assert __import__("inspect").isabstract(Iterable)

    # Recover globals(). Polluted globals() seems to hinder pytest smooth run.
    deimportall(globals())
