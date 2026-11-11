# NVIDIA SkillSpector

Add `--skillspector` to the native install command, retaining other chosen
flags. This adds one shared `skillspector` skill to Codex and OpenCode. It
preserves the complete upstream Skill Inspector method with a native offline
execution supplement and exact source/license records.

The reviewed [NVIDIA source](https://github.com/NVIDIA/skillspector/tree/9dbf4fc75386169275e5f18c47686cb0d7274afa)
is package 2.12.0, Apache-2.0. Runtime acquisition is explicit and isolated:

```sh
python3 recipes/skillspector.py install --python /absolute/existing/python --uv /absolute/existing/uv
python3 recipes/skillspector.py verify
python3 recipes/skillspector.py run --target /approved/component --outdir /fresh/private/report
```

The recipe uses the pinned Git tree and frozen uv lock, excludes extras/dev,
records installed distribution/runtime/interpreter hashes and checks dependency
health. The standard build-isolation backend is separately resolved by uv;
the receipt records this limit. No global packages, daemon, MCP registration
or OpenCode extension is needed. Use an existing supported Python and uv.

Static runs invoke the actual upstream CLI with `--no-llm`, a fresh environment
and HOME, tracing disabled, and `SKILLSPECTOR_OSV_TIMEOUT=0`. macOS network
denial is required and tested before a scan. Other platforms fail closed in
this recipe. No provider key or credential store is read. Target scripts are
parsed as data and are never executed by this workflow.

Each explicit component gets a materialized, hashed snapshot and its own report.
Reports and complete input inventories remain private with the task. Symlinked
skill roots are resolved deliberately; nested escapes and oversized scopes
are rejected. Do not scan account/config stores, conversations, memory or vaults.
An agent/plugin source directory is different from its credential-bearing state.

A completed static scan is not approval. Read the actual limitations and
source behind HIGH/CRITICAL findings and sensitive MEDIUM findings. Retain the
upstream APPROVE/CAUTION/REJECT rubric with evidence. Matching trusted expected
bytes establishes integrity separately from pattern-based security assessment.
Opaque binaries and dependency artifacts need their own checks.

Live OSV advisory lookup and scanner semantic analysis are unavailable in this
offline lane. Do not represent them as passed. The upstream `codex_cli`
semantic provider is intentionally disabled; this integration preserves that
restriction. Other semantic providers need separately verified data, safety,
version, cost and authorization conditions. Installing the skill grants none.
