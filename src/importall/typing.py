from collections.abc import Callable, MutableMapping
from typing import TypeVar, Union

from typing_extensions import ParamSpec


__all__ = ["SymbolTable", "JSONLoadsReturnType", "IdentityDecorator"]


P = ParamSpec("P")
R = TypeVar("R")


SymbolTable = MutableMapping[str, object]


JSONLoadsReturnType = Union[None, bool, float, str, list, dict]


class IdentityDecorator:
    def __call__(self, __func: Callable[P, R]) -> Callable[P, R]:
        ...
