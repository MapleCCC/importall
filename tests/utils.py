import warnings
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import TypeVar


__all__ = ["eval_name", "pytest_not_deprecated_call", "issubmapping"]


KT = TypeVar("KT")
VT = TypeVar("VT")


def eval_name(name: str) -> object:
    """
    The use of `eval()` on arbitrary string has been considered dangerous practice.
    `eval_name()` is a safer and specialized alternative to `eval()`.
    It only evaluates expression consisting of a single name.
    """

    if not name.isidentifier():
        raise ValueError(f"Invalid name: {name}")

    return eval(name)


@contextmanager
def pytest_not_deprecated_call() -> Iterator[None]:
    """
    Return a context manager to assert that the code within context doesn't trigger any
    `DeprecationWarning`.

    This utility is intended for use in test code employing pytest framework. It
    shoud not be used otherwise.
    """

    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always", DeprecationWarning)
        yield

    for warning_message in record:
        assert not issubclass(warning_message.category, DeprecationWarning)


def issubmapping(m1: Mapping[KT, VT], m2: Mapping[KT, VT]) -> bool:
    return all(value == m2[key] for key, value in m1.items())
