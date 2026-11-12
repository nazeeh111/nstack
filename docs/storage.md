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

## Maintenance

1. Measure relevant directories and physical free space separately. Identify
   owners and active references; age or size alone does not make data disposable.
2. Trace both the latest undo and full recovery chain, including journals,
   snapshots, referenced releases, runtime registrations and project links.
3. Preserve projects, unique source/evidence, original backups, vault data and
   recovery dependencies. Leave unavailable or unclassified material alone.
   Prove candidates reproducible or compare duplicate bytes with canonical source.
4. Before any separately authorized removal, revalidate exact candidates and
   dependencies and retain necessary provenance. Record actual actions and compare
   physical free space afterward. Verify active releases and recovery references.

Transaction and chat-history backups are recovery records. Keep large audit
receipts with the owning project and recheck live state before using old inventories.
