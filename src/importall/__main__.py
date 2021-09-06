"""
Script to launch an importall REPL, within which every available names from standard
libraries are already imported.

Usage: `python -m importall`
"""

initial_globals = globals().copy()

import code
import sys

import colorama
from colorama import Fore, Style

from .importall import get_all_symbols


colorama.init()


def highlight(s: str) -> str:
    return Style.BRIGHT + s + Style.RESET_ALL


def bright_green(s: str) -> str:
    return Style.BRIGHT + Fore.GREEN + s + Style.RESET_ALL


def main() -> None:

    prompt = getattr(sys, "ps1", ">>> ")

    banner = (
        f"importall REPL {sys.version} on {sys.platform}\n"
        + highlight(
            "Every available names from standard libraries are already imported. "
            "Use them directly instead of unnecessarily importing them again.\n"
        )
        + 'Type "help", "copyright", "credits" or "license" for more information.\n'
        + prompt
        + bright_green("import everything!🚀✨")
    )

    local = initial_globals | get_all_symbols()

    exitmsg = "exiting importall REPL..."

    code.interact(banner=banner, local=local, exitmsg=exitmsg)


if __name__ == "__main__":
    main()
