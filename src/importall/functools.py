from typing import TypeVar


__all__ = ["nulldecorator"]


T = TypeVar("T")


def nulldecorator(fn: T) -> T:
    """Similar to contextlib.nullcontext, except for decorator"""
    return fn
