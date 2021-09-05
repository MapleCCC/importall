import builtins
import functools
import json
from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar, cast

from lazy_object_proxy import Proxy as _Proxy

from .functools import nulldecorator
from .typing import JSONLoadsReturnType


__all__ = ["singleton_class", "profile", "jsonc_loads", "hashable", "Proxy"]


R = TypeVar("R")


# A decorator to transform a class into a singleton
singleton_class = functools.cache


# The name `profile` will be injected into builtins in runtime by line-profiler.
profile = getattr(builtins, "profile", None) or nulldecorator

if TYPE_CHECKING:
    profile = nulldecorator


def jsonc_loads(text: str) -> JSONLoadsReturnType:
    """Similar to json.loads(), except also accepts JSON with comments"""

    # TODO use more robust way to clean comments, use syntax parsing
    # TODO recognize more comment formats, Python-style comment, C-style comment, ...
    # TODO recognize multi-line comment

    lines = text.splitlines(keepends=True)
    cleaned = "".join(line for line in lines if not line.lstrip().startswith("//"))
    return json.loads(cleaned)


def hashable(obj: object) -> bool:
    """Check if an object is hashable"""

    try:
        hash(obj)
    except TypeError:
        return False
    else:
        return True


builtins_patched = False


def Proxy(func: Callable[[], R]) -> R:
    """
    Patch `lazy-object-proxy.Proxy`, so that `repr()`, `id()`, and `type()` also are
    blind to proxy-ness.
    """

    global builtins_patched
    if not builtins_patched:
        _id, _repr, _type = id, repr, type
        builtins.id = (
            lambda x: _id(x) if not isinstance(x, _Proxy) else _id(x.__wrapped__)
        )
        builtins.repr = (
            lambda x: _repr(x) if not isinstance(x, _Proxy) else _repr(x.__wrapped__)
        )

        # FIXME
        #
        # class patched_type(_type):
        #     def __new__(cls, *args, **kwargs):
        #         if len(args) == 1 and not kwargs:
        #             x = args[0]
        #             x = x if not isinstance(x, _Proxy) else x.__wrapped__
        #             args = (x,)
        #         return _type(*args, **kwargs)
        #
        # builtins.type = patched_type

        builtins_patched = True

    return cast(R, _Proxy(func))
