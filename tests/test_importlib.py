import email.generator
import functools

import pytest

from importall.importlib import (
    clean_up_import_cache,
    import_name_from_module,
    wildcard_import_module,
)


def test_import_name_from_module() -> None:
    assert import_name_from_module("partial", "functools") == functools.partial
    assert import_name_from_module("generator", "email") == email.generator


def test_wildcard_import_module() -> None:
    symtab = {}
    exec("from functools import *", {}, symtab)
    assert wildcard_import_module("functools") == symtab

    symtab = {}
    exec("from itertools import *", {}, symtab)
    assert wildcard_import_module("itertools") == symtab


def test_clean_up_import_cache() -> None:
    with pytest.deprecated_call(match="the binhex module is deprecated"):
        import binhex

    clean_up_import_cache("binhex")

    with pytest.deprecated_call(match="the binhex module is deprecated"):
        import binhex
