import builtins

import pytest

from importall import deimportall, get_all_symbols, importall
from importall.stdlib_list import BUILTINS_NAMES

from .fixtures import isolate_environement  # type: ignore # autouse fixture
from .subtest import _test_stdlib_symbols_in_namespace
from .utils import eval_name, pytest_not_deprecated_call


class TestImportallFunction:
    """
    Unit tests for testing the `importall()` function
    """

    def test_plain_call(self) -> None:

        importall(globals())
        _test_stdlib_symbols_in_namespace(globals())

    def test_default_globals_argument(self) -> None:

        source = "from importall import importall; importall()"
        symtab = {}
        exec(source, {}, symtab)
        _test_stdlib_symbols_in_namespace(symtab)

        with pytest.raises(
            RuntimeError,
            match="importall() function with default namespace argument is only allowed to be invoked at the module level",
        ):
            importall()

    def test_lazy_parameter_is_false(self) -> None:

        importall(globals(), lazy=False)
        _test_stdlib_symbols_in_namespace(globals())

    def test_protect_builtins_parameter_is_true(self) -> None:

        importall(globals(), protect_builtins=True)

        for name in BUILTINS_NAMES:
            assert eval_name(name) is getattr(builtins, name)

    def test_protect_builtins_parameter_is_false(self) -> None:

        assert open.__module__ == "io"

        importall(globals(), protect_builtins=False)

        assert open.__module__ == "webbrowser"

    def test_include_deprecated_parameter_is_false(self) -> None:

        with pytest_not_deprecated_call():
            importall(globals(), include_deprecated=False)

    def test_include_deprecated_parameter_is_true(self) -> None:

        # This unit test makes a reasonable assumption that there are very likely always
        # some deprecations going on in Python's codebase.

        with pytest.deprecated_call():
            importall(globals(), include_deprecated=True)

    def test_prioritized_parameter_iterable_argument(self) -> None:

        importall(globals())

        assert compress.__module__ == "zlib"  # type: ignore

        importall(globals(), prioritized=["lzma"])

        assert compress.__module__ == "lzma"  # type: ignore

    def test_prioritized_parameter_mapping_argument(self) -> None:

        importall(globals())

        assert compress.__module__ == "zlib"  # type: ignore

        importall(globals(), prioritized={"lzma": 1, "zlib": -1})

        assert compress.__module__ == "lzma"  # type: ignore

    def test_ignore_parameter(self) -> None:

        importall(globals())

        assert compress.__module__ == "zlib"  # type: ignore

        importall(globals(), ignore=["zlib"])

        assert compress.__module__ == "lzma"  # type: ignore


def test_get_all_symbols() -> None:

    _test_stdlib_symbols_in_namespace(get_all_symbols())


def test_deimportall() -> None:

    origin_globals = globals().copy()

    importall(globals())

    deimportall(globals())

    assert globals() == origin_globals

    with pytest.raises(
        RuntimeError,
        match="deimportall() function with default namespace argument is only allowed to be invoked at the module level",
    ):
        deimportall()
