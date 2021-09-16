"""
Utility script to generate static data of stdlib public names

# Usage: `python -m importall.generate`
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from tqdm import tqdm

from .stdlib_list import IMPORTABLE_STDLIB_MODULES
from .stdlib_utils import DeducePublicInterfaceError, deduce_stdlib_public_interface


MODULES_WITH_ZERO_TOP_LEVEL_PUBLIC_NAMES = frozenset(
    {"distutils", "email.mime", "test", "urllib", "wsgiref"}
)

KNOWN_FALSE_POSITIVES = {"_thread": {"exit_thread"}}


def generate_stdlib_public_names() -> dict[str, list[str]]:

    stdlib_public_names: dict[str, list[str]] = {}

    for module_name in tqdm(
        # FIXME we should not only use IMPORTABLE_STDLIB_MODULES, because the list should be much more general
        IMPORTABLE_STDLIB_MODULES,
        desc="Generating static list of stdlib public names",
        # TODO which style is better: "5.42module/s" or "5.42modules/s" ?
        unit="module",
    ):

        try:
            public_names = deduce_stdlib_public_interface(module_name)
        except DeducePublicInterfaceError:
            print(
                f"Failed to generate public interface of library {module_name}",
                file=sys.stderr,
            )
            raise

        # Remove false positives
        public_names -= KNOWN_FALSE_POSITIVES.get(module_name, set())

        # Sanity check: a stdlib is unlikely to have no public names
        if module_name not in MODULES_WITH_ZERO_TOP_LEVEL_PUBLIC_NAMES:
            assert public_names, f"{module_name} has zero top level public names"

        stdlib_public_names[module_name] = sorted(public_names)

    return stdlib_public_names


def reformat_json_file(file: Path) -> None:
    prettier_executable = "prettier.cmd" if os.name == "nt" else "prettier"
    options = ["--end-of-line", "auto", "--write"]
    subprocess.check_call([prettier_executable, *options, str(file)])


def main() -> None:

    ver = ".".join(str(c) for c in sys.version_info[:2])
    file = Path(__file__).with_name("stdlib_public_names") / (ver + ".json")

    stdlib_public_names = generate_stdlib_public_names()

    json_style = {"indent": 2, "sort_keys": True}

    json_text = json.dumps(stdlib_public_names, **json_style)

    file.write_text(json_text, encoding="utf-8")

    reformat_json_file(file)


if __name__ == "__main__":
    main()
