import inspect
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
        "The intended use of the `everything` module is to be imported in the form: `import everything`"
    )

importall(frame.f_globals)
