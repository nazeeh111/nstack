# Graphify: conditional local code graph

Graphify can map an explicitly chosen code directory and answer repeated structural questions through a persistent graph. This integration admits only its local code-only CLI. It does not register an assistant skill, replace targeted search/Serena, or create a memory service.

The pinned upstream is [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify/tree/35d1d2038b9e9d470f117bf8f2473d415b5f5358), version **0.9.106**, revision `35d1d2038b9e9d470f117bf8f2473d415b5f5358`. Upstream package name is `graphifyy`; executable/module name is `graphify`. Apache-2.0 and older MIT notices are retained separately from nstack's license.

## Use

The recipe requires Apple Silicon macOS, existing `uv`, existing CPython3.12, and macOS `sandbox-exec`. It never downloads Python or modifies system Python. Preparation is explicit and installs an isolated environment under the private nstack state directory. There is no automatic preparation or upgrade when running a task.

From the nstack checkout, first prepare once using actual discovered executable paths:

```sh
python3 recipes/graphify.py prepare --python /absolute/existing/python3.12 --uv /absolute/existing/uv
python3 recipes/graphify.py verify
```

Then use one explicitly approved project directory and a separate new private output directory:

```sh
python3 recipes/graphify.py extract --source /absolute/project/src --outdir /absolute/private/task-graph
python3 recipes/graphify.py query --source /absolute/project/src --outdir /absolute/private/task-graph "normalize"
python3 recipes/graphify.py path --source /absolute/project/src --outdir /absolute/private/task-graph "app.py::run()" "normalize()"
python3 recipes/graphify.py explain --source /absolute/project/src --outdir /absolute/private/task-graph "normalize()"
```

Repeat `extract` with the same source/output pair for incremental updates. Ambiguous symbols require `path::symbol` or the graph's full node ID. The output directory must be fresh or contain this recipe's matching ownership record. A changed pin, existing unrelated output, altered runtime, source symlink, sensitive-name/vault input, or input above 10,000 files/128MiB fails closed. These limits suit a chosen source subtree; this is not an automatic whole-home scan. Do not point it at a real vault or credential store.

The actual admitted extraction is:

```text
<pinned-venv-python> -I -B -m graphify extract <source> --code-only --no-cluster --max-workers 1 --out <output>
```

It produces `<output>/graphify-out/graph.json`, caches, and per-run receipts/logs. In this mode there is no community analysis, generated report, or HTML renderer. Graph and cache contents are private derived project data. Retain them with the owning task and check relevant edges against current source before relying on them.

## Isolation and fidelity

Each run constructs a fresh empty HOME and environment, sets `GRAPHIFY_BACKEND=none`, disables query logging and Google shortcut access, and omits all provider/proxy/account variables. It invokes no upstream `graphify install` mode. There are no AGENTS edits, hooks, OpenCode plugins, watcher, post-commit rebuild, daemon, HTTP/MCP server, database, Cloud connection, vault export, or browser/CDN execution.

Before upstream runs, the same OS profile must deny a loopback network connection and a synthetic file read outside the approved home paths. The final profile denies network access, denies `/Users` content reads except the explicitly chosen source/output/runtime/interpreter, and confines writes to output. It retains normal system-loader access and metadata lookup, so it is **not** a universal filesystem read sandbox. The denied-file probe uses only an owned temporary synthetic file; it never opens a real personal-data file to test permissions.

The runtime PATH contains an empty directory, so graph extraction cannot launch Git, a model CLI, or other unrelated helpers. This deliberately means Git's tracked-file override and personal/global Git ignore configuration are not consulted; source-local `.gitignore`/`.graphifyignore` behavior remains available. A code-only run still enumerates the selected directory and may inspect supported non-code inputs before omitting semantic extraction. Choose an approved code subtree, not an arbitrary personal folder.

The exact actual upstream Codex/OpenCode skill bodies and their eight reference sidecars each are preserved under `upstream/`, with hashes/source paths in `SOURCE.json`. They are **reference-only**, not installed skills. Their broad graph-first descriptions, automatic unpinned installation, model/subagent instructions, and installer effects are not activated by this recipe. No rewritten replacement skill is presented as upstream. Graphify source is unchanged; this boundary is a separately labeled launcher.

## Dependency and license record

`wheels-macos-arm64-cp312.json` selects exact wheel URLs/hashes from the pinned upstream `uv.lock`: 30 core runtime packages and one separate setuptools84.2.1 build package. No provider SDKs, watch/MCP/database clients, transcription models, heavy clustering extras, or `[all]` extra is installed. Requirements use exact versions and hashes. Downloads are anonymous HTTPS; builds and installation run with OS network denial and no index. The source archive and reproducible built wheel have fixed hashes checked by the recipe. Build tools live in disposable non-synced temporary storage; runtime dependencies remain durable in the isolated environment.

Wheel metadata and available exact license texts were inspected before installation and are retained in `DEPENDENCIES.json` and `licenses/`. Core wheels have no `.pth` startup files or installed data scripts. Licenses are principally MIT/BSD, with NumPy's bundled licenses and Elixir's Apache/MIT notices preserved. Upstream packaging limitation: tree-sitter-groovy0.1.2 declares MIT in METADATA but omits the full license text from its wheel and source distribution. That declaration and the source archive hash are recorded; this repository does not redistribute its binary wheel. This review does not certify the native code of every dependency.

## Verified readiness

The source archive was checked against the reviewed Git pin; two source builds in different directories reproduced wheel SHA256 `3d1003bc420f4413da555d78946a151ccd41ec3decc583c5b2f034decf58c50e`. Actual bounded acceptance used a synthetic Python corpus and a documentation omission sentinel under OS network denial:

- 10 initial nodes and 14 edges; known import, call, inheritance and source lines independently checked against Python's standard AST parser.
- Repeat extraction retained the same graph; rename and deletion removed stale nodes/edges; no dangling endpoints or semantic document nodes.
- Actual query, disambiguated path, and explanation returned the expected call relationship.
- Zero model input/output tokens and zero external provider cost. Five focused tests passed, including runtime acceptance and source/environment safeguards.

Run `python3 -m unittest discover -s tests -p test_graphify.py -v`. Runtime acceptance skips when this exact environment has not been explicitly prepared. This evidence covers the Python fixture and admitted commands, not every supported language, large-corpus performance, communities, full semantic extraction, host loading, or token-saving marketing claims. Use remains conditional/on-demand.
