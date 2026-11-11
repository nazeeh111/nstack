# Strix code assessment

Modified by nstack from the pinned usestrix method recorded in [SOURCE.md](../SOURCE.md).

Use Strix for a requested source-assisted assessment of an identified repository, service or diff. Read [runtime and results](penetration-testing-with-strix.md) before execution. Do not replace an ordinary code/security review with an active pentest merely because this reference is available.

Inspect Git state and preserve actual dirty/staged/untracked bytes. Strix mounts local targets writable, so scan a task-owned copy or checkout. Capture its source revision/hash and identify the authorization model, routes, dangerous sinks, tenant boundary and attacker-controlled inputs. Focus a monorepo on the relevant service. If a running app is separately authorized, combine source and its reachable test URL; Docker Desktop commonly exposes host services through `host.docker.internal`. Do not start or touch a live service without the task's authority.

For changed code, resolve the actual base branch/commit and verify it exists. Do not assume `origin/main`, compare with the current branch's own upstream, or silently fall back to only the last commit. An empty or unresolved diff is an incomplete review, not a clean result. See [CI drafting](ci-security-scanning-with-strix.md) when pipeline behavior is requested.

Source alone can suggest a vulnerability but may not establish exploitability. Inspect each finding's code location, input path, authorization checks and PoC impact. A response status or scanner assertion is insufficient by itself. Read the exact run artifacts and note unreviewed paths, errors and budget/turn stops. This method complements dependency and secret scanners; it is not an exhaustive inventory of known vulnerable packages or exposed credentials. Never extract or print live secrets as proof.

For an authorized patch, use [remediation](fix-security-vulnerabilities-with-strix.md). Cloud upload is a distinct disclosure decision covered by the dormant [managed method](managed-pentesting-with-strix.md), not a fallback for unavailable local tools.
