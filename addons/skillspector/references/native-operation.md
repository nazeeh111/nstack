# Native offline operation

This supplement changes execution only. Keep both upstream review lines: genuine scanner findings and independent source-aware judgment. Use it for agent skills and their bundled tool/plugin code. General application code audits belong with the relevant security specialist.

Locate this skill's `runtime_recipe` in nstack's current native-tools index, or resolve `recipes/skillspector.py` from the installed nstack code. The recipe has explicit `install`, `verify`, `help`, and `run` commands. Runtime acquisition is on demand and needs the user's existing installation authority. It acquires only the pinned official source and frozen Python dependencies in private nstack state. It does not install packages globally or enable a service.

```sh
python3 <recipe> install
python3 <recipe> verify
python3 <recipe> run --target <approved-local-component> --outdir <fresh-private-output>
```

Repeat `--target` for an explicit batch. The recipe verifies source/runtime bytes once per batch, resolves each target root, copies a materialized snapshot without executing target code, records input hashes and skipped sensitive-file names, and invokes the actual upstream CLI `scan --no-llm --format json`. Nested links outside the selected component are refused. Reports, component inventories, snapshot hashes, scanner logs, network-denial proof and a run receipt stay with the task. Do not supply account directories, credentials, private conversations, memory or vault contents. A public plugin/source snapshot is appropriate; an authenticated host's entire config folder is not.

On macOS, scanning requires a working native `sandbox-exec` boundary. The recipe verifies network connections fail with a permission error under the exact scan profile before starting upstream code. It uses a fresh allowlisted environment, isolated HOME, disables tracing, and sets `SKILLSPECTOR_OSV_TIMEOUT=0`. A missing or denied sandbox stops the operation; do not substitute proxy variables or remove the policy. Report that the scan could not run and continue only with the clearly labelled manual source-review fallback.

The recipe never selects an LLM provider or calls a semantic model. Live OSV vulnerability lookup and scanner semantic coverage are unavailable in this lane; dependency artifact download and transitive fetching are not requested. Keep every report's actual completeness/limit information. A successful static invocation with findings is a completed scan requiring adjudication, not an approval. Preserve partial/error reports and source changes as failures; do not turn a low score into a claim of full security.

The registered upstream `codex_cli` provider is intentionally disabled because its sandbox permits host file reads. Preserve that restriction. Hosted APIs, OpenCode semantic child sessions and local model downloads are separate optional operations requiring applicable authorization and verified safety/cost boundaries. Installation grants no such authority. The optional upstream OpenCode/Pi extensions and MCP server are unnecessary for this shared skill.

For corruption checks, compare the recorded installed bytes with trusted pinned source and authorized adaptations separately. Security detections do not establish byte integrity; matching bytes do not establish safety. Scan each identified component rather than assuming a recursive scan covers arbitrary tools, dependencies, opaque binaries or every plugin. Inspect HIGH/CRITICAL findings and sensitive MEDIUM findings in source. Keep APPROVE/CAUTION/REJECT with the upstream rubric and state skipped, opaque or incomplete coverage.
