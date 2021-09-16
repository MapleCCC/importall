import email.generator
import functools
import sys

import pytest

from importall.importlib import (
    clean_up_import_cache,
    import_name_from_module,
    wildcard_import_module,
)

from .utils import INEXISTENT_MODULE


def test_import_name_from_module() -> None:

    # FIXME should use `is` instead of `==`

    # import top level symbol
    assert import_name_from_module("partial", "functools") == functools.partial
    assert (
        import_name_from_module("partial", "functools", lazy=True) == functools.partial
    )

    # import submodule
    assert import_name_from_module("generator", "email") == email.generator
    assert import_name_from_module("generator", "email", lazy=True) == email.generator

    with pytest.raises(ImportError):
        assert import_name_from_module("xxx", "functools")

    with pytest.raises(ModuleNotFoundError):
        assert import_name_from_module("xxx", INEXISTENT_MODULE)


def test_wildcard_import_module() -> None:

    # Wildcard import a module that defines __all__
    symtab = {}
    exec("from functools import *", {}, symtab)
    assert wildcard_import_module("functools") == symtab

    # Wildcard import a module that doesn't define __all__
    symtab = {}
    exec("from itertools import *", {}, symtab)
    assert wildcard_import_module("itertools") == symtab

    with pytest.raises(ModuleNotFoundError):
        wildcard_import_module(INEXISTENT_MODULE)


def test_clean_up_import_cache() -> None:

    with pytest.deprecated_call(match="the binhex module is deprecated"):
        import binhex

    clean_up_import_cache("binhex")

    assert "binhex" not in sys.modules

    with pytest.deprecated_call(match="the binhex module is deprecated"):
        import binhex
