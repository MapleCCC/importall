from hypothesis import given
from hypothesis.strategies import integers

from importall.utils import profile, provide_lazy_version


@given(integers())
def test_profile(x: int) -> None:
    @profile
    def inc(x: int) -> int:
        return x + 1

    assert inc(x) == x + 1


@given(integers())
def test_provide_lazy_version(x) -> None:
    @provide_lazy_version
    def inc(x: int) -> int:
        return x + 1

    assert inc(x, lazy=True) == inc(x, lazy=False) == inc.__wrapped__(x) == x + 1
