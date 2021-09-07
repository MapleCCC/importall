import os
import sys

import pytest


__all__ = ["isolate_environement"]


@pytest.fixture()
def isolate_globals():
    # Copy a reference, because the name `globals` can't be accessed after the `.clear()` call.
    globals_dict = globals()
    original_globals = dict(globals_dict)
    yield
    globals_dict.clear()
    globals_dict |= original_globals


@pytest.fixture()
def isolate_sys_modules():
    original_sys_modules = dict(sys.modules)
    yield
    sys.modules.clear()
    sys.modules |= original_sys_modules


@pytest.fixture()
def isolate_os_environ():
    original_os_environ = dict(os.environ)
    yield
    os.environ.clear()
    os.environ |= original_os_environ


@pytest.fixture(autouse=True)
def isolate_environement(isolate_globals, isolate_sys_modules, isolate_os_environ):
    """
    Before the test runs, backup the environment.
    After the test runs, restore the environment.
    """

    # Reference: test.support.CleanImport() function implementation
    # https://github.com/python/cpython/blob/v3.9.0/Lib/test/support/__init__.py#L1241
