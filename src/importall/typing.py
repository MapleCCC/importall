from collections.abc import MutableMapping
from typing import Union


__all__ = ["SymbolTable", "JSONLoadsReturnType"]


SymbolTable = MutableMapping[str, object]


JSONLoadsReturnType = Union[None, bool, float, str, list, dict]
