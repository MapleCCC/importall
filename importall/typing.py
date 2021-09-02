from collections.abc import MutableMapping
from typing import Any


__all__ = ["SymbolTable"]


SymbolTable = MutableMapping[str, Any]
