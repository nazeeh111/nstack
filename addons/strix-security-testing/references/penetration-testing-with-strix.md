# Strix pentest method

Modified by nstack from the pinned usestrix method recorded in [SOURCE.md](../SOURCE.md). This reference prepares or executes a specifically authorized run; it does not activate a runtime during skill installation.

## Choose a feasible runtime

Local Strix runs in a Docker sandbox with a selected model backend. Managed Strix runs on the provider's infrastructure and needs separate account, data and spending authority. Missing Docker or model access does not select cloud automatically. Read the [managed method](managed-pentesting-with-strix.md) only when that route is requested or selected with the user.

For a local route, check executable presence with `command -v strix` and `command -v docker`. An existing, reviewed CLI can later be checked with `strix --version` and `strix --help`; do not execute an unknown binary as a discovery test. Python source installation requires Python 3.12 or newer. Docker must be running, and the first scan normally downloads a sandbox image. Review the exact runtime package, dependency lock and image digest before acquisition. Floating installers and downloading/running a shell installer are not part of this method.

Select the model without changing the user's active host model or effort. A local OpenAI-compatible or Ollama endpoint still needs structured tool calls, sufficient context and adequate resources; compatibility is untested until demonstrated. A remote LLM sends source-derived context to that provider. Existing host subscriptions do not establish a usable or authorized Strix authentication route. Do not read existing account/config stores to discover secrets. Keep Strix MCP connections absent or explicitly task-scoped; configured connections can expose all server tools. Choose the telemetry policy before a run; upstream enables telemetry by default and documents `STRIX_TELEMETRY=0` to disable it.

## Bound the scan

The documented command shape below is an active scan, not a setup check. Replace placeholders only after scope and budget are authorized:

```text
strix -n -t <task-owned-target> --scan-mode quick --scope-mode full --max-budget <approved-USD> --max-turns <per-agent-turns>
```

Use `quick`, `standard` or `deep` to match the task; unqualified mode defaults to deep. `-n` selects headless execution. `--max-turns` applies to each agent, not the whole run. The budget check occurs after responses, may overshoot with in-flight calls and depends on price estimates. Bound provider spending separately when a true ceiling is needed. Interactive mode can extend the budget when resumed, so do not use it for an unattended bounded run.

Targets may be local directories, repository URLs, URLs/domains/IPs, API specifications or target lists. Review ownership and declared hosts, including those an API specification introduces. Local directory targets are mounted writable. Work in an isolated task-owned checkout/copy, and keep the run artifacts with that task. Use `--instruction-file` for non-secret scope/context; do not insert real credentials into CLI arguments or evidence. A live test account requires an approved secret-handling path and its own authorized test scope.

Use `--scope-mode diff --diff-base <actual-base>` only when reviewing changes. Resolve and verify the intended base; a branch's own upstream can yield an empty diff. Use `--workspace-file <path>` for an authorized non-secret support file rather than expanding targets. `--target-list` combines targets, so inspect every entry. Follow long scans in the active task with bounded polling.

## Read actual results

Artifacts under `strix_runs/<run-name>/` include `penetration_test_report.md`, `vulnerabilities/*.md`, `vulnerabilities.json`, `vulnerabilities.csv`, `findings.sarif` and `run.json`. Match the run name, input revision and target scope rather than choosing an arbitrary newest directory.

Headless exit 1 means a fatal error; exit 2 means findings meeting the selected threshold; exit 0 means none proven at that threshold in what was analyzed. Lower-severity findings remain when `--fail-on` is used. A hard budget stop may record `stopped`; a warning-triggered early wrap-up can record `completed` despite partial coverage. Inspect status, errors, cost, target/path coverage and the report together.

Read each claimed finding's request, response, code path and impact. Distinguish proven exploit, plausible observation and untested category. Do not infer no false positives or complete coverage from upstream marketing. Hand an authorized fix to [remediation](fix-security-vulnerabilities-with-strix.md); use [CI drafting](ci-security-scanning-with-strix.md) only for a requested pipeline change.
