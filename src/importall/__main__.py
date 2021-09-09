"""
A script to either launch an importall REPL, within which every available names from
standard libraries are already imported, or run a Python script, with every available
names from standard libraries injected into the script's namespace.

Usage: `python -m importall [script]`
"""

initial_globals = globals().copy()

import builtins
import code
import sys
from pathlib import Path

import colorama
from colorama import Fore, Style

from .importall import get_all_symbols


colorama.init()


def highlight(s: str) -> str:
    return Style.BRIGHT + s + Style.RESET_ALL


def bright_green(s: str) -> str:
    return Style.BRIGHT + Fore.GREEN + s + Style.RESET_ALL


def run_script(script_path: str) -> None:

    script = Path(script_path)

    text = script.read_text(encoding="utf-8")

    inject_builtins = builtins.__dict__ | get_all_symbols()
    inject_globals = initial_globals | {"__builtins__": inject_builtins}

    exec(compile(text, script, "exec"), inject_globals)


def run_repl() -> None:

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

    exitmsg = "exiting importall REPL..."

    inject_globals = initial_globals | get_all_symbols()

    code.interact(banner=banner, local=inject_globals, exitmsg=exitmsg)


def main() -> None:

    assert len(sys.argv[1:]) <= 1, "at most one argument is accepted"

    # If there is a script file as command line argument, run it, otherwise launch an
    # interactive shell.
    if sys.argv[1:]:
        run_script(sys.argv[1])
    else:
        run_repl()


if __name__ == "__main__":
    main()
