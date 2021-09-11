from json import JSONDecodeError
from typing import cast

import pytest
from hypothesis import given
from hypothesis.strategies import integers

from importall.utils import (
    Proxy,
    hashable,
    jsonc_loads,
    profile,
    provide_lazy_version,
    singleton_class,
)


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


@pytest.mark.xfail
def test_jsonc_loads() -> None:

    text = """
// This is a C-style single-line comment

/*
 * This is a C-style multi-line comment
/*

{ "1": 1 }  // This is also a C-style single-line comment

# This is a Python-style comment
    """

    jsonobj = cast(dict, jsonc_loads(text))
    assert jsonobj["1"] == 1


@pytest.mark.xfail
def test_jsonc_loads_invalid_input() -> None:

    text = """
// This is a C-style single-line comment

/*
 * This is a C-style multi-line comment
/*

{ "1" 1 }  // This is also a C-style single-line comment

# This is a Python-style comment
    """

    with pytest.raises(JSONDecodeError, match="Expecting ':' delimiter"):
        jsonc_loads(text)


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


@pytest.mark.xfail
@given(integers())
def test_Proxy(x: int) -> None:
    def func():
        return x

    p = Proxy(func)

    assert p == x
    assert p is x
    assert hash(p) == hash(x)
    assert repr(p) == repr(x)
    assert type(p) == type(x)


@given(integers())
def test_provide_lazy_version(x) -> None:
    @provide_lazy_version
    def inc(x: int) -> int:
        return x + 1

    assert inc(x) == inc.__wrapped__(x) == x + 1
