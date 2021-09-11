import builtins
import inspect
from collections.abc import Callable
from functools import partial, wraps
from typing import TYPE_CHECKING, TypeVar, cast

from lazy_object_proxy import Proxy
from typing_extensions import ParamSpec

from .functools import nulldecorator
from .typing import IdentityDecorator


__all__ = ["profile", "provide_lazy_version", "tk_is_available", "raises"]


P = ParamSpec("P")
R = TypeVar("R")


# The name `profile` will be injected into builtins in runtime by line-profiler.
profile = getattr(builtins, "profile", None) or nulldecorator

if TYPE_CHECKING:
    profile = nulldecorator


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


def raises(etype: type[Exception], error_message: str) -> IdentityDecorator:
    """
    A decorator to make decorated function raise given exception with given error
    message whenever failure happens.

    The `error_message` parameter accepts a format string whose replacement fields are
    substituted for arguments to the decorated function.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:

        signature = inspect.signature(func)

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return func()

            # Catch Exception instead of BaseException, because we don't want to hinder
            # system-exiting exceptions from propagating up.
            except Exception:

                bound_argument = signature.bind(*args, **kwargs)
                bound_argument.apply_defaults()

                formatted_message = error_message.format_map(bound_argument.arguments)

                raise etype(formatted_message) from None

        return wrapper

    return decorator
