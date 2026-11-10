# 01 adaptive routing

`01` is an explicitly invoked skill, not another agent engine. Start a chat
with `$01` and the desired result. Its instructions stay relevant to later
requests in that conversation until the user disables 01. A saved task status
does not activate it in an unrelated chat.

It keeps ordinary requests direct. For substantial or specialist work, it
examines relevant expertise and verification methods before choosing a route,
then reads and applies the selected complete skills and needed support.
It reconsiders capabilities at stage changes, failures, new evidence or a
materially better option. It combines complementary expertise, uses independent
scrutiny when useful and checks actual outputs rather than trusting success
messages. The active host executes work with the user's existing model,
reasoning effort, account and permissions; 01 does not switch harnesses. No daemon, hook or compulsory plan,
team, report, global memory store or automatic self-edit is installed.

## Install

Add `--adaptive-routing` to your existing complete native selection. For the
currently documented optional collection:

```sh
python3 native_setup.py install --replace --agent-reach --repository-docs --academic-research --ecc --unslop --maps-scraper --untangle-codebase --adaptive-routing
```

Keep your other explicitly selected flags; omitting them requests a different
collection. The transaction backs up the actual skill root and instructions,
rehearses restoration and preserves other selected bundles and support. A
second install with unchanged inputs is a no-op. Terminal recovery remains:

```sh
"$HOME/Library/Application Support/nstack/rollback.sh"
```

The shared collection also exposes01 to OpenCode. Its supported
`disable-model-invocation` frontmatter and Codex's `allow_implicit_invocation`
metadata both preserve explicit entry. Use the host's own skill selector;
sharing the files does not merge generated memories or conversations.

## Capability lookup

01 owns specialist selection so the user does not need to name individual
skills. It considers native tools, connected plugins/MCPs, skills and installed
runtimes together, and reuses effective specialists across task stages.

When native summaries are incomplete, its bundled scripts/capabilities.py
searches the current installed skill and runtime indexes, including additions
outside the original catalog. It reads bounded skill descriptions, returns a
small ranked result and records the index hashes. It does not install anything,
read provider/account stores or claim that a catalog match executed. Native
connected-tool discovery remains separate. The selected complete skills and
relevant support still need to be applied to the actual artifact.

## Proof and limits

The project uses fresh native conversations with the existing subscription,
model and effort. Frozen synthetic inputs, independent artifact checks and
negative controls stay separate from worker prompts. Tool traces must show
successful full skill/reference reads, relevant execution and output checks;
an advertised capability, metadata match or self-report is insufficient.

The [portable synthetic cases and independent checkers](../evals/01/README.md)
compare the old and refined instructions on direct work, specialist
format work, a later discipline change without re-invocation, explicit disable,
unavailable integration, conflicting reference advice and false-success output.
Additional trials exercise real native process restart/resume, changed input,
an interrupted operation and independently owned specialist work with an
integration review. Report first-attempt results and trace evidence separately;
these examples do not establish universal reliability or every tool's readiness.

The generic skill-creator validator's allowlist does not include OpenCode's
manual-invocation flag. Keep that host-supported field and validate it in the
actual native loaders rather than changing a built-in validator or removing
the explicit-entry protection. Codex-only schema checks can separately inspect
a temporary projection without the OpenCode field; label that scope accurately.

A skill supplies guidance in the conversation context. It cannot guarantee a
host's future summarization, grant unavailable tools, bypass permissions or
force a model to follow instructions perfectly. Preserve task-scoped recovery
context when substantial work needs it. Host-native automatic memory remains
separate and user-owned skill improvements require user authorization.
