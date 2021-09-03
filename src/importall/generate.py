""" Utility script to generate static data of stdlib public names """

# Usage: `python -m importall.generate`

import json
import subprocess
import sys
from pathlib import Path

from .constants import IMPORTABLE_MODULES
from .importlib import deduce_public_interface


def main() -> None:

    ver = ".".join(str(c) for c in sys.version_info[:2])
    file = Path(__file__).with_name("stdlib_public_names") / (ver + ".json")

    # FIXME we should not only use IMPORTABLE_MODULES, because the list should be much more general
    data = {}
    for module_name in IMPORTABLE_MODULES:
        public_names = deduce_public_interface(module_name)
        data[module_name] = sorted(public_names)

    file.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    # FIXME without `shell=True` this call fails, why?
    # The use of `shell=True` is discouraged, so we should find solution ASAP.
    subprocess.check_call(["prettier", "--write", str(file)], shell=True)


if __name__ == "__main__":
    main()
