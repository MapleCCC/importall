import importlib.util
import warnings
from collections.abc import Iterator, Mapping, MutableMapping
from contextlib import ExitStack, contextmanager
from typing import TypeVar

import pytest


__all__ = [
    "pytest_not_deprecated_call",
    "issubmapping",
    "mock_dict",
    "INEXISTENT_MODULE",
]


KT = TypeVar("KT")
VT = TypeVar("VT")


# FIXME is the impl correct ?
@contextmanager
def pytest_not_deprecated_call() -> Iterator[None]:
    """
    Return a context manager to assert that the code within context doesn't trigger any
    `DeprecationWarning` or `PendingDeprecationWarning`.

    This utility is intended for use in test code employing pytest framework. It
    shoud not be used otherwise.
    """

    with warnings.catch_warnings(record=True) as record:
        warnings.simplefilter("always", DeprecationWarning)
        yield

    for warning_message in record:
        if issubclass(
            warning_message.category, (DeprecationWarning, PendingDeprecationWarning)
        ):
            pytest.fail("expect no DeprecationWarning or PendingDeprecationWarning")


def issubmapping(m1: Mapping[KT, VT], m2: Mapping[KT, VT]) -> bool:
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


def importable(module: str) -> bool:
    """Check if a module is importable."""

    # Reference: https://docs.python.org/3/library/importlib.html#checking-if-a-module-can-be-imported

    return importlib.util.find_spec(module) is not None


# A module that guarantees to be inexistent. Useful for testing behavior that involves
# fiddling with modules.
INEXISTENT_MODULE = "gugugugugugugugugugugu"

assert importable(INEXISTENT_MODULE)
