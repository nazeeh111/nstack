# Strix web application assessment

Modified by nstack from the pinned usestrix method recorded in [SOURCE.md](../SOURCE.md).

Before a live run, identify the authorized URL, environment, permitted actions, exclusions and rate/time/spending bounds. Prefer staging when available. Exclude real payment, mass notification, destructive admin and third-party identity paths unless the user specifically includes them. Do not infer third-party authorization from a linked domain.

Read [runtime and results](penetration-testing-with-strix.md). Establish an approved path for test accounts without putting credentials into command history, plaintext task artifacts or reports. Two seeded accounts in different tenants enable meaningful cross-account access tests; low/high privilege accounts enable vertical authorization tests. Do not substitute real account data for missing fixtures. Without accounts, describe the reachable anonymous surface and its limits.

Source-assisted testing can expose authorization and business-logic paths that crawling misses. Add source or `http://host.docker.internal:<port>` only when those targets are within the authorized scope. Choose scan depth to match the task and use explicit turn/budget settings; budget estimation is not a guaranteed spend ceiling.

Read the actual report and per-finding evidence. Replay an exploit only if its effects remain authorized; confirm what changed or what data was accessible. Check `run.json`, cost and actual path coverage before interpreting an empty result. A `completed` status can still accompany warning-triggered partial coverage. Use [remediation](fix-security-vulnerabilities-with-strix.md) for requested fixes and [CI drafting](ci-security-scanning-with-strix.md) for a requested pipeline change. The [managed method](managed-pentesting-with-strix.md) stays dormant unless selected with separate data/account authority.
