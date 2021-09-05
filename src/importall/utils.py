import builtins
import functools
import json
from typing import TYPE_CHECKING

from .functools import nulldecorator
from .typing import JSONLoadsReturnType


__all__ = ["singleton_class", "profile", "jsonc_loads", "hashable"]


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
