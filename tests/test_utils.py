import operator
import sys

import pytest
from hypothesis import given, settings
from hypothesis.strategies import integers

from importall.utils import profile, provide_lazy_version, run_in_new_interpreter


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


@pytest.mark.asyncio
class TestRunInNewInterpreter:
    """Unit tests for `run_in_new_interpreter()`"""

    @settings(max_examples=5, deadline=3000)
    @given(integers())  # type: ignore # FIXME `@given()`'s type annotation should be updated to accept async function.
    async def test_normal_call(self, x: int) -> None:

        assert x + 1 == await run_in_new_interpreter(operator.add, x, 1)

    async def test_fresh_environment(self) -> None:

        sys.modules["pytest"] = pytest

        assert await run_in_new_interpreter(
            eval, "'pytest' not in __import__('sys').modules"
        )
