"""
Utility script to generate static data of stdlib public names

# Usage: `python -m importall.generate`
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

from tqdm.asyncio import tqdm_asyncio

from .stdlib_list import IMPORTABLE_STDLIB_MODULES
from .stdlib_utils import deduce_stdlib_public_interface


MODULES_WITH_ZERO_TOP_LEVEL_PUBLIC_NAMES = frozenset(
    {"distutils", "email.mime", "test", "urllib", "wsgiref"}
)

KNOWN_FALSE_POSITIVES = {"_thread": {"exit_thread"}}


async def generate_stdlib_public_names() -> dict[str, list[str]]:

    async def helper(module_name: str) -> list[str]:

        public_names = await deduce_stdlib_public_interface(module_name)

        # Remove false positives
        public_names -= KNOWN_FALSE_POSITIVES.get(module_name, set())

        # Sanity check: a stdlib is unlikely to have no public names
        if module_name not in MODULES_WITH_ZERO_TOP_LEVEL_PUBLIC_NAMES:
            assert public_names, f"{module_name} has zero top level public names"

        return sorted(public_names)

    stdlib_public_names = await tqdm_asyncio.gather(
        # FIXME we should not only use IMPORTABLE_STDLIB_MODULES, because the list should be much more general
        *(helper(module) for module in IMPORTABLE_STDLIB_MODULES),
        desc="Generating static list of stdlib public names",
        # TODO which style is better: "5.42module/s" or "5.42modules/s" ?
        unit="module",
    )

    return dict(zip(IMPORTABLE_STDLIB_MODULES, stdlib_public_names))


def reformat_json_file(file: Path) -> None:
    """Reformat JSON file"""

    prettier_executable = "prettier.cmd" if os.name == "nt" else "prettier"
    options = ["--end-of-line", "auto", "--write"]
    subprocess.check_call([prettier_executable, *options, str(file)])


async def main() -> None:

    ver = ".".join(str(c) for c in sys.version_info[:2])
    file = Path(__file__).with_name("stdlib_public_names") / (ver + ".json")

    stdlib_public_names = await generate_stdlib_public_names()

    json_style = {"indent": 2, "sort_keys": True}

    json_text = json.dumps(stdlib_public_names, **json_style)

    file.write_text(json_text, encoding="utf-8")

    reformat_json_file(file)


if __name__ == "__main__":
    asyncio.run(main())
