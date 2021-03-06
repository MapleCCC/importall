import sys
from types import FrameType


__all__ = ["getcallerframe", "is_called_at_module_level"]


def getcallerframe() -> FrameType:
    """Return the frame object of the stack frame of the caller of the current function"""

    # Use `sys._getframe()` instead of `inspect.stack().frame`. Profiling shows that
    # `inspect.stack()` is super expensive, due to internal I/O calls.

    try:
        return sys._getframe(2)
    except ValueError:
        raise RuntimeError(
            "getcallerframe() expects to be called in a function"
        ) from None


def is_called_at_module_level() -> bool:
    """
    Check if the current function is being called at the module level.

    Raise `RuntimeError` if `is_called_at_module_level()` is not called in a function.
    """

    if not (frame := getcallerframe().f_back):
        raise RuntimeError(
            "is_called_at_module_level() expects to be called in a function"
        )

    # There is currently no reliable and officially-provided way to determine whether a
    # function is called from the module level or not.
    #
    # Therefore we use a try-best-effort heuristic approach here.
    #
    # This check could emit false positive in the case of some advanced dynamic-reflection
    # inspection tricks, like `func.__code__ = func.__code__.replace(co_name="<module>")`.
    #
    # However such case is so unlikely and rare that we should not be concerned.
    #
    # We are good with the current approach as it works for most cases.

    return frame.f_code.co_name == "<module>"
