import builtins
import functools
from typing import Any

import pytest

from importall.stdlib_utils import (
    deduce_stdlib_public_interface,
    deprecated_modules,
    deprecated_names,
    from_stdlib,
    import_stdlib_public_names,
    stdlib_public_names,
)


# A workaround to suppress type checker complaints that functools doesn't have the __all__ attribute.
# FIXME add __all__ to functools.pyi in python/typeshed
functools: Any


def test_import_stdlib_public_names() -> None:
    symtab = {name: getattr(functools, name) for name in functools.__all__}
    assert import_stdlib_public_names("functools") == symtab
    assert import_stdlib_public_names("functools", lazy=True) == symtab

    assert "List" not in import_stdlib_public_names("typing")
    assert "List" in import_stdlib_public_names("typing", include_deprecated=True)


def test_deduce_stdlib_public_interface() -> None:
    public_names = deduce_stdlib_public_interface("functools")
    assert public_names == set(functools.__all__)


def test_from_stdlib() -> None:

    for symbol in [True, False, None, pow, int, all, builtins]:
        assert from_stdlib(symbol)

    assert from_stdlib(functools)
    assert from_stdlib(functools.partial)

    assert not from_stdlib(from_stdlib)
    assert not from_stdlib(test_from_stdlib)
    assert not from_stdlib(pytest)


def test_deprecated_modules() -> None:
    assert "distutils.command.bdist_msi" in deprecated_modules()
    assert "distutils.command.bdist_msi" not in deprecated_modules("3.8")


def test_deprecated_names() -> None:
    assert "List" in deprecated_names("typing")
    assert "List" not in deprecated_names("typing", version="3.8")


def test_stdlib_public_names() -> None:
    assert "partial" in stdlib_public_names("functools")
    assert "cache" not in stdlib_public_names("functools", version="3.8")
