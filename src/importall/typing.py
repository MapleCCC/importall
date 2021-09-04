from collections.abc import MutableMapping
from typing import Any, Union


__all__ = ["SymbolTable", "JSONLoadsReturnType"]


SymbolTable = MutableMapping[str, Any]


JSONLoadsReturnType = Union[None, bool, float, str, list, dict]
