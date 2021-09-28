import builtins
import os

from recipes.sys import tk_is_available
from stdlib_list import stdlib_list


__all__ = [
    "BUILTINS_NAMES",
    "STDLIB_MODULES",
    "UNIX_ONLY_STDLIB_MODULES",
    "IMPORTABLE_STDLIB_MODULES",
]


BUILTINS_NAMES = frozenset(dir(builtins)) - {
    "__build_class__",
    "__doc__",
    "__loader__",
    "__name__",
    "__package__",
    "__spec__",
}


# We use the lists maintained by the `stdlib-list` library instead of that by the `isort`
# library or that of `sys.stdlib_module_names`, for they don't include sub-packages and
# sub-modules, such as `concurrent.futures`.
#
# One can compare the two lists:
#
# 1. List maintained by the `isort` library:
# https://github.com/PyCQA/isort/blob/main/isort/stdlibs/py39.py
#
# 2. List maintained by the `stdlib-list` library:
# https://github.com/jackmaney/python-stdlib-list/blob/master/stdlib_list/lists/3.9.txt

STDLIB_MODULES = frozenset(stdlib_list())

# Patch stdlib-list: add missing standard libraries
# TODO open an issue in https://github.com/jackmaney/python-stdlib-list/
# FIXME should we consider these standard libraries ? What's the authority definition of "standard libraries" in Python?
STDLIB_MODULES |= {"msilib.schema", "msilib.sequence", "msilib.text"}

# Patch stdlib-list: some modules should not be considered public standard libraries
# TODO open an issue in https://github.com/jackmaney/python-stdlib-list/
#
# Names from the `__main__` module should not be considered standard library utilities.
#
# TODO what's `__phello__.foo` module for anyway ??
# Importing `__phello__.foo` module will cause "Hello world!" to be printed
# on the console, and we don't yet know why.
#
# The `antigravity` and `this` modules are easter eggs.
STDLIB_MODULES -= {"__main__", "__phello__.foo", "antigravity", "this"}

# The `test` package is for Python dev internal use, and should not be considered public
# standard library.
STDLIB_MODULES -= {mod for mod in STDLIB_MODULES if mod.split(".")[0] == "test"}


UNIX_ONLY_STDLIB_MODULES = frozenset(
    {
        "crypt",
        "curses",
        "curses.ascii",
        "curses.panel",
        "curses.textpad",
        "dbm.ndbm",
        "dbm.gnu",
        "fcntl",
        "grp",
        "readline",
        "multiprocessing.popen_fork",
        "multiprocessing.popen_forkserver",
        "multiprocessing.popen_spawn_posix",
        "nis",
        "ossaudiodev",
        "posix",
        "pty",
        "pwd",
        "resource",
        "spwd",
        "syslog",
        "termios",
        "tty",
    }
)


IMPORTABLE_STDLIB_MODULES = STDLIB_MODULES.copy()

# Despite its show-up in docs, `distutils.command.bdist_packager` is actually
# unimportable at runtime.
IMPORTABLE_STDLIB_MODULES -= {"distutils.command.bdist_packager"}

# lib2to3 package contains Python 2 code, which is unrunnable under Python 3.
IMPORTABLE_STDLIB_MODULES -= {
    mod for mod in IMPORTABLE_STDLIB_MODULES if mod.split(".")[0] == "lib2to3"
}

# On Windows OS or JVM, UNIX-specific modules are ignored.
if os.name != "posix":
    IMPORTABLE_STDLIB_MODULES -= UNIX_ONLY_STDLIB_MODULES

# Some modules depend on availability of Tk
if not tk_is_available():
    IMPORTABLE_STDLIB_MODULES -= {
        mod
        for mod in IMPORTABLE_STDLIB_MODULES
        if mod.split(".")[0] in {"tkinter", "turtle", "turtledemo"}
    }
