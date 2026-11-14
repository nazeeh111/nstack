# Craft Anything

Craft Anything investigates shipped software: executables, compiled libraries, app packages and recorded artifacts. Its evidence-first method helps when source browsing cannot answer a question about the actual delivered program. Ordinary source work, website building and UI polish keep their existing routes.

The optional `--craft-anything` native skill retains the complete upstream method and recovery guide, both licenses and supporting source records. Its active entry changes only discovery wording and adds the separately labeled native binding. It does not install global MCP tools, run upstream setup, change provider settings or start another coding harness.

## Source and rights

Selected release **0.6.1**, source revision `48a9c5a60ff83ff620f98661339be6281a7debc6`, from [storytold/craft-anything](https://github.com/storytold/craft-anything/tree/48a9c5a60ff83ff620f98661339be6281a7debc6). All 1,046 files in the acquired source archive were compared with their official Git blob identities with no mismatch during this review. The selected original skill and its recovery support are retained unchanged; `PORT.patch` records the active entry delta. `SOURCE.json` records exact retained-file hashes.

Upstream code and method are MIT OR Apache-2.0. Third-party dependencies/fonts and trademarks retain their own terms and notices. The runtime is acquired directly from the official release, not redistributed inside nstack. Its official artifact digest, package-file manifest and signing identity are fixed by the recipe. This is official-release identity evidence, not a reproducible source-to-binary build attestation or a security audit of every dependency.

## Static CLI route

The recipe currently supports Apple Silicon macOS using its existing native code assessment and `sandbox-exec`. It downloads the exact official notarized **intact application package**, privately under nstack's durable runtime state. It does not launch the GUI, touch `/Applications` or add a global CLI link. No Rust installation/build, separate browser, model, provider, account or API key is needed for its admitted static tools. The intact package occupies about 266 MB; the temporary DMG download is disposable after native validation/copying. Heavy external analysis engines stay absent.

```sh
python3 recipes/craft_anything.py install
python3 recipes/craft_anything.py verify
python3 recipes/craft_anything.py check
python3 recipes/craft_anything.py inspect \
  --source /absolute/authorized/program \
  --outdir /absolute/private/task/craft-evidence
python3 recipes/craft_anything.py inspect \
  --source /absolute/authorized/program \
  --outdir /absolute/private/task/craft-evidence \
  --tool native-strings-find --params '{"pattern":"specific text"}'
```

Use actual discovered recipe paths from `SOURCE.json`/the installation-local runtime index when running outside the checkout. The source is one unlinked regular file at most 128 MiB. Output must be new or owned by this exact source hash/revision. Changed inputs and foreign output are preserved and refused. Existing runtimes are verified, not overwritten; unrelated prior edits require reconciliation.

Each inspection uses a fresh empty HOME/config and empty PATH, omits account/provider/proxy variables, denies network in the OS, confines writes to the chosen output, and denies personal-home content reads except the selected file, owned runtime/output and Python guard interpreter. Normal operating-system/loader reads remain available, following the established Graphify runtime boundary. The same OS profile must deny a synthetic out-of-scope file read and network connection before the target is opened. System metadata/loader access remains; this is not a universal host isolation claim. Explicit per-run Deep mode permits reading the chosen artifact's bytes without changing global settings. The target is never executed.

Only a bounded set of built-in static commands is admitted: triage, functions, sections, strings, call relationships, native disassembly/pseudocode, Mach-O/slices, Wasm and import/export/layout views. See the actual `inspect --help`. Evidence, native CLI outputs, guard checks and per-call receipts stay under the task output, with the upstream `.cany` investigation ledger alongside them. Preserve evidence IDs, source hashes, coverage limits and the observed/derived/inferred distinction in conclusions.

## Native assessment and limits

The standalone CLI ZIP was checksum/signature-valid but rejected by macOS `spctl --assess --type execute`: **“the code is valid but does not seem to be an app.”** It was never executed. The separate official DMG passed native disk-image assessment and stapled-ticket validation; its intact app passed deep/strict signature verification and application execution assessment as **Notarized Developer ID**, signer Learning Machines LLC, team `DJ6XS33FX8`. The recipe preserves and rechecks this package chain. It does not remove quarantine, relax Gatekeeper, ignore a refusal or use the rejected distribution as a fallback.

Craft Anything is early alpha. A tiny synthetic Mach-O fixture checks only version/help, triage, a known function/string, an absent-string control, input preservation and OS containment. Runtime acceptance is recorded in the local `CHECK.json`; skill/source installation alone is not a passing runtime check. A parser result does not establish actual program behavior, safety of all possible inputs, completeness of decompilation or all-format/tool coverage.

The broader upstream methods remain available for later explicitly scoped commissioning. Rebuilds launch a coding harness; the upstream Codex adapter has not established a real-account rebuild here. Global MCP setup can add a preapproval for `rebuild_start`. Browser/runtime/device operations, upstream doctor/setup/auth checks, credential helpers, remote plugins, generated assets and billed providers are outside this static route. Keep current host controls and obtain any genuinely missing scope before those effects. Do not infer them from installing this skill.
