---
name: cloudflare-security-audit
description: Apply Cloudflare's source-grounded code security review method with explicit coverage, independent validation and structured findings. Use for a requested source-code security review or audit needing this method, not Cloudflare account administration.
---

# Cloudflare Security Audit

Find concrete failures across a real trust boundary, establish the strongest visible preventing controls, and report only the observed impact. This native adaptation retains the pinned [original operational contract](upstream/ORIGINAL-SKILL.md), complete domain prompts, schema and offline validators. [Source provenance](SOURCE.json) identifies unchanged files and native differences. It adds no provider, account connection, scanner service or sandbox.

## Mode and authority

For a focused question, source review or finding investigation, use the relevant method in guidance mode. Loading this skill does not start the full workflow, create audit artifacts or authorize a target. Use the full six-phase workflow only for an explicitly requested codebase audit, comprehensive review or report artifacts. Resolve material ambiguity before starting that work; continue independent source inspection within the request.

Preserve the selected host, model and effort. `Task tool`, `research`, `general` and `subagent_type` in the original mean native delegation capabilities and conceptual roles, not a particular vendor API. Use authorized fresh contexts for independent checks. Same-model independent review does not establish model diversity. No new provider billing, credentials, live traffic, account operation or target mutation follows from this method.

## Native scheduling and output differences

Read the original contract before a full audit. Its evidence, coverage, verdict, write-isolation, sandbox and independent-review rules apply. These explicit native differences replace only its scheduling and default output instructions:

- Cover all four reconnaissance lenses: product/stack/local operation; principals/authority/controls; entry surfaces/copies/sinks; local execution/deployment visibility. The parent may inspect them together or sequentially, or delegate distinct work when useful. The original four baseline reconnaissance agents and four-call budget minimum are not mandatory native fanout.
- Plan actual calls and remaining coverage, then reserve fresh coverage critics and independent candidate/final-record verification before hunting. Adapt hunter count and concurrency to boundaries, available contexts and the user's budget. Keep the original quick/standard/deep coverage and verification distinctions. A fixed team size is not a coverage claim, and less fanout never lowers the evidence bar.
- Preserve fresh independent candidate verification and coverage critics. For quick, one fresh verifier may perform both candidate and final-record checks as the original permits. Other profiles keep the final verification separate. Material record replacements require another independent verifier. A hunter cannot verify its own claim. If independence or a strict budget prevents required work, record an incomplete audit and exact gaps; do not substitute serial self-review or invent verifier results.
- Put retained audit outputs in the current task's authorized, owned, non-synced evidence directory outside the target. Use an in-target directory only when explicitly selected and verified ignored by version control. Resolve an owned external path when necessary. Do not automatically create the original home-directory default or use a shared temporary directory as an execution fallback. Disposable builds and fixtures belong only in the assigned scratch area.

The parent alone owns shared metadata, architecture, coverage ledger, findings and reports. Give each delegate its unique scratch root; preserve source and unrelated work. Record source revision and dirty state, scope/profile, selected domain blocks, actual planned/spent calls, owners and incomplete reasons in the task's audit metadata. Count actual reconnaissance calls instead of the original fixed reserve; preserve user-set limits and all critic/verification reserves.

## Execution boundary

Source inspection is read-only. Before executing any target-controlled build, test, process, browser, emulator, fuzzer or fixture, verify every original OS-enforced control: no external network; empty allowlisted environment with scratch-local home/caches; read-only source and toolchain; scratch-only writes; explicit low CPU, memory, process, file-size, disk and wall-clock bounds. Separate agents and permission prompts do not establish this sandbox.

Retained execution evidence also requires the original parent-side descriptor-safe promotion procedure, including no-follow traversal, exclusive destination creation, single-link regular files, bounded reads and identity checks after all target processes terminate. Read that complete procedure in the original contract and include it in hunter/verifier prompts as directed. If any required execution or promotion control is unavailable, do not run target code or promote its files. Preserve the exact `needs_validation` blocker and safe resolution plan. Use dummy data only; do not fetch target dependencies or inspect credential stores.

## Full workflow

1. Read [reconnaissance and deterministic coverage](upstream/RECONNAISSANCE.md). Establish all four lenses, source state, prior evidence and canonical ledger units. Apply the native scheduling differences above. Treat stale, deferred and blocked work as current gaps.
2. Read [hunting and coverage critics](upstream/HUNTING.md) and [attack-class selection](upstream/ATTACK-CLASSES.md). Read selected domain companions when their source-visible boundary applies. Supply exact selected blocks, controls and source scope to hunters. Preserve fingerprints, explicit exclusions, owned evidence and per-unit dispositions. Keep the profile's critic passes and disclose unfinished coverage.
3. Read [candidate validation and reporting](upstream/VALIDATION-AND-REPORTING.md). Independently challenge each candidate's current source trace, preventing layers, affected principal/resource and minimum bounded result. Keep blocked hypotheses distinct from disproved claims.
4. Read [the schema](upstream/report-schema.json) immediately before producing findings. Only `confirmed` receives severity and requires complete bounded observed evidence; `needs_validation` has exact blockers and no severity; `rejected` preserves a refuted claim. Validate parent-owned JSON after the relevant updates:

       node "<skill-dir>/upstream/validate-findings.cjs" "<output-dir>/findings.json"
       node "<skill-dir>/upstream/validate-coverage-ledger.cjs" "<output-dir>/coverage-ledger.json"

5. Verify final records with fresh independent eyes as the profile requires. Independently verify material replacements, then rerun both validators. Missing independent disposition leaves a ledger candidate and incomplete run, not a finding.
6. Derive the original `REPORT.md`, `FINDINGS-DETAIL.md` and `NEEDS-VALIDATION.md` from verified records and the ledger. State scope, source, actual checks, dissent, prior-run use and deferred/out-of-scope gaps. Finish with validated artifacts or an explicit incomplete status and exact reason.

Validators need an existing Node runtime and OS no-follow/nonblocking file support; they install nothing. Their success proves document shape and internal ledger state rules. Separately check actual source claims, block references, artifact provenance, independence and findings-to-ledger links. Neither a clean report, consensus nor schema success proves that the target has no vulnerabilities.
