# Harness choice

A harness is the agent engine: its tool loop, session state, permissions and
recovery. Selecting a model inside OpenCode does not replace that engine.

For an existing nstack Mac, use native Codex for the additional everyday engine.
The optional [OpenCode launcher](OPENCODE.md#actual-codex-harness) opens it in a
project terminal with its current settings and subscription sign-in. Keep
OpenCode's native chat available alongside it. This uses an already installed,
tested engine and avoids a second background orchestration service.

| Source reviewed | Role | Decision |
| --- | --- | --- |
| [OpenAI Codex](https://github.com/openai/codex), installed CLI 0.167.0 | Native coding agent with its own tools, permissions, sessions and subscription access | Chosen for the explicit everyday launch lane |
| [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness/tree/fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159), root 0.2.2-rc.1 | Separate plugin-based agent runtime and web/desktop interface | Developer preview; a future isolated experiment, not an OpenCode engine drop-in |
| [DeepSeek Superagent prototype](https://github.com/deepseek-ai/dsh-superagent-prototype/tree/8c32a9dc5d72c033816c6a8110b37f40cf94fba4), 0.1.0 | One-repository request intake, ticket execution and GitHub replies/PRs using DeepSeek Harness | Reviewed, not installed or activated for ordinary local tasks |
| [OpenHarness](https://github.com/autonomous-ai/openharness/tree/6b0963497eed7f711270ffba730c61e48fd91d24) | A command center around existing agent terminals, with daemon, hooks and optional machine links | Adds overlap for this single-Mac setup; does not replace an agent's internal engine |

## What would justify DeepSeek Superagent

Its own README calls it research code for reference, not a production-ready
product. Its executor and presets use DeepSeek Harness APIs, not OpenCode's.
Renaming its files or adding it to OpenCode's skills would not install that runtime.

A real trial needs a specific repository, a dedicated bot account with scoped
access, allowed requesters, model/provider authority and a separate harness
profile. Start with automatic merging disabled and proactive intake in observe
mode. Observe mode does not disable explicitly requested work or all model use.
Do not turn it on as a generic personal assistant or point it at the whole Mac.

The pinned deployment guide specifies DeepSeek Harness 0.2.1-rc.3 and the package
declares a compatible range; check that exact combination rather than installing
an unreviewed latest runtime. Its profile changes process-wide PATH and Git
configuration, so keep it apart from everyday sessions. Setup would need its own
backup, provider check, denied-request tests, interruption/retry check, durable
artifact verification and rollback before claiming readiness.

Shared canonical knowledge would still use Markdown with current source/scope
and correction metadata. Copying host-generated memories or chats between
applications is not part of this design. No Superagent daemon, bot, account,
schedule or automatic GitHub posting is created by nstack's Codex launcher.

Sources: pinned repositories above, [OpenCode GUI SDK](https://opencode.ai/docs/build/plugins/gui),
[OpenCode V2](https://opencode.ai/docs/), and [Codex authentication](https://learn.chatgpt.com/docs/auth?surface=cli).
