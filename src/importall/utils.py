from __future__ import annotations  # for types imported from _typeshed

import asyncio
import builtins
import pickle
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from functools import wraps
from pickle import PicklingError
from subprocess import CalledProcessError
from typing import TYPE_CHECKING, TypeVar

from recipes.functools import lazy_call
from recipes.inspect import bind_arguments
from typing_extensions import ParamSpec

from .functools import nulldecorator
from .inspect import getcallerframe
from .typing import IdentityDecorator


if TYPE_CHECKING:
    from _typeshed import StrOrBytesPath


__all__ = [
    "profile",
    "provide_lazy_version",
    "raises",
    "unindent_source",
    "run_in_new_interpreter",
    "eval_name",
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
            return lazy_call(func, *args, **kwargs)

    wrapper.__wrapped__ = func

    return wrapper


def raises(etype: type[Exception], error_message: str) -> IdentityDecorator:
    """
    A decorator to make decorated function raise given exception with given error
    message whenever failure happens.

    The `error_message` parameter accepts a format string whose replacement fields are
    substituted for arguments to the decorated function.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return func(*args, **kwargs)

            # Catch Exception instead of BaseException, because we don't want to hinder
            # system-exiting exceptions from propagating up.
            except Exception:
                bound_arguments = bind_arguments(func, *args, **kwargs)
                formatted_message = error_message.format_map(bound_arguments)
                raise etype(formatted_message)

        return wrapper

    return decorator


def unindent_source(text: str) -> str:
    lines = text.splitlines()
    margin = min(len(line) - len(line.lstrip()) for line in lines if line.strip())
    return "\n".join(line[margin:] for line in lines)


async def asyncio_subprocess_check_output(
    args: Sequence[StrOrBytesPath], redirect_stderr_to_stdout: bool = False
) -> bytes:
    """Augment `subprocess.check_output()` with async support"""

    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT if redirect_stderr_to_stdout else None,
    )
    stdout, stderr = await proc.communicate()

    retcode = proc.returncode
    assert retcode is not None

    if retcode != 0:
        raise CalledProcessError(retcode, args, stdout, stderr)

    return stdout


# TODO design some creative approaches to add color highlighting to literal source
# TODO create a subinterpreter within the same process to reduce performance overhead
async def run_in_new_interpreter(
    func: Callable[P, R], /, *args: P.args, **kwargs: P.kwargs
) -> R:
    """
    Run the callable in a new interpreter instance. Return the result of the callable.

    Picklability of the callable and its arguments and its return value are required.

    Raise `RunInNewInterpreterError` on failure.
    """

    try:
        pickled = pickle.dumps((func, args, kwargs))
    except PicklingError:
        raise ValueError(
            "Picklability of the callable and its arguments and its return value are required."
        )

    source = unindent_source(
        f"""
        import os, pickle, sys
        from contextlib import redirect_stderr, redirect_stdout

        func, args, kwargs = pickle.loads({pickled})

        with open(os.devnull, "w") as f:
            with redirect_stdout(f), redirect_stderr(f):
                result = func(*args, **kwargs)

        sys.stdout.buffer.write(pickle.dumps(result))
    """
    )

    command = [sys.executable or "python", "-c", source]

    try:
        # Spawn subprocess with stderr captured, so as to avoid cluttering console output
        pickled_result = await asyncio_subprocess_check_output(
            command, redirect_stderr_to_stdout=True
        )

    except CalledProcessError as exc:
        raise RuntimeError(
            f"Fail to run {func} in new interpreter due to:\n"
            + "\n".join(" " * 4 + line for line in exc.stdout.decode().splitlines())
        )

    return pickle.loads(pickled_result)


def eval_name(
    name: str, globals: dict[str, object] = None, locals: Mapping[str, object] = None, /
) -> object:
    """
    The use of `eval()` on arbitrary string has been discouraged as a dangerous
    practice. `eval_name()` is a safer and specialized alternative to `eval()`. It only
    evaluates expression consisting of a single name.
    """

    if not name.isidentifier():
        raise ValueError(f"Invalid name: {name}")

    # Constraint implemented by the position-only syntax, so as to imitate the
    # built-in `eval()`'s behavior.
    assert not (globals is None and locals is not None)

    if globals is None:
        globals = getcallerframe().f_globals
        locals = getcallerframe().f_locals

    if locals is None:
        locals = globals

    return eval(name, globals, locals)
