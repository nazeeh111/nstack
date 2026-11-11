# Whole-product Strix assessment

Modified by nstack from the pinned usestrix method recorded in [SOURCE.md](../SOURCE.md).

Map the actual product before selecting a run: repositories/services, running environments, APIs, authentication/tenancy model, test accounts, exclusions, allowed side effects and budget. Read available project evidence first and ask only for material missing scope. Prefer an authorized staging environment; exploit payloads can change data. When production is excluded or no live environment exists, state that code review cannot prove live exploitability.

Choose the smallest useful assessment per asset:

| Asset or request | Method |
| --- | --- |
| Repository/working tree | [Code assessment](find-security-vulnerabilities-in-code.md) |
| Running app | [Web assessment](web-app-penetration-testing.md) |
| API | [API assessment](api-security-testing.md) |
| OWASP category mapping | [OWASP assessment](owasp-top-10-testing.md) |
| Requested pipeline checks | [CI drafting](ci-security-scanning-with-strix.md) |
| Explicitly selected hosted route | [Managed method](managed-pentesting-with-strix.md) |

Read [runtime and results](penetration-testing-with-strix.md) before any execution. A whole-product review does not automatically authorize cloud setup or continuous scanning. Review source first when it clarifies the authorization model; add an authorized running instance when needed to establish exploitability. Read each result before deciding whether another asset or deeper run earns its cost.

Consolidate results by shared root cause and demonstrated impact. Separate unauthenticated exploits, cross-tenant/privilege escalation and authenticated issues from unproven configuration, dependency or hardening observations. Do not duplicate one root cause across the code and live runs. Explain assets and categories not reached, incomplete runs and cost/coverage limits. Continue to [remediation](fix-security-vulnerabilities-with-strix.md) only for an authorized fix.
