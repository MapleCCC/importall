import sys
import warnings
from collections.abc import Iterator, Mapping, MutableMapping
from contextlib import ExitStack, contextmanager
from typing import NoReturn, TypeVar, Union

import pytest
from recipes.importlib import importable


__all__ = [
    "pytest_not_raises",
    "pytest_not_deprecated_call",
    "issubmapping",
    "mock_dict",
    "INEXISTENT_MODULE",
]


KT = TypeVar("KT")
VT = TypeVar("VT")


class Unreachable(RuntimeError):
    """Raised when supposedly unreachable code is reached"""


def pytest_fail_from(
    msg: str = "",
    pytrace: bool = True,
    *,
    cause: Union[BaseException, type[BaseException], None],
) -> NoReturn:

    """
    Enhance `pytest.fail()` with exception chaining.

    The `cause` parameter accepts either an exception class or instance, or None.
    The semantic of the value is similar to that of the `raise-from` statement.
    Refer to the official document of `raise-from` statement for details:
    https://docs.python.org/3/reference/simple_stmts.html#raise
    """

    __tracebackhide__ = True

    try:
        pytest.fail(msg, pytrace)

    # FIXME pytest doesn't expose `_pytest.outcomes.Failed` as public API, and it would be
    # fragile to rely on private API, hence discouraged. Current naive workaround is to
    # blindly and greedily catch any exceptions.
    except BaseException as exc:
        raise exc from cause

    raise Unreachable


@contextmanager
def pytest_not_raises(
    etype: Union[type[BaseException], tuple[type[BaseException], ...]] = BaseException
) -> Iterator[None]:
    """
    Return a context manager to assert that code within context doesn't raise specified
    exceptions.

    `etype` parameter accepts either an exception type, or a tuple of exception types.

    This utility is intended for use in test code employing pytest framework. It
    shoud not be used otherwise.
    """

    __tracebackhide__ = True

    try:
        yield
    except etype as exc:

        # A workaround to hide traceback of `contextlib._GeneratorContextManager.__exit__`.
        # It's an internal detail of the `contextlib` library.
        sys._getframe(1).f_locals["__tracebackhide__"] = True

        pytest_fail_from(f"expect no exception of type {etype}", cause=exc)


@contextmanager
def pytest_not_deprecated_call() -> Iterator[None]:
    """
    Return a context manager to assert that the code within context doesn't trigger any
    `DeprecationWarning` or `PendingDeprecationWarning`.

    This utility is intended for use in test code employing pytest framework. It
    shoud not be used otherwise.
    """

    __tracebackhide__ = True

    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always", DeprecationWarning)
        warnings.simplefilter("always", PendingDeprecationWarning)
        yield

    # A workaround to hide traceback of `contextlib._GeneratorContextManager.__exit__`.
    # It's an internal detail of the `contextlib` library.
    sys._getframe(1).f_locals["__tracebackhide__"] = True

    for warning in record:
        if issubclass(
            warning.category, (DeprecationWarning, PendingDeprecationWarning)
        ):
            pytest.fail("expect no DeprecationWarning or PendingDeprecationWarning")


def issubmapping(m1: Mapping[KT, VT], m2: Mapping[KT, VT], /) -> bool:
    return all(value == m2[key] for key, value in m1.items())


@contextmanager
def _mock_dict(dic: MutableMapping) -> Iterator[None]:
    """A context manager to mock a dictionary"""

    origin_dict = dict(dic)
    try:
        yield
    finally:
        dic.clear()
        dic |= origin_dict


@contextmanager
def mock_dict(*dicts: MutableMapping) -> Iterator[None]:
    """A context manager to mock dictionaries"""

    with ExitStack() as stack:

        for dic in dicts:
            stack.enter_context(_mock_dict(dic))

        yield


# A module that guarantees to be inexistent. Useful for testing behavior that involves
# fiddling with modules.
INEXISTENT_MODULE = "gugugugugugugugugugugu"

assert not importable(INEXISTENT_MODULE)
