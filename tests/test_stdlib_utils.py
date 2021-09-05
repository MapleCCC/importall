import builtins
import functools
from typing import Any

import pytest

from importall.stdlib_utils import (
    from_stdlib,
    deduce_public_interface,
    import_stdlib_public_names,
    deprecated_names,
    deprecated_modules,
    stdlib_public_names,
)


# A workaround to suppress type checker complaints that functools doesn't have the __all__ attribute.
# FIXME add __all__ to functools.pyi in python/typeshed
functools: Any


def test_import_stdlib_public_names():
    symtab = {name: getattr(functools, name) for name in functools.__all__}
    assert import_stdlib_public_names("functools") == symtab


def test_deduce_public_interface():
    public_names = deduce_public_interface("functools")
    assert public_names == set(functools.__all__)


def test_from_stdlib():

    for symbol in [True, False, None, pow, int, all, builtins]:
        assert from_stdlib(symbol)

    assert from_stdlib(functools)
    assert from_stdlib(functools.partial)

    assert not from_stdlib(from_stdlib)
    assert not from_stdlib(test_from_stdlib)
    assert not from_stdlib(pytest)


def test_deprecated_modules():
    assert "distutils.command.bdist_msi" in deprecated_modules()
    assert "distutils.command.bdist_msi" not in deprecated_modules(version="3.8")


def test_deprecated_names():
    assert "List" in deprecated_names(module="typing")
    assert "List" not in deprecated_names(version="3.8", module="typing")


def test_stdlib_public_names():
    assert "partial" in stdlib_public_names("functools")
