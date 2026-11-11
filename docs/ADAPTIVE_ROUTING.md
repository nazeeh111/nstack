# 01 adaptive routing

`01` is an explicitly invoked skill, not another agent engine. Start a session
with `$01` and the desired result. Its instructions stay relevant to later
requests in that session until the user disables 01. A saved task status
does not activate it in an unrelated session.

For nontrivial work, it binds each stage to an available capability, inputs,
a deliverable and an acceptance check, orders dependencies and executes.
The route stays internal or in the existing task entrypoint; advice alone is
a deliverable only when the user requested advice.

It keeps ordinary requests direct. For substantial or specialist work, it
examines relevant expertise and verification methods before choosing a route,
then reads and applies the selected complete skills and needed support.
It reconsiders capabilities at stage changes, failures, new evidence or a
materially better option. It combines complementary expertise, uses independent
scrutiny when useful and checks actual outputs rather than trusting success
messages. The active host executes work with the user's existing model,
reasoning effort, account and permissions; 01 does not switch harnesses. No daemon, hook or compulsory plan,
team, report, global memory store or automatic self-edit is installed.

For a weak match or concrete capability gap, 01 applies the installed find-skills method. A justified addition stays project-scoped and proceeds through source review, verification and actual task use within existing authority. No second skill invocation is required.

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

The shared collection also exposes01 to OpenCode. Its
`metadata.opencode/autoinvoke: false` setting preserves explicit selection in
OpenCode. Codex uses `policy.allow_implicit_invocation: false` in
`agents/openai.yaml`. Use the host's own skill selector; sharing the files does
not merge generated memories or conversations.

## Capability lookup

01 owns specialist selection so the user does not need to name individual
skills. It considers native tools, connected plugins/MCPs, skills and installed
runtimes together, and reuses effective specialists across task stages.

For broad requests such as maximizing a presentation, 01 derives the relevant
quality dimensions from the audience, artifact and constraints. It considers
complementary expertise across disciplines, instead of mapping a task noun to
one skill. Categories are temporary views of the current capabilities, not a
maintained task-to-skill table or a requirement to use every available tool.

When native summaries are incomplete, its bundled scripts/capabilities.py
refreshes bounded metadata from current user/project skill roots and searches
nstack’s recorded skill/runtime indexes. Added skills can be found on the next
lookup without regenerating a category file. It reads frontmatter rather than
executing skill bodies, returns a small ranked result and records discovery
provenance. Explicit isolated-state lookup does not read unrelated host skills.

This file discovery does not establish host enablement, permissions, current
runtime callability or that a method actually ran. Native connected-tool/plugin
discovery remains separate. Read and apply selected complete skills and needed
support to the actual artifact; verify its outputs.

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

A skill supplies guidance in the conversation context. It cannot guarantee a
host's future summarization, grant unavailable tools, bypass permissions or
force a model to follow instructions perfectly. Preserve task-scoped recovery
context when substantial work needs it. Host-native automatic memory remains
separate and user-owned skill improvements require user authorization.

## Instruction design

The entrypoint keeps routing and adaptation rules; shared authority, privacy
and local-work rules live in AGENTS.md. Complete specialist methods load when
relevant. No generic decision checklist or mandatory planning ceremony is added.
This follows OpenAI’s guidance on [concise project instructions](https://learn.chatgpt.com/guides/best-practices),
[progressive skill disclosure](https://learn.chatgpt.com/docs/build-skills) and
[testing skills through real outcomes](https://developers.openai.com/blog/eval-skills).
The [September 2026 prompt review](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)
also motivates removing repeated orchestration prose. Its Astra-specific behavior
claims are not assumed for other models; the user’s model and effort stay intact.

Comparable Superpowers, Everything Claude Code and gstack workflows were reviewed
for routing and evaluation ideas. Their bootstrap hooks, compulsory roles and
startup procedures are not installed: no demonstrated gap justified that overlap.
Behavioral comparisons establish the tested cases, not universal superiority.

CrewAI’s [task dependencies and guardrails](https://docs.crewai.com/en/concepts/tasks)
inform one compact coordination rule: sequence dependencies, parallelize
independent work, and check consequential handoffs before downstream use.
These are host-native workflow choices; CrewAI is not a required runtime.
