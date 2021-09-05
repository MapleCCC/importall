from hypothesis import given
from hypothesis.strategies import integers

from importall.functools import nulldecorator


@given(integers())
def test_nulldecorator(x: int) -> None:
    @nulldecorator
    def inc(x: int) -> int:
        return x + 1

    assert inc(x) == x + 1
