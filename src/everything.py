"""
This module implements the magic import feature. Import this module will cause every
avaiable names from standard libraries to be imported to the importer's namespace.

Usage: `import everything`
"""


import sys
from types import FrameType

from importall import importall


class GetImporterFrameError(Exception):
    "An exception to signal that get_importer_frame() fails"


def get_importer_frame() -> FrameType:
    """
    Get the frame of the importer who imports the current module.

    Raise GetImporterFrameError if such frame can't be found.
    """

    frame = sys._getframe()

    while frame and frame.f_globals["__package__"] != "importlib":
        frame = frame.f_back

    while frame and frame.f_globals["__package__"] == "importlib":
        frame = frame.f_back

    if not frame:
        raise GetImporterFrameError

    return frame


try:
    frame = get_importer_frame()
except GetImporterFrameError:
    raise RuntimeError(
        "The intended use of the `everything` module is to be imported in the form: `import everything`"
    )

importall(frame.f_globals)
