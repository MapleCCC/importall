import sys
from collections.abc import Mapping
from platform import python_implementation
from typing import Any, cast


__all__ = ["_test_stdlib_symbols_in_namespace"]


# TODO if we remove the underscore prefix, will pytest fail ?
def _test_stdlib_symbols_in_namespace(namespace: Mapping[str, object]) -> None:

    ns = cast(Mapping[str, Any], namespace)

    assert ns["log2"](2) == 1

    assert list(ns["combinations"]("ABCD", 2)) == [
        ("A", "B"),
        ("A", "C"),
        ("A", "D"),
        ("B", "C"),
        ("B", "D"),
        ("C", "D"),
    ]

    assert ns["getrecursionlimit"]() == sys.getrecursionlimit()

    assert ns["python_implementation"]() == python_implementation()

    assert ns["nlargest"](4, [48, 5, 21, 38, 65, 12, 27, 18]) == [65, 48, 38, 27]

    assert ns["bisect_right"]([24, 35, 38, 38, 46, 47, 52, 54, 54, 57, 87, 91], 53) == 7

    assert ns["reduce"](ns["xor"], [58, 37, 96, 115, 20, 15, 8]) == 31

    assert ns["defaultdict"](int)[""] == 0

    assert not ns["truth"](
        ns["itemgetter"](0)(ns["attrgetter"]("maps")(ns["ChainMap"]()))
    )

    assert ns["barry_as_FLUFL"].optional[:2] == (3, 1)
