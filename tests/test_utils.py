import pytest
from hypothesis import given
from hypothesis.strategies import integers

from importall.utils import hashable, profile, provide_lazy_version, singleton_class


def test_singleton_class() -> None:
    @singleton_class
    class A:
        pass

    assert A() is A()


@given(integers())
def test_profile(x: int) -> None:
    @profile
    def inc(x: int) -> int:
        return x + 1

    assert inc(x) == x + 1


def test_hashable() -> None:

    assert hashable(1)
    assert hashable(1.0)
    assert hashable(None)
    assert hashable(True)
    assert hashable("")
    assert hashable(globals)
    assert hashable(exec)
    assert hashable(ValueError)

    assert not hashable([])
    assert hashable(tuple())
    # test hashability of dict
    assert not hashable({})
    # test hashability of set
    assert not hashable({1})

    def func():
        pass

    class A:
        pass

    assert hashable(func)
    assert hashable(A)
    assert hashable(A())

    assert hashable(hashable)

    assert hashable(pytest)


@given(integers())
def test_provide_lazy_version(x) -> None:
    @provide_lazy_version
    def inc(x: int) -> int:
        return x + 1

    assert inc(x) == inc.__wrapped__(x) == x + 1
