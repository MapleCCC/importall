import builtins
import os

from stdlib_list import stdlib_list


__all__ = ["BUILTINS_NAMES", "IMPORTABLE_MODULES"]


BUILTINS_NAMES = frozenset(dir(builtins)) - {
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

curr_ver_stdlib_list = set(stdlib_list())

# Patch stdlib-list: add missing standard libraries
# TODO open an issue in https://github.com/jackmaney/python-stdlib-list/
# FIXME should we consider these standard libraries ? What's the authority definition of "standard libraries" in Python?
curr_ver_stdlib_list |= {"msilib.schema", "msilib.sequence", "msilib.text"}

# Patch stdlib-list: some modules should not be considered public standard libraries
# TODO open an issue in https://github.com/jackmaney/python-stdlib-list/
curr_ver_stdlib_list -= {"multiprocessing.context", "_collections_abc", "unittest.loader"}

IMPORTABLE_MODULES = frozenset(curr_ver_stdlib_list)

# Don't import some special standard library modules
#
# The `__main__` module is meta.
# Names from the `__main__` module should not be considered standard library utilities.
#
# No need to import names from `builtins`, since they are always available anyway.
#
# Importing `__phello__.foo` module will cause "Hello world!" to be printed
# on the console, and we don't yet know why.
#
# The `antigravity` and `this` modules are easter eggs.
IMPORTABLE_MODULES -= {"__main__", "__phello__.foo", "antigravity", "builtins", "this"}

# lib2to3 package contains Python 2 code, which is unrunnable under Python 3.
IMPORTABLE_MODULES -= {mod for mod in IMPORTABLE_MODULES if mod.startswith("lib2to3")}

if os.name == "nt":
    # On Windows OS, UNIX-specific modules are ignored.
    IMPORTABLE_MODULES -= {
        "multiprocessing.popen_fork",
        "multiprocessing.popen_forkserver",
        "multiprocessing.popen_spawn_posix",
    }
