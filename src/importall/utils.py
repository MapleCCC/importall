import builtins
import inspect
import pickle
import subprocess
import sys
from collections.abc import Callable, Mapping
from functools import partial, wraps
from typing import TYPE_CHECKING, TypeVar, cast

from lazy_object_proxy import Proxy
from typing_extensions import ParamSpec

from .functools import nulldecorator
from .typing import IdentityDecorator


__all__ = [
    "profile",
    "provide_lazy_version",
    "tk_is_available",
    "raises",
    "run_in_new_interpreter",
]


P = ParamSpec("P")
R = TypeVar("R")


# The name `profile` will be injected into builtins at runtime by line-profiler.
profile = getattr(builtins, "profile", None) or nulldecorator

if TYPE_CHECKING:
    profile = nulldecorator


# FIXME we want to add type annotation to `provide_lazy_version()` to indicate to type
# checkers that an optional keyword parameter named `lazy` is injected to the signature
# of decorated function.
#
# Yet there is currently no officially-supported way to properly type annotate a
# decorator that add a keyword argument to the wrapped function. The `Concatenating
# Keyword Parameters` section of PEP-612 summarizes the status quo:
# https://www.python.org/dev/peps/pep-0612/#concatenating-keyword-parameters
#
# For now, we fallback to the `no type check` option, until the Python dev team, in the
# future, roll out more sophisticated type system constructs, so that expressing more
# powerful type concepts is made possible.


def provide_lazy_version(func: Callable[P, R]) -> Callable[..., R]:
    """
    A decorator to make the decorated function provide an option to return a
    lazily-evaluated result.

    The return result, if lazy evaluation mode is on, looks like normal result, except
    that the actual function execution is delazyed until the return result is actually
    used by external code.

    Inject an optional keyword argument named `lazy` to the signature of the decorated
    function. Setting the `lazy` parameter to `True` enables lazy evaluation mode.

    The decorated function is instrumented with a `__wrapped__` attribute to access the
    original vanilla function.

    It's recommended to decorate pure functions only.
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
                return func(*args, **kwargs)

            # Catch Exception instead of BaseException, because we don't want to hinder
            # system-exiting exceptions from propagating up.
            except Exception:

                bound_argument = signature.bind(*args, **kwargs)
                bound_argument.apply_defaults()

                formatted_message = error_message.format_map(bound_argument.arguments)

                raise etype(formatted_message)

        return wrapper

    return decorator


def unindent_source(text: str) -> str:
    lines = text.splitlines()
    margin = min(len(line) - len(line.lstrip()) for line in lines if line.strip())
    return "\n".join(line[margin:] for line in lines)


class RunInNewProcessError(RuntimeError):
    """An exception to represent that `run_in_new_interpreter()` fails"""


# TODO async, twisted, tornado
# TODO design some creative approaches to add color highlighting to literal source
# TODO better error report
# TODO create a subinterpreter within the same process to reduce performance overhead
@raises(RunInNewProcessError, "fail to run {func} in new process")
def run_in_new_interpreter(
    func: Callable[P, R], /, *args: P.args, **kwargs: P.kwargs
) -> R:
    """
    Run the callable in a new interpreter instance. Return the result of the callable.

    Picklability of the callable and its arguments and its return value are required.

    Raise RunInNewInterpreterError on failure.
    """

    pickled_func = pickle.dumps(func).hex()
    pickled_args = pickle.dumps(args).hex()
    pickled_kwargs = pickle.dumps(kwargs).hex()

    source = unindent_source(
        f"""
        import os
        import pickle
        import sys
        from contextlib import redirect_stdout

        func = pickle.loads(bytes.fromhex('{pickled_func}'))
        args = pickle.loads(bytes.fromhex('{pickled_args}'))
        kwargs = pickle.loads(bytes.fromhex('{pickled_kwargs}'))

        with open(os.devnull, "w") as f:
            with redirect_stdout(f):
                result = func(*args, **kwargs)

        sys.stdout.buffer.write(pickle.dumps(result))
    """
    )

    command = [sys.executable or "python", "-c", source]

    # Spawn subprocess with stderr captured, so as to avoid cluttering console output
    return pickle.loads(subprocess.check_output(command, stderr=subprocess.STDOUT))
