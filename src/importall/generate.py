""" Utility script to generate static data of stdlib public names """

# Usage: `python -m importall.generate`

import json
import subprocess
import sys
from pathlib import Path

from tqdm import tqdm

from .stdlib_list import IMPORTABLE_STDLIB_MODULES
from .stdlib_utils import deduce_stdlib_public_interface


MODULES_WITH_ZERO_TOP_LEVEL_PUBLIC_NAMES = frozenset(
    {"distutils", "email.mime", "test", "urllib", "wsgiref"}
)


def main() -> None:

    ver = ".".join(str(c) for c in sys.version_info[:2])
    file = Path(__file__).with_name("stdlib_public_names") / (ver + ".json")

    data: dict[str, list[str]] = {}

    # FIXME we should not only use IMPORTABLE_STDLIB_MODULES, because the list should be much more general
    for module_name in tqdm(
        IMPORTABLE_STDLIB_MODULES,
        desc="Generating static list of stdlib public names",
        # TODO which style is better: "5.42module/s" or "5.42modules/s" ?
        unit="module",
    ):

        try:
            public_names = deduce_stdlib_public_interface(module_name)
        except (ImportError, ModuleNotFoundError):
            print(
                f"Failed to generate public interface of library {module_name}",
                file=sys.stderr,
            )
            raise

        # Sanity check: a stdlib is unlikely to have no public names
        if module_name not in MODULES_WITH_ZERO_TOP_LEVEL_PUBLIC_NAMES:
            assert public_names, f"{module_name} has zero top level public names"

        data[module_name] = sorted(public_names)

    file.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    # FIXME without `shell=True` this call fails, why?
    # The use of `shell=True` is discouraged, so we should find solution ASAP.
    subprocess.check_call(
        ["prettier", "--end-of-line", "auto", "--write", str(file)], shell=True
    )


if __name__ == "__main__":
    main()
