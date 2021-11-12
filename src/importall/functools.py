from collections.abc import Callable
from typing import TypeVar


__all__ = ["nulldecorator"]


T = TypeVar("T")


FunctionOrClassType = TypeVar("FunctionOrClassType", bound=Callable)


def nulldecorator(fn_or_cls: FunctionOrClassType) -> FunctionOrClassType:
    """Similar to contextlib.nullcontext, except for decorator"""
    return fn_or_cls
