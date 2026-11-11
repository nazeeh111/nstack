# Local n8n workflow runtime

This adds real on-demand n8n2.47.4 core execution. It does not create an owner account, register a license, connect MCP/OAuth, import private chats, or configure external services. The existing upstream skills remain separate and unchanged.

From the nstack source directory:

```sh
python3 recipes/workflows.py prepare
python3 recipes/workflows.py pull
python3 recipes/workflows.py check
python3 recipes/workflows.py start
python3 recipes/workflows.py stop
python3 recipes/workflows.py status
```

`start` serves only http://localhost:5678. Initial owner setup is a user action in the browser. No MCP/API connection has been established by this recipe. `check` runs only authored synthetic builtin-node fixtures, uses new IDs for every run, checks exact output and persisted wiring, rejects wrong wiring and an invalid node, verifies localhost health/restart persistence, then stops all owned containers. It retains the named data volume and private receipts under `NSTACK_STATE/native-tools/workflows/n8n/2.47.4`. Do not delete this volume: it holds the instance database and framework-generated encryption material. The helper never extracts credentials or copies the volume to evidence.

Use `--port 5679` on the initial preparation if5678 is occupied. Keep the same port for later commands. Use `--state /absolute/private/path` to create a distinct instance with its own project/volume. Existing different configurations are preserved and rejected. Before changing a used instance's version/configuration, back up and rehearse restoring its actual volume through a separately reviewed task. This recipe has no destructive remove, upgrade, or credential-export command.

Docker must already be running. The CLI uses a private empty Docker config and explicit existing local Unix socket, without inheriting provider/proxy variables or Docker credentials. It never mounts that socket into containers. The core has only one named data volume, localhost UI binding,2GiB/2CPU caps, no restart policy, no extra Linux capabilities and rotated local logs. Runtime image is fixed by the recorded multiarch digest. Telemetry, update notices, templates, frontend hooks and community-package installation are disabled.

The project bridge allows outbound network access for later deliberately configured integrations. Telemetry switches are not a firewall. The acceptance workflows use no network/provider/API nodes. A Docker29 internal-only network did not publish the localhost port, so it is not used for the UI runtime. Do not expose a public webhook/tunnel or run an imported workflow merely because validation passes; review its effects and authority first.

JavaScript/Python Code nodes require an explicitly configured matching external task runner for appropriate isolation. This minimal route deliberately tests builtin nodes only. It does not add Assistant's privileged Docker-in-Docker sandbox, SearXNG, Postgres, Redis, AI models or providers. These remain task-specific dependencies. n8n can log a missing internal Python runner warning even when no Code node is used; that is not evidence that Python execution works.

Runtime licensing is n8n Sustainable Use License with enterprise exclusions, retained in LICENSE.n8n.md. This is a personal/internal-use setup, not permission to sell unrestricted hosted n8n. No registration or paid license is required for basic Community workflows. Source and image provenance are in SOURCE.json. Upstream server2.47.4 source supports `execute --rawOutput`; the helper verifies returned execution data rather than trusting the CLI's exit code. Internal resume tokens are redacted before synthetic evidence is written.

Trigger source preparation is separate:

```sh
python3 recipes/workflows.py trigger-prepare
```

This verifies the complete pinned4.8.3 Docker subtree and Apache license in private durable storage. It generates no secrets and starts no services. See ../trigger/README.md for the resource and dedicated-engine gates. Trigger4.8.3 matches the existing selected SDK version; research into4.8.4 has not relabeled the installed skill or runtime.
