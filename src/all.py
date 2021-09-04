import builtins
import inspect
import sys
from types import FrameType
from typing import Optional

from importall import importall


def get_importer_frame() -> Optional[FrameType]:
    """Get the frame of the importer who imports the parent module of the caller"""

    stack = inspect.stack()
    index = 0

    try:
        while stack[index].frame.f_globals["__package__"] != "importlib":
            index += 1

        while stack[index].frame.f_globals["__package__"] == "importlib":
            index += 1

        return stack[index].frame

    except IndexError:
        return None


frame = get_importer_frame()
if not frame:
    raise RuntimeError(
        "The intended use of the `all` module is to be imported in the form: `import all`"
    )

importall(frame.f_globals)

# Make sure the name "all" is not shadowed by the imported `all` module
sys.modules["all"] = builtins.all  # type: ignore
