from hypothesis import given
from hypothesis.strategies import integers

from importall.inspect import getcallerframe, is_called_at_module_level


@given(integers())
def test_getcallerframe(x: int) -> None:
    def f():
        frame = getcallerframe()
        assert frame.f_locals["x"] == x

    f()


def test_is_called_at_module_level() -> None:
    def f():
        assert not is_called_at_module_level()

    f()

    source = """
def g():
    assert is_called_at_module_level()

g()
    """

    exec(source, globals(), locals())
