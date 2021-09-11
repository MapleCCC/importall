import builtins
import functools
from collections.abc import Callable
from functools import partial, wraps
from typing import TYPE_CHECKING, TypeVar, cast

from lazy_object_proxy import Proxy as _Proxy
from typing_extensions import ParamSpec

from .functools import nulldecorator


__all__ = [
    "singleton_class",
    "profile",
    "hashable",
    "Proxy",
    "provide_lazy_version",
    "tk_is_available",
]


P = ParamSpec("P")
R = TypeVar("R")


# A decorator to transform a class into a singleton
singleton_class = functools.cache


# The name `profile` will be injected into builtins in runtime by line-profiler.
profile = getattr(builtins, "profile", None) or nulldecorator

if TYPE_CHECKING:
    profile = nulldecorator


def hashable(obj: object) -> bool:
    """Check if an object is hashable"""

    try:
        hash(obj)
    except TypeError:
        return False
    else:
        return True


builtins_patched = False


# TODO remove this function because there is no need for patching anymore.
# Use test to ensure no regression before and after removal of this function.
def Proxy(func: Callable[[], R]) -> R:
    """
    Patch `lazy-object-proxy.Proxy`, so that `repr()`, `id()`, and `type()` also are
    blind to proxy-ness.
    """

    global builtins_patched

    if not builtins_patched:

        _id, _repr, _type = id, repr, type

        # FIXME Patching id() is not enough to ensure that `Proxy(x) is x` evaluates to
        # True.
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

    Access `__wrapped__` to retrieve the original function.
    """

    @wraps(func)
    def wrapper(*args, lazy: bool = False, **kwargs) -> R:

        eager = not lazy

        if eager:
            return func(*args, **kwargs)
        else:
            return cast(R, Proxy(partial(func, *args, **kwargs)))

    wrapper.__wrapped__ = func

    return wrapper


def tk_is_available() -> bool:
    """Check if Tk is available"""

    try:
        import tkinter  # type: ignore
    except ModuleNotFoundError:
        return False
    else:
        return True
