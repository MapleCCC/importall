"""
This module implements the magic import feature. Import this module will cause every
avaiable names from standard libraries to be imported to the importer's namespace.

Usage: `import everything`
"""


import builtins
import inspect
import sys
from types import FrameType, ModuleType
from typing import cast

from importall import importall


class GetImporterFrameError(Exception):
    "An exception to signal that get_importer_frame() fails"


def get_importer_frame() -> FrameType:
    """Get the frame of the importer who imports the current module"""

    stack = inspect.stack()
    index = 0

    try:
        while stack[index].frame.f_globals["__package__"] != "importlib":
            index += 1

        while stack[index].frame.f_globals["__package__"] == "importlib":
            index += 1

        return stack[index].frame

    except IndexError:
        raise GetImporterFrameError from None


try:
    frame = get_importer_frame()
except GetImporterFrameError:
    raise RuntimeError(
        "The intended use of the `all` module is to be imported in the form: `import all`"
    )

importall(frame.f_globals)

# Make sure the name "all" is not shadowed by the imported `all` module
sys.modules["all"] = cast(ModuleType, builtins.all)
