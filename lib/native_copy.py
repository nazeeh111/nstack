"""Independent copies for generated bundles, using APFS shared blocks when available.

This is not the transaction backup helper. Its contract matches copytree/copy2
for generated release files; native_setup still validates every byte and mode.
"""
import ctypes
import errno
import functools
import os
import shutil
import sys


@functools.lru_cache(maxsize=1)
def _clonefile():
    library = ctypes.CDLL('/usr/lib/libSystem.B.dylib', use_errno=True)
    function = library.clonefile
    function.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
    function.restype = ctypes.c_int
    return function


def _copy_file(source, destination):
    if sys.platform == 'darwin':
        try:
            clone = _clonefile()
        except AttributeError:
            clone = None  # Older hosts can lack the optional native function.
        if clone is not None:
            if clone(os.fsencode(source), os.fsencode(destination), 0) == 0:
                shutil.copystat(source, destination)
                return destination
            error = ctypes.get_errno()
            # clonefile(2) is atomic: an unsupported clone leaves no output.
            # Preserve permission, existing-target and I/O failures as errors.
            if error not in (errno.ENOTSUP, errno.EXDEV, errno.ENOSYS):
                raise OSError(error, os.strerror(error), destination)
    return shutil.copy2(source, destination)


def copy_generated_tree(source, destination):
    """Copy a new generated tree with independent inodes and ordinary traversal."""
    return shutil.copytree(source, destination, copy_function=_copy_file)
