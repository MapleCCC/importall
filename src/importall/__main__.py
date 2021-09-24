"""
A script to either launch an importall REPL, within which every available names from
standard libraries are already imported, or run a Python script, with every available
names from standard libraries injected into the script's builtins namespace.

Usage: `python -m importall [-h] [script]`
"""

initial_globals = globals().copy()

import argparse
import builtins
import code
import runpy
import sys

import colorama
from colorama import Fore, Style

from .importall import get_all_symbols, importall


colorama.init()


def highlight(s: str) -> str:
    return Style.BRIGHT + s + Style.RESET_ALL


def bright_green(s: str) -> str:
    return Style.BRIGHT + Fore.GREEN + s + Style.RESET_ALL


def run_script(script: str) -> None:

    importall(builtins.__dict__)
    runpy.run_path(script)


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

    parser = argparse.ArgumentParser(
        prog="python -m importall",
        usage="python -m importall [-h] [script]",
        description="A script to either launch an importall REPL, "
        "within which every available names from standard libraries are already imported, "
        "or run a Python script, "
        "with every available names from standard libraries injected into the script's builtins namespace.",
    )
    parser.add_argument("script", nargs="?", help="A Python script file to run.")
    args = parser.parse_args()

    # If there is a script file as command line argument, run it, otherwise launch an
    # interactive shell.
    if args.script:
        run_script(args.script)
    else:
        run_repl()


if __name__ == "__main__":
    main()
