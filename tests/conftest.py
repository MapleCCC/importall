import os
import sys

import pytest

from .utils import mock_dicts


@pytest.fixture
def mock_environment(request):
    """
    Before the test runs, backup the environment.
    After the test runs, restore the environment.
    """

    # Reference: test.support.CleanImport() function implementation
    # https://github.com/python/cpython/blob/v3.9.0/Lib/test/support/__init__.py#L1241

    f_globals = request.function.__globals__

    with mock_dicts(f_globals, sys.modules, os.environ):
        yield
