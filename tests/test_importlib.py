import functools

import pytest

from importall.importlib import (
    import_name_from_module,
    wildcard_import_module,
    clean_up_import_cache,
)


def test_import_name_from_module() -> None:
    assert import_name_from_module("partial", "functools") == functools.partial


def test_wildcard_import_module() -> None:
    symtab = {}
    exec("from functools import *", {}, symtab)
    assert wildcard_import_module("functools") == symtab


def test_clean_up_import_cache() -> None:
    with pytest.deprecated_call():
        import binhex

    clean_up_import_cache("binhex")

    with pytest.deprecated_call():
        import binhex
