import subprocess

import pytest
from hypothesis import given
from hypothesis.strategies import integers

from importall.inspect import getcallerframe, is_called_at_module_level


@given(integers())
def test_getcallerframe(x: int) -> None:
    def f():
        frame = getcallerframe()
        assert frame.f_locals["x"] == x

    f()


def test_getcallerframe_called_from_non_function() -> None:

    source = "from importall.inspect import getcallerframe\n" "getcallerframe()"
    command = ["python", "-c", source]

    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        subprocess.check_output(command, stderr=subprocess.STDOUT, text=True)

    error_message = "RuntimeError: getcallerframe() expects to be called in a function"
    assert error_message in exc_info.value.output


def test_is_called_at_module_level() -> None:

    assert not is_called_at_module_level()

    def f():
        assert not is_called_at_module_level()

    f()

    class A:
        assert not is_called_at_module_level()

        def method(self):
            assert not is_called_at_module_level()

    A().method()

    source = """
def g():
    assert is_called_at_module_level()

g()
    """

    exec(source, {"is_called_at_module_level": is_called_at_module_level})
