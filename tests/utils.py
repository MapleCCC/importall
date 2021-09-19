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


class pytest_not_deprecated_call(warnings.catch_warnings):
    """
    Return a context manager to assert that the code within context doesn't trigger any
    `DeprecationWarning` or `PendingDeprecationWarning`.

    This utility is intended for use in test code employing pytest framework. It
    shoud not be used otherwise.
    """

    def __init__(self) -> None:
        super().__init__(record=True)

    def __enter__(self) -> Optional[list[warnings.WarningMessage]]:
        self._record = super().__enter__()

        warnings.simplefilter("always", DeprecationWarning)
        warnings.simplefilter("always", PendingDeprecationWarning)

        return self._record

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: TracebackType,
    ) -> None:

        __tracebackhide__ = True

        for warning in self._record:
            if issubclass(
                warning.category,
                (DeprecationWarning, PendingDeprecationWarning),
            ):
                pytest.fail("expect no DeprecationWarning or PendingDeprecationWarning")

        super().__exit__(exc_type, exc_value, traceback)


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
