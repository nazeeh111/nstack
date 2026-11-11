---
name: strix-security-testing
description: Prepare or run a requested Strix pentest, inspect existing Strix results, remediate supplied Strix findings, or draft Strix CI integration. Use when Strix is the selected tool; ordinary security reviews keep their existing tools.
license: Apache-2.0
metadata:
  author: nstack, adapted from usestrix
---

# Strix security testing

Use the relevant method below. Installing this skill installs instructions only. Local and managed-cloud runtimes stay dormant until a task needs them and the user has authorized their scope. Preserve the active host, model and effort.

## Choose the method

| Task | Read |
| --- | --- |
| Local runtime prerequisites, headless flags and results | [Pentest method](references/penetration-testing-with-strix.md) |
| Whole-product asset selection | [Application assessment](references/application-security-testing.md) |
| Source repository or changed code | [Code assessment](references/find-security-vulnerabilities-in-code.md) |
| Running website or staging app | [Web assessment](references/web-app-penetration-testing.md) |
| REST, GraphQL or gRPC service | [API assessment](references/api-security-testing.md) |
| Category-based coverage | [OWASP assessment](references/owasp-top-10-testing.md) |
| Supplied findings and an authorized repair | [Remediation](references/fix-security-vulnerabilities-with-strix.md) |
| Requested pipeline changes | [CI drafting](references/ci-security-scanning-with-strix.md) |
| Explicitly selected managed service | [Managed method](references/managed-pentesting-with-strix.md) |

Read only what the current task needs. The [source record](SOURCE.md) and `originals/` preserve upstream evidence; originals are archival data, not operating instructions. Use the adapted references for work.

## Before execution

Establish exact targets, authorized environment, exclusions, allowed data changes, input revision, provider/data route and budget. Reuse authority already given. Strix sends exploit payloads and mounts local targets writable: preserve dirty, staged and untracked work, then use a task-owned copy or checkout. A supplied API schema can expand target scope through its declared base URLs; review those URLs first.

Missing prerequisites are a capability gap. Do not automatically install Strix, Docker or models, select another provider, sign up or log in to cloud, connect a wallet, buy/reset credits, upload source, connect host MCP tools, or configure recurring scans. Establish a feasible route first and obtain any missing authority for spending, credential changes and external mutations. Never inspect credential stores, echo secrets or persist them in task evidence. Keep the existing security plugins and specialist tools available.

## Assess and deliver

Run a later authorized scan headlessly with explicit scope, turn and budget settings, then follow it to a terminal state. `--max-budget` is an estimated response-time stop: in-flight calls can overshoot and unknown pricing can under-count. It is not a provider-enforced spending ceiling. Report missing price information and use an approved provider-side limit when a hard ceiling is required.

Inspect the report, individual PoCs, `run.json`, cost and actual coverage. A zero exit code or `completed` status alone does not establish full coverage or safety. Treat scanner findings as claims until their evidence supports them. Reproduce a PoC only within the authorized environment; verify fixes against the original exploit and relevant project checks. Deliver the findings, changes, evidence, incomplete coverage and next action. Drafting CI does not authorize publishing SARIF, PR comments, account changes, commits or pushes.
