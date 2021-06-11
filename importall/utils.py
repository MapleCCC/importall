import builtins
import functools
import json
import sys
from collections import defaultdict
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

import regex


__all__ = [
    "singleton_class",
    "nulldecorator",
    "profile",
    "deprecated_modules",
    "deprecated_names",
]


T = TypeVar("T")


VersionTuple = tuple[int, int]


# A decorator to transform a class into a singleton
singleton_class = functools.cache


def nulldecorator(fn: T) -> T:
    """Similar to contextlib.nullcontext, except for decorator"""
    return fn


# The name `profile` will be injected into builtins in runtime by line-profiler.
profile = getattr(builtins, "profile", None) or nulldecorator

if TYPE_CHECKING:
    profile = nulldecorator


def jsonc_loads(text: str) -> Any:
    """Similar to json.loads(), except also accept JSON with comments"""

    # TODO use more robust way to clean comments, use syntax parsing
    # TODO recognize more comment formats, Python-style comment, C-style comment, ...
    # TODO recognize multi-line comment

    lines = text.splitlines(keepends=True)
    cleaned = "".join(line for line in lines if not line.lstrip().startswith("//"))
    return json.loads(cleaned)


def convert_version_to_tuple(version: str) -> VersionTuple:
    """
    Convert version info from string representation to tuple representation.
    The tuple representation is convenient for direct comparison.
    """

    m = regex.fullmatch(r"(?P<major>\d+)\.(?P<minor>\d+)", version)
    version_tuple = (int(m.group("major")), int(m.group("minor")))
    return version_tuple


def load_deprecated_modules() -> dict[VersionTuple, frozenset[str]]:
    """Load DEPRECATED_MODULES from JSON file"""

    json_file = Path(__file__).parent / "deprecated_modules.json"
    json_text = json_file.read_text(encoding="utf-8")
    json_obj = jsonc_loads(json_text)

    return {
        convert_version_to_tuple(version): frozenset(modules)
        for version, modules in json_obj.items()
    }


def load_deprecated_names() -> dict[VersionTuple, dict[str, frozenset[str]]]:
    """Load DEPRECATED_NAMES from JSON file"""

    json_file = Path(__file__).parent / "deprecated_names.json"
    json_text = json_file.read_text(encoding="utf-8")
    json_obj = jsonc_loads(json_text)

    res = defaultdict(dict)

    for version, modules in json_obj.items():
        for module, names in modules.items():
            res[convert_version_to_tuple(version)][module] = frozenset(names)

    return res


DEPRECATED_MODULES = load_deprecated_modules()

DEPRECATED_NAMES = load_deprecated_names()


@cache
def deprecated_modules(*, version: str = None) -> set[str]:
    """
    Return a set of modules who are deprecated after the given version.

    If no version is given, default to the current version.

    The `version` parameter takes argument of the form `3.6`, `2.7`, etc.
    """

    if version is None:
        version_tuple = sys.version_info[:2]
    else:
        version_tuple = convert_version_to_tuple(version)

    modules: set[str] = set()

    for _version, _modules in DEPRECATED_MODULES.items():
        if version_tuple >= _version:
            modules |= _modules

    return modules


@cache
def deprecated_names(*, version: str = None, module: str = None) -> set[str]:
    """
    Return a set of names who are deprecated after the given version.

    If no version is given, default to the current version.

    The `version` parameter takes argument of the form `3.6`, `2.7`, etc.
    """

    if version is None:
        version_tuple = sys.version_info[:2]
    else:
        version_tuple = convert_version_to_tuple(version)

    names: set[str] = set()

    for _version, _modules in DEPRECATED_NAMES.items():
        if version_tuple < _version:
            continue

        for _module, _names in _modules.items():
            if module is None or module == _module:
                names |= _names

    return names
