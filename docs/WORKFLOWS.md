# On-demand workflows

These integrations build applications and execute explicitly selected jobs. They do not replace the Codex/OpenCode harness, canonical Obsidian vault or host-owned memory. No service starts automatically. The installer supplies portable recipes; each recipe has its own source locks and acceptance checks. An installed recipe is not proof its runtime is commissioned on another Mac.

| Need | Integration | What was checked on the author's Mac |
|---|---|---|
| Import, execute and export visual workflows | [n8n](../integrations/workflows/n8n/README.md) | Official 2.47.4 Docker CLI, real branching result, wrong-result and invalid-node controls, persistent stop/start and localhost health. Owner UI, OAuth, API and Code runner are not configured. |
| Find node schemas and validate workflow structure | [n8n docs MCP](../integrations/workflows/n8n-mcp/README.md) | Selected 2.101.0, seven real tools and native stdio transport. Workflow API tools need a separately configured n8n connection. Structural validation does not prove the result is correct. |
| Durable TypeScript background jobs | [Trigger.dev](../integrations/workflows/trigger/README.md) | Selected 4.8.3 source/profile prepared. Full self-hosted execution remains untested; it needs a dedicated Docker engine, sufficient resources and private operator configuration. The two selected authoring/cost skills remain available. |
| Tool-using AI applications and durable state graphs | [LangChain and LangGraph](../integrations/ai-workflows/README.md) | Locked Linux arm64 Docker runtime, typed tool calls and graph pause/crash/resume with exactly one effect. Tests use a fixed local model, with no paid inference. |
| Application tracing and evaluation | [Langfuse](../integrations/ai-workflows/README.md#optional-langfuse) | Six official pinned images pulled and Compose profile validated. Not started: the existing Docker VM has approximately 8 GiB; the stack needs more resources and private operator configuration. No automatic tracing enabled. |
| Repeated structural mapping of a codebase | [Graphify](../integrations/graphify/README.md) | Source-exact 0.9.106 CLI, independent AST comparison, repeat/rename/deletion, queries, paths and explanations. Code-only, offline, project-scoped; semantic enrichment and upstream host hooks stay unconfigured. |

Use the complete linked instructions and actual command interface. LangChain/LangGraph are application libraries, not extra background services. Langfuse is optional observability for an application that needs it. Narrow code navigation can keep its existing semantic tools instead of building a graph.

On this private deployment, 01's live runtime search includes descriptions and activation conditions from the installed tool index. New records become discoverable without editing 01 or maintaining a second category list. Readiness and permissions still require inspection; search results do not execute anything.

Licenses and pinned upstream revisions are recorded beside each integration. Runtime data, accounts, secrets, images and local evidence are not included in this repository. Heavy profiles remain stopped until their resource and configuration prerequisites are satisfied.
