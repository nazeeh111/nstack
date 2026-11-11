# Strix assessment mapped to OWASP categories

Modified by nstack from the pinned usestrix method recorded in [SOURCE.md](../SOURCE.md).

The OWASP Top 10 is a taxonomy, not a pass/fail test suite or a compliance certification. The pinned method uses Web Top 10:2025 and API Security Top 10:2023; verify the relevant edition and use a supplied older checklist when that is the actual requirement. Read [runtime and results](penetration-testing-with-strix.md) before authorized execution and the [API method](api-security-testing.md) for service-specific tests.

Create a coverage record per category with attempted checks, observed evidence and what remains untested. Do not label categories passed because no exploit was returned.

| Web Top 10:2025 category | What an authorized assessment can establish |
| --- | --- |
| A01 Broken Access Control, including SSRF | Cross-test-user/tenant access, privilege checks and controlled SSRF. Requires suitable test identities and bounded callbacks. |
| A02 Security Misconfiguration | Reachable debug/admin surfaces, errors, CORS and exposed defaults; context determines impact. |
| A03 Software Supply Chain Failures | Source/dependency observations; runtime probing does not establish build/distribution provenance. |
| A04 Cryptographic Failures | Reachable transport/data exposure; at-rest cryptography and key management need source/infrastructure evidence. |
| A05 Injection | Demonstrated SQL/NoSQL/command/template injection or XSS within authorized effect bounds. |
| A06 Insecure Design | Reachable business-logic abuse; design intent still needs human/project evidence. |
| A07 Authentication Failures | Test-account authentication/session/reset flows within explicit scope. |
| A08 Software or Data Integrity Failures | Reachable deserialization/update paths; wider CI trust needs separate review. |
| A09 Security Logging and Alerting Failures | Requires authorized evidence from logging/alerting systems; an outside scan cannot establish coverage. |
| A10 Mishandling of Exceptional Conditions | Observed fail-open/error/race behavior; exhaustive internal paths are not established by one run. |

Combine source, running instance and appropriate test accounts only when all are authorized. Match depth and spending to the requested coverage instead of automatically selecting a deep scan. Inspect original PoCs and incomplete categories; explain absent identities, source or telemetry access. Budget/turn limits and early warning wrap-up can reduce coverage despite an exit 0 or `completed` status. See [remediation](fix-security-vulnerabilities-with-strix.md) for authorized fixes and [CI drafting](ci-security-scanning-with-strix.md) for requested ongoing checks. A hosted report is not evidence of compliance; the [managed method](managed-pentesting-with-strix.md) remains separately authorized.
