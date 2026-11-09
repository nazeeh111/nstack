# Everyday setup

The default global collection contains all 170 installable on-demand leaves from
the evaluated manifest. It excludes trial/substitute/reference/rejected leaves.
Natural names and complete bundles are verified independently against the
registered original releases. Optional `--only EXACT-NAME` deliberately narrows
an installation; it is not the full setup. The explicit additions are
`--agent-reach`, `--repository-docs` and `--academic-research`. The latter guides public repository
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

Enable the core Templates plugin and set **Settings → Templates → Template
folder location** to `Templates`. The folder existing on disk does not configure
the plugin. Verify with `obsidian vault=YOUR_VAULT templates`, then create a
disposable note with `obsidian vault=YOUR_VAULT create path="Archive/Template Check.md"
template="Knowledge Note"`. Read it back and verify its properties before moving
the check note to Trash. Keep the template's initial state as `draft`; a new note
belongs in the current view only after its source and scope have been checked.

Check both app and installer versions in **Settings → General**. App updates can
leave the underlying installer behind; follow Obsidian's [installer update
instructions](https://obsidian.md/help/updates) when it reports that an update is
needed, then reopen the vault and check its views and CLI again.

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

## Academic research skills

Explicit `--academic-research` fetches Imbad0202/academic-research-skills at
`6d9388674de1ad0437ad95db3d52f92b92204d84` (suite 3.24.2) privately. It adds
deep-research, academic-paper, academic-paper-reviewer, academic-pipeline and
sr-screener. The entire 2,860-file source tree has a pinned aggregate hash;
each entry retains complete root/sibling support and the untouched original.
Codex adaptations narrow discovery, translate platform bindings and suppress
Claude hooks, automatic updates, fixed swarms and provider/credential transports.
No API-key environment or auth-copy helper is invoked. Local helpers require
source review and explicit project-local input/output paths. Screening preparation
uses a fresh dedicated work directory because upstream can clear existing batches.

The upstream is CC BY-NC 4.0, copyright Cheng-I Wu. It is source-available for
noncommercial use; it is not MIT-licensed or unrestricted open source. The public
nstack repository contains authored integration code and attribution, not the
upstream payload. Preserve upstream LICENSE/NOTICE and review its terms for your
intended use. Installed references and scripts are not a claim of fully tested
research validity, citation recall or journal-review independence.

## Updated selection and optional additions

The 3.4 selection has 170 installable on-demand entries with explicit natural
names, including four independent gstack skills, six pstack skills, ten Remotion
leaves, Grease Pencil, Unreal animation/pipeline techniques and scoped runtime
adapters. Support is retained outside the exposed native entry list. Templates,
heavy runtimes, provider services and hardware operations retain their task
triggers. PaperBanana's three prepared sources remain a trial; generated plot
execution refuses until a verified isolated executor exists. No blank placeholder
image can count as successful generation.

`--ecc` adds only `codebase-onboarding` and `eval-harness` from the pinned ECC
source. Onboarding does not write AGENTS.md unless asked. Eval utilities support
local synthetic fixtures, record integrity and replay; their candidate execution
gate is unavailable on every OS and is kept closed. Capsules are not proof of
truth, independent grading or operating-system containment. No ECC hooks,
instinct store or controller is installed. Karpathy's general principles were
reviewed as references because existing user guidance already covers them.

Additional exercised Mac routes are Blender5.2.1, TLC1.7.4 with existing Node/Java,
Worktrunk0.81.0, Repomix1.19.0 and PyVISA's simulator. Their recorded entrypoints
belong in the private native-tools index. Worktrunk's selected skill revision and
release binary are separate provenance fields; neither is silently equated.
`recipes/P056/install.py` checks the official Mac ARM release digest and does not
install shell hooks. `nstack commission P049 cli` installs the frozen Repomix
package; `nstack check P049 cli` exercises packing and exclusion.

For a simulator-only instrument trial, create a private Python3.12 environment
and sync `recipes/X-HW-VISA/sim/requirements.lock` with hash checking, then run
`recipes/X-HW-VISA/sim/check.py` with that environment's Python. It binds literal
`@sim`; real instrument access and physical outputs are separate task authority.
The Blender cache fixture in `tests/fixtures/blender_simulation.py` exercises an
owned procedural rigid-body scene. Its baked-cache pass does not prove cloth,
fluid, geometry-node or other simulation caches.

The canonical vault stays one private Markdown/Git repository. Source-backed
notes retain stable IDs, scope, source hashes and correction history. Existing
notes and user changes are preserved. No new vault, filler taxonomy, background
memory server, automatic API key or paid provider is added by this update.
