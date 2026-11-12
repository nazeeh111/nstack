# On-demand AI application workflows

This integration provides a real, isolated Python runtime for explicitly requested applications. It does not add a host agent, automatic tracing, memory service or provider account.

The locked Linux arm64 image contains Python3.12.16, LangChain1.5.0, LangChain Core1.8.0, LangGraph1.2.20 and SQLite checkpoint3.1.3 with42 exact wheel hashes. `SOURCE.json` records official release commits, wheel URLs/hashes and base-image manifests. The wheels are official registry artifacts; this is not a reproducible build from Git source. The Python base pin is a multi-platform official manifest, while this dependency lock supports **Linux arm64 only**.

Use LangGraph when a produced application needs explicit branching, durable state and human pauses. Add LangChain when its agent/tool/middleware interfaces help the application. Ordinary Codex/OpenCode work and Obsidian notes continue through their existing tools. No provider integration extra is installed. [LangSmith](langsmith/README.md) is available on demand through its pinned SDK and local tracing/evaluation example; hosted tracing is disabled.

From the nstack repository:

```sh
python3 recipes/ai_workflows.py install
python3 recipes/ai_workflows.py verify
python3 recipes/ai_workflows.py check
python3 recipes/ai_workflows.py run --project /absolute/approved/project --script relative_script.py
```

The script sees `/project` read-only and its unique output directory as `/work`. It has no network. Inputs must be an explicitly selected real project directory and an existing unlinked relative Python script. The home root, settings, credential locations, Knowledge vault and private runtime state cannot be project mounts. The wrapper never mounts a Docker socket inside a container. This is an offline application template, so online model execution is outside its interface.

`install` explicitly fetches the immutable official Python image and hash-verified wheels, then builds with network disabled. It never changes global Python packages or Docker VM settings. New versions are staged separately; failed preparation logs are retained and older valid versions are preserved. Repeated installation verifies and reuses the exact runtime without resolving upgrades. Existing Docker CLI/daemon are required. Select another existing local endpoint with `--docker-host unix:///absolute/socket` before the command; remote daemons are unsupported.

All output, source copies, wheels, logs, receipts and a durable private image archive live beneath `$NSTACK_STATE/native-tools/ai-workflows/<fingerprint>/`, defaulting to the user's local nstack state. Docker also retains its normal private image store. No credentials or proxy settings are inherited into containers or the isolated Docker client. Every CLI invocation uses a fresh empty Docker configuration, without reading an existing credential store. `verify` checks source/lock/wheel/archive identities and the actual local image ID before execution. The pinned image archive can be restored using Docker's image-load operation and the recorded image ID/tag if the daemon image store is later lost; restoration is an explicit action.

Each invocation creates a unique owned container, inspects its configuration before startup, and removes only that exact owned container afterward. It enforces network-none, no published ports, a read-only root, dropped capabilities, no-new-privileges, a1CPU/1GiB/128-process limit and temporary scratch space. The current user's numeric UID/GID owns its output. Runtime images and data remain for reuse; no global prune or volume deletion occurs.

`check` uses a fixed local function implementing the chat-model interface. It performs **no AI inference**. It checks a deterministic LangChain tool call and invalid typed input, persists a LangGraph interrupt, crashes after a SQLite effect commits, then resumes in another new container and requires exactly one effect. A deliberately wrong expected result must fail. Every successful phase confirms version pins and a denied external connection. Inspection/log/checkpoint evidence stays in the unique private run directory. These checks prove the tested offline application behavior, not provider output quality or every possible replay pattern.

For licenses, upstream LangChain/LangGraph MIT notices are retained next to this file. Installed wheels retain their own license files. Third-party licenses remain independent of nstack and LangChain's MIT license.

## Optional Langfuse

`langfuse/compose.json` is a prepared **stopped** six-component observability profile, derived from the exact retained upstream Compose and release recorded in `langfuse/SOURCE.json`. It is a separate service for an application that needs searchable traces, scores and comparisons. It does not collect native Codex/OpenCode chats, API keys, environment dictionaries or vault contents.

The profile pins web/worker, Postgres, Redis, ClickHouse and MinIO by immutable manifests. The beta AI Gateway is omitted. All image routes were anonymously pulled on Linux arm64 during acceptance. The initial MinIO401 was the standard OCI Bearer challenge; a temporary anonymous token resolved it without an account. No token is retained in provenance or configuration.

The current8GiB Docker VM has **not** run this stack. Official Compose trial guidance suggests4cores/16GiB, while the current per-component sizing table totals25.5GiB with local object storage. The profile has not passed startup, auth, trace-ingestion, backup/restore or memory acceptance. Image pulls and Compose validation do not establish those outcomes. No VM configuration change is part of this integration.

Its intended later startup requires explicit project commissioning and fresh private development secrets for `POSTGRES_PASSWORD`, `CLICKHOUSE_PASSWORD`, `REDIS_AUTH`, `MINIO_ROOT_PASSWORD`, `SALT`, `ENCRYPTION_KEY` and `NEXTAUTH_SECRET`. No default secrets are supplied or generated now. A local test user/project also needs initialization before trace API use. Do not create a remote account or reuse a real provider/host credential. Keep any later environment file private outside the public repository, with its own backup/restoration plan. Use a unique explicit Compose project name and set `NSTACK_STATE` to the private local nstack root. The bind data directories are scoped under that root and project name. They must be explicitly prepared with appropriate service ownership; `create_host_path: false` prevents accidental directory creation.

Only web `127.0.0.1:3100` and object-upload `127.0.0.1:9190` are published. Databases, Redis, worker and MinIO console have no host ports. An internal network blocks container external egress; telemetry, Halo, signup onboarding and Gateway activation are off. The browser may still attempt optional external assets, so fully offline UI acceptance also needs browser egress controls. Restart is `no`, logs rotate, and private bind data persists. Stop only the selected project and preserve its data; do not use routine `down -v` or prune.

A later trace test should send only an allowlisted synthetic event and deterministic score, query it back, reject unauthenticated calls, verify a fake sensitive canary is absent before transmission and after storage, then restart and measure resource use. Redact before SDK calls. Export masking does not cover every field/exporter, and EE server masking is not a privacy boundary for this free route. No automatic tracing is enabled here.

Langfuse's core is MIT; designated EE directories use commercial terms. Other image components have their own licenses: the observed Redis7.4.12 source is RSALv2 or SSPLv1, PostgreSQL17.11 uses the PostgreSQL License, and MinIO identifies AGPLv3. ClickHouse is Apache2.0 upstream, but an exact image-to-source Git revision was not established in this scoped review. Source references and limits are in `langfuse/SOURCE.json`. No EE feature or separately billed route is activated. Future provider calls, embeddings, model judges, hosted tracing or cloud services need separate explicit scope and spending authority. Existing ChatGPT/Codex sign-in is never extracted into an application API key.
