# nstack on Mac Claude Code

The optional Claude Code adapter installs the same reviewed base methods and
chosen addons through Claude's own skill discovery. It leaves Codex and OpenCode
profiles intact. It does not reactivate Claude on an existing machine unless you
explicitly run this installer for that home.

Use an existing Claude Code installation and account. From a reviewed nstack
checkout, choose the complete set of addons you want:

```sh
python3 claude_setup.py install --adaptive-routing
```

This includes the reviewed base selection plus `01`. The optional switches match
`native_setup.py`: `--agent-reach`, `--repository-docs`, `--academic-research`,
`--ecc`, `--unslop`, `--maps-scraper`, `--untangle-codebase`, `--raea`,
`--llm-council`, `--cloudflare-security-audit`, `--strix`, `--skillspector`,
`--roast-room`, `--council-of-high-intelligence` and `--craft-anything`. Keep every desired switch on
later installs; an omitted addon is removed only from this adapter's owned links.
`--only NAME` can be repeated for a deliberately limited base selection. With no
`--only`, the full reviewed base is selected. Use `--home` and `--state` only for
an explicitly chosen target installation. `--claude-home /absolute/config-dir`
selects the Claude configuration directory. Without that flag, installation for
the current user honors `CLAUDE_CONFIG_DIR`; a different `--home` defaults to
its own `.claude` directory. An existing managed installation cannot silently
move to another configuration directory using the same state. Reconcile or use
separate state for a separate profile. `--vault /absolute/existing/vault`
records an authorized knowledge location, without granting file permissions or
copying personal notes. Source access, redistribution rights and each runtime's
prerequisites still apply. An addon switch installs guidance, not its engine.
When selecting `--claude-home`, launch Claude Code with `CLAUDE_CONFIG_DIR` set
to the same directory so its native loader uses the installed profile.

The adapter creates individual `~/.claude/skills/NAME` links and a managed nstack
block in `~/.claude/CLAUDE.md`, or those same paths under the selected Claude
configuration directory. Unrelated skills and instructions stay in place.
An existing skill with the same name is preserved and causes a collision error;
inspect it and resolve the ownership choice explicitly. Existing linked profile
directories and changed owned entries also stop the installer. It never merges
account settings or inspects credential stores.

Complete support bundles remain outside the discovery directory, with their
relative paths preserved. Only selected entrypoints are linked into Claude.
Separate Claude payloads remove permission-granting and execution-control
frontmatter (`allowed-tools`, `model`, `hooks`, `context`, `agent`, `shell`),
while retaining the method body and other metadata. Original entry bytes are
retained outside the exposed leaves. `01` and existing manual-only methods use
Claude's `disable-model-invocation: true`; ordinary skills retain automatic
selection. Entries containing Claude's executable dynamic shell-injection syntax
or a skill-directory plugin manifest require a separately reviewed port and are
rejected. No such execution is activated by this adapter.

Start a new ordinary Claude Code session after installation. Confirm the
personal skills and instructions in Claude's native `/skills` and `/context`
views, then begin routing with `/01` and your outcome. The session uses Claude's
native tools and available MCPs, with its current model and permission settings.
01's installed lookup helper selects the Claude skill index and personal/project
Claude roots from its own release location. It honors `CLAUDE_CONFIG_DIR` for the
current user's personal skills, while project roots remain `.claude/skills`.
Its optional `--host native` or
`--host claude` override is useful from a source checkout. Separate host variants
do not crowd the default search results on a machine with both installations.
Respect manual-only boundaries and report a missing capability honestly. Codex
account plugins, tool identifiers and generated memory do not become Claude
capabilities by sharing skill files. Host-specific integrations need their own
available equivalent or explicit commissioning. No hooks, background service,
provider keys, paid inference, account connection or runtime startup is added.

Before a profile change, the installer backs up actual target bytes and rehearses
their restoration separately. It journals writes under the existing nstack
profile lock, checks fingerprints for concurrent changes and registers terminal
recovery before the first mutation. Repeating identical inputs is a no-op.
Cached payloads are checked against verified native source inputs, rather than
trusting an editable cache manifest. A changed generated payload or managed
instruction block stops for reconciliation.

The install result reports the exact run and recovery helper. To undo its last
profile change and continue the recorded recovery chain:

```sh
"$HOME/Library/Application Support/nstack/rollback.sh"
```

To undo only a named Claude installation run:

```sh
python3 claude_setup.py rollback /absolute/nstack/state/runs/claude-RUN
```

Recovery checks all recorded targets before restoring any. Later conflicting
edits stop recovery and remain intact for reconciliation. New unrelated files
and knowledge stay untouched. If an installation is interrupted, use its
registered rollback before attempting a new install.

The isolated tests exercise real filesystem transactions, preserved dirty bytes,
relative support, native header filtering, manual invocation, source tampering,
collisions, concurrent edits, repeat behavior, interrupted writes, generation
updates and the saved installer's terminal rollback. They do not demonstrate
native Claude model behavior, tool availability or runtime acceptance. Confirm
those in the friend's actual host before claiming a fully commissioned setup.

Host contracts were checked against Anthropic's official
[skill documentation](https://code.claude.com/docs/en/skills) and
[instruction-file documentation](https://code.claude.com/docs/en/memory), including
the [configuration-directory override](https://code.claude.com/docs/en/settings).
