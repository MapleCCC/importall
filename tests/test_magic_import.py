import pytest

from .subtest import _test_stdlib_symbols_in_namespace


@pytest.mark.usefixtures("isolate_environment")
def test_magic_import_everything() -> None:
    import everything

    _test_stdlib_symbols_in_namespace(globals())


@pytest.mark.usefixtures("isolate_environment")
def test_magic_import_all() -> None:
    import all

    _test_stdlib_symbols_in_namespace(globals())
