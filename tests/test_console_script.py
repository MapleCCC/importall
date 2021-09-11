from runpy import run_module

import pytest

from .subtest import _test_stdlib_symbols_in_namespace

# TODO do some research about how to test an interactive CLI application

@pytest.mark.xfail
def test_console_script() -> None:
    _test_stdlib_symbols_in_namespace(run_module("importall"))
