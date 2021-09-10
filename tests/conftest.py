import os
import sys

import pytest


__all__ = ["mock_environment"]


@pytest.fixture
def mock_globals(request):
    globals_dict = request.function.__globals__
    original_globals = dict(globals_dict)
    yield
    globals_dict.clear()
    globals_dict |= original_globals


@pytest.fixture
def mock_sys_modules():
    original_sys_modules = dict(sys.modules)
    yield
    sys.modules.clear()
    sys.modules |= original_sys_modules


@pytest.fixture
def mock_os_environ():
    original_os_environ = dict(os.environ)
    yield
    os.environ.clear()
    os.environ |= original_os_environ


@pytest.fixture
def mock_environment(mock_globals, mock_sys_modules, mock_os_environ):
    """
    Before the test runs, backup the environment.
    After the test runs, restore the environment.
    """

    # Reference: test.support.CleanImport() function implementation
    # https://github.com/python/cpython/blob/v3.9.0/Lib/test/support/__init__.py#L1241
