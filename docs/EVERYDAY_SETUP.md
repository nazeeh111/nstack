# Everyday setup

The default global collection contains all 126 installable on-demand leaves from
the evaluated manifest. It excludes trial/substitute/reference/rejected leaves.
Natural names and complete bundles are verified independently against the
registered original releases. Optional `--only EXACT-NAME` deliberately narrows
an installation; it is not the full setup. The explicit additions are
`--agent-reach` and `--repository-docs`. The latter guides public repository
lookups and strict version handling in Context7.

## Runtime connections

Keep native computer use, Node REPL, existing account integrations, model and
effort. Install Serena from the selected source into an isolated Python
environment. Its MCP entry uses `start-mcp-server --context /absolute/codex.yml
--mode no-memories --agent-interface tools --enable-web-dashboard false
--enable-gui-log-window false`. Use the authored context and prompt templates
in `templates/serena`, copied into a private SERENA_HOME. The supported prompt
override belongs at `SERENA_HOME/prompt_templates/system_prompt.yml`.
Do not substitute a session-wide mandatory startup or Claude runtime workflow.

Use Codex's supported `codex mcp add` and `codex mcp --help`, retaining current
permissions and unrelated entries. Context7's free read-only URL is
`https://mcp.context7.com/mcp`; enable only resolve-library-id and query-docs.
GitMCP's URL is `https://gitmcp.io/docs`; enable only fetch_generic_documentation,
search_generic_documentation and search_generic_code. Neither needs account
login for the tested public queries. Hosted service code and corpora are mutable;
reviewed source revisions are not a claim of a pinned hosted deployment.
Reject an explicit missing-version fallback to current docs as version evidence.
Never send private code, vault notes or account information to these services.

ChromeDevTools stays an explicit per-task tool, not another globally active
browser. Use isolated/headless profiles, no usage statistics/performance CrUX,
and `--workspace /exact/authorized/project` for output. A denied output path is
not permission to use unrestricted flags. Agent-browser uses a unique named
session and matching skill-data assets from the exact selected source; do not
attach an everyday authenticated profile. Agent Reach is anonymous/public by
default. Do not run its browser-cookie import or account setup automatically.

## Exact native tools checked on the author Mac

These are bounded actual-operation reports, not acceptance of every platform or
feature. The 198 on-demand component routes remain distinct from installed and
verified runtimes. `nstack route ID` gives prerequisites and the implementation
route; a route or cached source is not proof that a tool ran.

| Tool | Version / selected source revision | Actual check |
|---|---|---|
| Serena | 2.1.1.dev0 / ede329aaf0c824bea75455a2926f01420d7aa620 | Symbols, imported references, cross-file rename and behavior; native tool call |
| Context7 | 1496b428efb35acb7bd6a1da98e50fd1d3dccdcc reviewed | Distinct Apollo projects, old version, explicit missing-version fallback |
| GitMCP | c487a29895dcfcb5b672247e646426a56e2051c1 reviewed | Public repository documentation through native MCP |
| Agent Reach | 1.6.1 / c70ae6da5d39bc90e09ad2ae0575ccc89f31e284 | Anonymous public-page content; account channels unconfigured |
| OfficeCLI | 1.0.160 / c56512c8c7b76fe284f09940e4cd492470099d3e | DOCX table/image/edit, XLSX formulas, PPTX chart/table/notes and schema readback |
| LibreOffice | 26.8.2.2 | Signed app, official SHA256, real PDF exports and explicit UNO spreadsheet recalculation |
| MarkItDown | 0.1.9 / 7482c092d9c0074a89803c9fdb63a969e7fe17fc | Local DOCX/PPTX/PDF extraction with plugins disabled |
| Scrapling | 0.5.1 / 3a4bb5b0a008233c85269a0a38a6d08edd4ce329 | Local parser field/unit/cardinality checks and duplicate negative |
| agent-browser | 0.41.2 / 6682da310c75bed8af340b39cc10b7f71bded155 | Exact-source Rust build, form once, isolated second session |
| ChromeDevTools | 1.12.0 / 0877ee00d2e43c1c04bba275e7d08cc1033e36e9 | Exact-source/submodule bundle, console/network diagnostics, measured trace comparison |
| Obsidian | 1.14.4 | Native create/read/search, Base query, note correction and private Git history |

Same-number published agent-browser and ChromeDevTools packages differed from
the selected revisions. The actual Mac uses source builds, not those packages.
OfficeCLI used `OFFICECLI_NO_AUTO_RESIDENT=1`. Its official Mac arm64 binary SHA256
was `fe2b31c6c27534dfbbf155386b6b9105420f9315bbb606335ec61490d171386d`.
LibreOffice's official Mac arm64 DMG SHA256 was
`9f24fe83ab1ed5c95eb3df580119f32932f713e577feeac02bf619fb00749b55`.

Existing commissioned ast-grep, Playwright, Optuna, Gitleaks, UX lookup, FFmpeg,
room-decay estimation, posting guard and oasdiff also have actual fixture checks.
Keep an installation-local `native-tools/index.json` with absolute entrypoints,
source revisions, locked dependencies and narrowly worded check results. Never
publish that machine-specific index. Keep permanent runtime dependencies durable;
reacquirable compilers/build caches can use non-synced temporary storage.

## Canonical knowledge vault

Choose one existing, explicitly authorized vault. `--vault /absolute/vault` only
writes its location into owned guidance; it does not import notes or initialize
an arbitrary directory. `templates/vault` is a clean starting structure with Home,
Library, Templates, Archive, a Base and Canvas. Copy only to a new destination or
merge deliberately. Initialize private local Git with no remote. Ignore Obsidian
workspace/cache data. Do not add private notes to this public toolkit.

Each durable note has a stable ID, owner/scope, current source revision/hash,
event/observation dates, state, generation, superseded generation and correction
path. Reopen the original source before using a claim. Correct the same note ID,
retain prior generations in Git, and exclude historical/test/archive records from
current views. Project source and evidence stay with their owning project.
Use explicit `vault=` and `path=` arguments with the native Obsidian CLI.

Keep Obsidian core Markdown, Bases, Canvas, search and links. Enable link updates
if desired through the ordinary app setting. No community plugin, remote sync,
cloud memory or database is required. QMD needs an actual passage-recall need;
Hindsight needs demonstrated cross-episode misses. Neither is activated merely
because it appears in the catalog. Native Codex automatic memory is separate:
its settings being enabled and a vault test do not prove automatic generation.

## What acceptance means

Fresh ordinary CLI sessions outside the setup performed a routine fix with zero
MCP calls; a cold objective discovered Canvas/Base specialists without naming
them and produced independently checked files. Separate sessions saved then
corrected a source-backed note; interruption plus native resume completed from
a durable checkpoint. Browser session separation and file operations were real.

Normal fresh desktop-chat acceptance still requires the user to launch a new
chat. The native computer-use guard prohibits controlling the Codex app. Backend
inventory is useful evidence but does not stand in for that desktop UI check.
Advanced Microsoft Office fidelity, browser dashboards, authenticated Agent Reach
channels, hardware/provider trials and native automatic-memory generation are
not claimed tested. Existing explicit retained plugin choices are preserved.

The stable rollback is:

```sh
"$HOME/Library/Application Support/nstack/rollback.sh"
```

It restores journaled profile changes and chains previous owned recovery helpers.
It refuses conflicting later edits instead of overwriting them. Private vaults,
new project artifacts and durable acquired dependencies are retained. Run from
Terminal, outside the active Codex process, and retain the private state folder.
