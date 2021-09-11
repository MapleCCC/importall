import builtins
import functools
from collections.abc import Callable
from functools import partial, wraps
from typing import TYPE_CHECKING, TypeVar, cast

from lazy_object_proxy import Proxy
from typing_extensions import ParamSpec

from .functools import nulldecorator


__all__ = [
    "singleton_class",
    "profile",
    "hashable",
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
