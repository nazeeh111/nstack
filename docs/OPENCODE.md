# OpenCode V2

Install nstack's native skill collection first, then run:

```sh
python3 opencode_setup.py install
opencode --version
opencode api skill.list
opencode mcp list
```

The adapter was checked against OpenCode 2.2.6. It uses the installed desktop
CLI, not another package installation. Pass `--cli /absolute/executable` for a
different existing V2 installation. The selected model, provider, effort,
credentials, conversations and native permissions are untouched.

OpenCode discovers the existing `~/.agents/skills` collection. Its global
`~/.config/opencode/AGENTS.md` links to the user-owned `~/.codex/AGENTS.md`.
Review that shared file for host-specific assumptions first. The optional
`templates/AGENTS.md` is a concise starting point, not an automatic replacement
for user preferences. The native installer continues to manage its nstack block.

A small V2 configuration disables background warming and connects the existing
free Context7 and GitMCP endpoints. If the selected Serena runtime is present,
it uses that runtime with no memories, dashboards or automatic project activation.
OpenCode gets a separate Serena state directory to avoid competing host writers.
The adapter refuses existing conflicting configuration or links before changing
anything. It never reads auth stores or service registration, copies provider
configuration, or rewrites existing JSONC. Existing customized configurations
require a scoped manual merge rather than an automatic reset.

Both hosts follow the same canonical Markdown knowledge and task handoffs.
On the author Mac the private vault is `~/Knowledge`, with private local Git
history. Keep source, scope, note ID, generation/hash, dates and correction path
with each claim. Re-read the current note and source before reuse. Give concurrent
tasks separate files; reconcile a changed generation before writing a shared note.
For project JSON records, `nstack knowledge set/delete --expected-generation N`
serializes writers and rejects stale updates. Creation uses generation 0. This
protects that command, not arbitrary Markdown edits or host-generated memories.
No synchronizing daemon, extra database, automatic-memory export or public-vault
copy is needed. Native automatic memories and chat histories remain host-owned.

## Actual Codex harness

The optional Desktop launcher starts the installed native Codex CLI in an
OpenCode session terminal. It adds `/codex` and **Open Codex harness** to the
desktop command palette. This is a separate native Codex conversation beside
the OpenCode chat. It does not replace OpenCode's own agent engine.

```sh
python3 opencode_setup.py install --codex-harness "$(command -v codex)"
```

The launcher targets OpenCode Desktop 2.2.6's experimental GUI and persistent
terminal APIs. Recheck it before upgrading OpenCode. It runs only from a saved
session on the app's own server, in that session's current project directory.
Repeating the command selects its running Codex terminal. A normal OpenCode TUI
terminal can run `codex` directly; the desktop command is not a TUI extension.

No model request is made by opening the terminal. Codex inherits its own account,
model/effort, instructions, discovered skills and permissions. The launcher
does not send the OpenCode transcript or composer draft to another agent.
Use the project's current task handoff file to continue work across hosts;
review it in Codex and give the objective there. Both hosts still read the same
shared skill collection and canonical vault. Their native chats and generated
memories remain separate. Native refusals are reported without alternate routes.

The installer accepts the exact original nstack adapter configuration or the
exact desired launcher configuration. Customized config or plugin bytes require
a scoped merge. Installation backups and rollback cover the two plugin files
and configuration, while the existing adapter and user data remain recoverable.
See [the harness decision](HARNESSES.md) for the alternatives reviewed.

Codex's account connectors, app tools, built-ins, permissions, model support and
native automatic memory are not OpenCode plugins. Shared skill discovery does
not prove every host-dependent operation. Check actual available tools and use
supported native equivalents; report unavailable operations. Trials, substitutes,
paid/hardware/provider lanes retain their original activation conditions.

The install privately journals its exact targets, rehearses restoration of
existing targets and extends the normal `nstack` rollback chain. A second install
with unchanged inputs writes no target or journal changes. Later user edits
block a conflicting rollback instead of being discarded. Empty parent directories
may remain after rollback; projects, notes and conversations are preserved.

```sh
"$HOME/Library/Application Support/nstack/rollback.sh"
```

Quit Obsidian before the full chain if it includes an Obsidian application
replacement. Use `python3 opencode_setup.py rollback /exact/run` for just this
adapter without invoking older changes. Recovery code is staged outside the
checkout before any live mutation.

Guidance checked against [OpenCode instructions](https://opencode.ai/docs/instructions/),
[skills](https://opencode.ai/docs/skills/), [MCP](https://opencode.ai/docs/mcp-servers/)
and [warming](https://opencode.ai/docs/warming/), plus the installed API schema.
OpenAI recommends short, accurate [personal and project instructions](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
and separating reusable skills from global rules in its [best practices](https://learn.chatgpt.com/docs/learn/best-practices).
Keep supported [permission configuration](https://learn.chatgpt.com/docs/permissions)
consistent; legacy sandbox settings override mixed modern defaults. Preserve the
current effective permissions when cleaning up redundant fields.
