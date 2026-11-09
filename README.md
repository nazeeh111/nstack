# nstack

A native-first Codex setup with a reviewed, searchable specialist catalog and
project-scoped activation. Routine edits use the project's existing tools.
Specialist instructions stay outside global skill discovery until needed.

The release registry contains 535 discovery decisions, 242 admitted component
records and 202 exact skill/support paths. Admission is not proof of runtime
acceptance. Read each component's trigger, non-use conditions, rights, patches
and checks before using it. Trials and substitutes fail closed until their
specific gate is implemented and satisfied. Consultation and excluded entries
cannot become standalone installs.

## Install on a Mac

Requirements: Git, Python 3.11 or later, and existing Codex subscription access.
The pinned CLI bootstrap currently supports native Apple Silicon macOS only.
The independently managed desktop app is preserved. No API key, purchase or
provider signup is part of installation. `uv` is needed only for the selected
Python runtime recipes; Node/npm and browser downloads are needed only for the
selected JavaScript recipes. The FFmpeg recipe uses the existing Apple compiler
and make.

From this checkout:

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
python3 install.py install --stage-only --bootstrap-cli
python3 install.py install --bootstrap-cli --retire-personal --run-id cutover
"$HOME/.local/bin/nstack" doctor
```

The last install command retires the complete personal skill collection into
private recovery storage, preserving built-ins. It merges only owned config
keys and preserves unrelated settings and current model/effort choices. It
does not read credential stores, move projects or conversations, manage hosted
account connections, or replace the desktop application. Inventory and back up
any separately managed hooks, profiles, plugins and jobs before retiring them.
An explicit private retirement plan supports snapshotted Codex profiles, hooks,
skill-lock files and already-unloaded Mac LaunchAgents. It rejects changed
targets and leaves other applications and jobs alone.

Private state defaults to `~/Library/Application Support/nstack/`, outside
skill discovery. Immutable code releases, source cache, reviewed builds,
runtime locks, private backups and restart-safe ownership journals live there.
`NSTACK_STATE` can select a separate private deployment for testing. Add
`$HOME/.local/bin` to your normal PATH if it is absent. To replace an existing
CLI entry elsewhere, pass its exact absolute path with `--cli-path`.

## First unfamiliar task

First run an ordinary task with its normal checks. It needs no specialist.
When a task needs one, configure only that project from a trusted Terminal:

```sh
nstack project-init /absolute/path/to/project --trust
nstack search room clap decay
nstack show P318
```

Open a fresh Codex session normally in that project. The installed guidance
directs Codex to search by artifact, operation and failure condition, inspect
the exact decision, and use the bounded project publisher. That publisher has
three operations: activate one selected leaf, deactivate one owned link, and
verify its fixed project shelf. It cannot run arbitrary commands or change
accounts, global settings, or another project's shelf. Read the returned
reviewed `SKILL.md` before doing the specialist work. Activation alone is not
evidence that the specialist was used.

A Terminal owner can perform the same source-backed publication explicitly:

```sh
nstack build P011 skills/obsidian-markdown/SKILL.md
nstack activate /absolute/project /absolute/release/path/from/build
nstack verify /absolute/project
nstack deactivate /absolute/project p011-obsidian-markdown
nstack project-remove /absolute/project
```

Sources are fetched by full Git commit, their blobs verified, and exact selected
leaves patched in staging. The source remains separate from the exposed leaf.
Required local support and notices are retained; unrelated collection entries
are not globally installed. Publisher ownership is private and bound to the
project's path and filesystem identity. A project file cannot forge ownership
to remove another shelf entry. The normal worker must remain unable to write
private source/builds or protected `.agents`/`.codex` paths.

## On-demand routes

`nstack route ID` returns the exact source, prerequisites, activation, check and
retirement sequence. All 198 on-demand components have a route: 46 use reviewed
selected leaves, 93 have isolated runtime recipes (94 operations), and 59 use
native build or official application procedures. Some components also retain
supporting leaves. The 28 trials and seven substitutes remain conditional;
generic publication, workspace creation and runtime commissioning reject them.
Their per-ID target verifiers must be implemented and pass before admission.
The nine consult records never become standalone installs.

Python source recipes build the exact selected source into an isolated wheel
with separate hash-locked build dependencies and runtime dependencies. Go
recipes use a checksummed private toolchain and the exact selected source.
Node workspaces use their native package manager, check packed local dependency
closure, and install only the native target packages into the named project.
No dormant route provisions an account, GPU, model, service or application.
A recipe is available for use; its actual target remains untested until checked.

Native source builds can start with `nstack workspace ID /absolute/project`.
This creates a private editable checkout and output prefix, outside discovery.
Repeat use requires unchanged source and Git bytes. `--fresh` retains an edited
attempt before preparing another. `nstack retire-workspace ID /absolute/project`
retains all bytes, including unexpected files, and removes only active ownership.
Follow the route's explicit working directory, lock procedure and environment.

## Local runtime operations

Examples with concrete commission, invocation, check and removal commands:

| Component | Operation | Scope |
|---|---|---|
| P053 | `cli` | ast-grep 0.51.1 structural search/refactor |
| P061 | `test` | Playwright Test 1.65.0, matched Chromium and Firefox |
| P318 | `rt60` | Exact reviewed pure-Python room-decay estimator; hash-locked environment |
| P230 | `media` | Minimum local-only FFmpeg/ffprobe build from the reviewed source commit |
| P190 | `cli` | Exact-source Gitleaks with private, redacted scanning reports |
| P144 | `python` | Exact-source Optuna in a locked isolated Python environment |
| P198 | `ux` | Selected local UX guidance data and stdlib lookup helper |
| P355 | `posting` | Local posting-text decoder and hidden-instruction guard |

```sh
nstack commission P318 rt60
nstack check P318 rt60
nstack run P318 rt60 -- clap.wav result.json
nstack commission P230 media
nstack check P230 media
nstack run P230 media -- ffprobe -v error -show_streams -of json output.mkv
nstack remove-runtime P230 media
```

Commissioning resolves only the registered operation. It never silently selects
a newer product or enables a whole collection. Existing locks are checked on
repeat use. Removal moves the exact owned environment into recovery storage,
including unexpected local additions, and removes its active receipt. It does
not recursively delete those bytes. Other runtime/platform/provider lanes keep
their prerequisites and target checks explicit in the catalog; a missing
adapter or unmet condition is a blocked operation, not a passing installation.

The original [synthetic clap example](examples/clap/README.md) produces editable
SVG, PDF, PNG and CSV, checks the known decay with an independent stdlib
comparator, and rejects a stale handoff before regeneration. No recording,
private data, model or API is required.

`nstack inventory /absolute/project` reads a fresh native CLI's skill and local
MCP metadata through its supported app-server protocol. `--binary /absolute/codex`
can inspect a separately managed backend. It discards raw configuration and
environment values. It does not establish normal desktop relaunch, hosted plugin
enablement or successful provider access. Hosted optional plugins must be retired
through supported native controls while preserving built-ins and account access.

Add `--plugins` to request fresh native plugin installation/enabled metadata and
marketplace error counts. An error or an unobserved remote catalog cannot prove
a plugin was removed. Installation, enabled state and actual tool use are separate
checks. Keep personal plugin choices in private deployment records; do not copy
account identifiers or preferences into the public registry. An explicitly retained
official plugin can coexist with the on-demand catalog without a duplicate local
skill collection. Its installation grants no new sending, spending or data access.
The native effective-config response is held transiently to extract server names
and local enablement flags. Configuration layers and credential files are not
requested; raw configuration is discarded.

## Correctable knowledge and handoffs

Keep one canonical project record, source attribution and current input hashes.
From inside the owning project:

```sh
nstack knowledge set /absolute/project fixture-level --claim '30 dB' --source evidence.txt
nstack knowledge read /absolute/project fixture-level
nstack knowledge delete /absolute/project fixture-level
```

Retrieval checks current project scope and actual source bytes. A correction
supersedes the prior generation; deletion leaves a tombstone. Commit durable
records through the project's authorized Git workflow. Reject stale derived
results at handoff and regenerate affected artifacts. Native automatic memory
remains separate and can skip externally sourced sessions; do not claim a
canonical-record check proves automatic-memory generation. Retrieval indexes
and memory services are conditional additions, not extra permanent authorities.

## Roll back from Terminal

```sh
"$HOME/Library/Application Support/nstack/rollback.sh"
```

The helper works independently of Codex and follows the recorded release chain
back to the pre-cutover profile. It restores only the recorded changes.
Owned TOML edits are inverted while preserving later unrelated edits. A later
conflicting edit to the same owned setting stops rollback for reconciliation.
New projects, knowledge and conversations are preserved. An explicit job plan
restores definitions in their original unloaded state; the installer never
stops or starts a loaded service. macOS may assign a new `com.apple.provenance`
tag to a copied file; nstack leaves that system tag alone while checking bytes,
ACLs, ownership, flags, modes and other extended attributes.

Keep the private backup after success. Reinstalling the same release/run is
idempotent; changing release code uses a new recorded run so earlier rollback
helpers and originals remain available.

## Redistribution

Original toolkit code is MIT. Third-party terms remain independent; see
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). This repository publishes
portable metadata, original adapters and patch mechanisms. It contains no raw
research ledger, private deployment, account binding, credential, personal
vault, conversation export or proprietary plugin implementation. Restricted
services and assets must use their official access and rights checks.

## Verification and supported scope

Run the portable tests with the command above. `python3 tests/check_recovery.py check --output /absolute/private/capture`
uses a loopback capture receiver and synthetic identities to test lost
acknowledgements, restart and exactly one business effect. It never sends mail.
The registry contract test checks full component/path coverage and permissions;
private deployment receipts and the supplied raw-ledger coverage checker stay
outside this public tree.

The pinned bootstrap supports Apple Silicon macOS. The normal CLI and independent
desktop backend have separate loaders; a backend inventory is not a desktop UI
check. Trial, proprietary, hardware-specific, provider and large model lanes are
conditional on their own rights, platform, resources and output checks. These
sources do not imply that every target runtime has been installed or tested.
