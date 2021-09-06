import builtins
import functools
import json
from collections.abc import Callable
from functools import partial, wraps
from typing import TYPE_CHECKING, TypeVar, cast

from lazy_object_proxy import Proxy as _Proxy
from typing_extensions import ParamSpec

from .functools import nulldecorator
from .typing import JSONLoadsReturnType


__all__ = [
    "singleton_class",
    "profile",
    "jsonc_loads",
    "hashable",
    "Proxy",
    "provide_lazy_version",
]


P = ParamSpec("P")
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


# FIXME we want to add type annotation to `provide_lazy_version()` to indicate to type
# checkers that an optional keyword parameter named `lazy` is injected to the signature
# of decorated function.
#
# Yet there is currently no officially-supported way to properly type annotate a
# decorator that add a keyword argument to the wrapped function. The `Concatenating
# Keyword Parameters` section of PEP-612 summaries the status quo:
# https://www.python.org/dev/peps/pep-0612/#concatenating-keyword-parameters
#
# For now, we fallback to the `no type check` option, until the Python dev team, in the
# future, roll out more sophisticated type system constructs, so that expressing more
# powerful type concepts is possible.


def provide_lazy_version(func: Callable[P, R]) -> Callable[..., R]:
    """
    A decorator to let the decorated function provide an option to return a
    lazily-evaluated result.

    The return result, if lazy evaluation mode is on, looks like normal result, except
    that the actual function execution is delazyed until the return result is actually
    used by external code.

    Inject an optional keyword argument named `lazy` to the signature of the decorated
    function. Setting the `lazy` parameter to `True` enables lazy evaluation mode.
    """

    @wraps(func)
    def wrapper(*args, lazy: bool = False, **kwargs) -> R:

        eager = not lazy

        if eager:
            return func(*args, **kwargs)
        else:
            return cast(R, Proxy(partial(func, *args, **kwargs)))

    return wrapper
