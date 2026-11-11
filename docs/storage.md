# Generated release storage

Native bundle preparation uses independent copy-on-write files on macOS when
`clonefile(2)` is available. Files initially share data blocks; writing either
copy leaves the other unchanged. Other hosts, unsupported volumes and copies
across filesystems use ordinary `copy2` copies. Release byte/mode verification
and the sealed manifest remain unchanged. Transaction backups retain their
existing metadata-preserving copy implementation.

This reduces future generated-copy growth on supported filesystems. It does not
prune previous releases or change active installations. `du` can count shared
blocks more than once, so directory totals do not establish physical savings.

Implementation follows the local Apple `clonefile(2)` and `cp(1)` manuals:
clone regular files during ordinary directory traversal, fall back for unsupported
cloning, and propagate permission and I/O errors.
