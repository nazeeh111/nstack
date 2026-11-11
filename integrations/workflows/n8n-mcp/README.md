# Offline n8n docs and validation MCP

This supplies the seven actual documentation/schema/validation tools expected by the selected n8n skills, without an n8n account or API key. It does not connect to the n8n workflow management API or replace the upstream skills' methods.

From the nstack source directory:

```sh
python3 recipes/n8n_mcp.py prepare
python3 recipes/n8n_mcp.py pull
python3 recipes/n8n_mcp.py check
python3 recipes/n8n_mcp.py list-tools
python3 recipes/n8n_mcp.py call --tool get_node --arguments '{"nodeType":"nodes-base.if","detail":"standard"}'
```

For a full workflow validation, write `{ "workflow": <workflow JSON object> }` into a task-owned arguments file, then:

```sh
python3 recipes/n8n_mcp.py call --tool validate_workflow --arguments-file /absolute/path/to/arguments.json
```

The `list-tools` and `call` commands print the original upstream JSON-RPC response. They start a fresh isolated server, perform a real MCP initialization and request, then remove their owned transient container. They do not synthesize tool results. Actual exposed tools are tools_documentation, search_nodes, get_node, validate_node, get_template, search_templates and validate_workflow. The network-isolated server has no N8N_API_URL or N8N_API_KEY, so workflow management tools are unavailable. Core import/execute/export is available separately through recipes/workflows.py.

For a native host's project-only stdio configuration, the executable command is:

```sh
python3 /absolute/path/to/nstack/recipes/n8n_mcp.py serve
```

`serve` forwards upstream bytes without renaming tools or changing their responses and cleans up on stdin EOF or termination. The optional disabled example files are not installed into either host. Codex uses command/args in a project .codex/config.toml; OpenCode2 uses a local command under mcp.servers. The installed OpenCode version was observed as2.2.6. Examples intentionally start disabled, and no global or project host configuration was changed. Existing host permissions still apply.

[Official OpenAI stdio configuration documentation](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) and [official OpenCode2 MCP documentation](https://opencode.ai/docs/mcp-servers) were checked on2026-11-11. Selecting an optional project binding is separate from claiming that these tools are already registered in the hosts.

Version2.101.0 preserves the selected P089 catalog revision1c755c5c8d99eb71faade17753a7f24138f4212c. The official Docker image reports build revision86b993e70008c4987902a235271e11bc03ef3f84. Official comparison shows only two subsequent commits changing three GitHub issue-triage CI files; runtime files are unchanged. Both revisions and image digest are disclosed in SOURCE.json. The image is MIT licensed, with the original license retained. Its bundled node catalog is based on n8n2.46.4; the separate core runtime is2.47.4. Verify exact node typeVersion against the target runtime instead of treating catalog defaults as live server schemas.

Acceptance actually initializes the MCP server, lists its tools, fetches IF-node information and validates the same synthetic fixtures used by the core runtime. The good workflow validates. The deliberately miswired workflow also validates structurally, while the core CLI's independent output assertion rejects its wrong result. The unknown-node fixture fails validation. This preserves the upstream rule that structural validation alone is insufficient. No API key, owner setup, OAuth, model/provider call or network workflow is required for this loop.

Every server runs on demand with network=none, read-only root filesystem, a small anonymous /tmp tmpfs,768MiB/1CPU cap, dropped capabilities, no-new-privileges, no host/vault/socket mounts, no published port and no persistent data volume. Telemetry is disabled before the first server process via N8N_MCP_TELEMETRY_DISABLED=true. Docker CLI gets its own empty config/home and a selected existing local Unix daemon endpoint, without inheriting provider/proxy variables or Docker account configuration. No image rebuild or upstream installer runs.

Private source locks and synthetic response receipts live under NSTACK_STATE/native-tools/workflows/n8n-mcp/2.101.0. Changing frozen bytes is rejected and preserves them. The helper never changes the n8n core volume, user containers or host settings. Optional templates can refer to external integrations; fetching template metadata does not authorize running those workflows.
