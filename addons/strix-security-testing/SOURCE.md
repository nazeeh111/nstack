# Strix source and modifications

This is a nstack adaptation of [usestrix/strix](https://github.com/usestrix/strix/tree/685bbc8138d35fc9fe378ac37ec0d9198b9c46a3), pinned at `685bbc8138d35fc9fe378ac37ec0d9198b9c46a3` (release 1.7.1), reviewed 2026-11-10. Upstream is Apache-2.0, Copyright 2025 OmniSecure Inc. The complete [LICENSE](LICENSE) is preserved byte-for-byte. No upstream NOTICE file was present in this snapshot. No endorsement or product trademark rights are implied.

[SOURCE.json](SOURCE.json) maps every upstream consumer skill path and SHA-256 to its byte-exact `originals/<method>.md` archive and adapted `references/<method>.md` path/hash. It also records immutable supporting-document URLs/hashes and the finished package file inventory. Originals retain their original frontmatter and content for comparison; their `.md` names prevent extra SKILL.md discovery. **Originals are archival source data, not operating instructions.** Read them only to audit provenance or compare a change. All operating methods are under `references/` and subject to this package's entrypoint.

## Modifications by nstack, 2026-11-10

- Added one narrow `strix-security-testing` entry; nine broad upstream discovery entries become relative method references, with no nested SKILL.md files or runtime helpers.
- Rewrote sibling-skill instructions as relative reference links and retained the nine methods: runtime/results, application, source, web, API, OWASP, remediation, CI and managed service.
- Removed automatic cloud fallback, account/credential setup, wallets, credit purchases/automatic top-ups, source uploads, floating installers and unrequested external integration/notification/schedule actions. Local and managed runtimes remain separately selected, authorized and dormant.
- Preserved target-specific methods and operational limits: writable source mounts, test-identity/tenant comparisons, schema-declared hosts, real diff bases, actual report/PoC evidence and incomplete coverage. Replaced blanket claims of no false positives or complete validation with evidence checks.
- Corrected the consumer skill's hard-spend-cap shorthand using the pinned CLI reference: budget estimates are checked after responses, can overshoot and can under-count. A provider-side limit is needed for a genuine hard spending ceiling.
- Kept model/effort, host credentials/MCP connections and existing security specialists independent. Secret rotation/history rewrites, real scans, cloud changes, paid calls, SARIF publication, comments, commits and pushes require their own task authority.

No upstream runtime, internal `strix/skills` prompt packs, service, dependency, Docker image, account or provider connection is distributed or activated here. Normal skill discovery stays enabled; using the instructions does not itself authorize execution. Source review and package checks do not establish scanner effectiveness.

For runtime details, consult the pinned support sources recorded in SOURCE.json. Recheck mutable pricing, entitlements, editions and dependencies before a future real runtime task. Do not follow the archived floating installation/payment commands as instructions.
