---
name: llm-council
description: Run Remy’s actual five-lens LLM Council with five independent advisors, five fresh anonymous peer reviews and a separate synthesis in the active native host.
---

# Remy's LLM Council

This entrypoint preserves the identity of `aiwithremy/claude-skills-llm-council`. It is the five-thinking-style method, separate from Roast Room and Council of High Intelligence.

## Load the actual method

The pinned upstream has no license grant, so its prose is fetched privately rather than republished in nstack. [The private source manifest](private-source.json) pins both complete original files and their SHA-256 hashes. Use the task's selected private source root, or the existing `~/Library/Application Support/nstack/source-packs/remy-council/55ee36e89e0f3f780099ac50332fbb3ec8d14738/` if configured. If absent, a free source-only route is:

    python3 "<this-skill>/scripts/fetch_source.py" /absolute/new/private/source-root

The target's parent must exist. For an existing original checkout, append `--source-dir /path/to/original/repository` to verify/copy without network. This helper fetches immutable source and verifies every file; it installs no runtime, calls no model and reads no credentials. Keep the original prose private. Do not silently substitute an authored summary for a requested source method if acquisition is unavailable.

Read the complete original `SKILL.md` from that private root before executing. Apply the native execution and evidence substitutions below. [Source provenance](SOURCE.json) records the pin and rights. [The method map](references/five-lens.md) makes the sequence inspectable without redistributing its prose.

## Native execution substitutions

Keep the user's active host, selected model and effort. Use actual supported native delegation. In Codex use `spawn_agent` with `fork_turns: "none"`, supplying the neutral question, authorized facts and assigned lens; omit model/effort overrides. Run host-sized waves when five simultaneous children do not fit. Opening answers cannot see each other across waves. Read only task-relevant authorized sources and applicable `AGENTS.md`; the source's Claude workspace/memory scan does not authorize unrelated notes or host memory.

Preserve all five original lenses: Contrarian, First Principles Thinker, Expansionist, Outsider and Executor. Collect five actual independent drafts, then use five **new** reviewer contexts. Preserve the source review's three judgments: strongest answer and why, largest blind spot, and omissions shared by all answers. Do not reuse author contexts or show reviewers the private identity mapping. The source's shared randomized A–E order is the faithful default; randomization does not establish freedom from position bias. The optional helper below is an explicit different order-control method, never a silently substituted source step.

Use a separate fresh native Chairman context for synthesis, with the neutral question, all five actual drafts, restored lens identities and five actual reviews. Preserve convergence, disagreement, omissions, recommendation and one concrete first step. Check decisive source claims independently. Supported uncertainty, a tie or insufficient evidence may qualify a recommendation; do not invent a fatal flaw, suppress evidence of risk or turn agreement into calibrated confidence. The Executor proposes action within existing authority; the method grants no new spending or external-action permission.

Missing/failed outputs remain missing. Reconcile native state before one useful bounded retry; never fabricate a replacement or call an incomplete five-by-five run complete. If independent contexts are unavailable, report that capability gap. A separately requested single-context illustration must be labeled and supplies no independent votes. Use the active host's actual lifecycle tools as detailed in [native execution](references/native-execution.md).

Present the verdict in chat by default, resolving the upstream's contradictory HTML note in favor of its explicit chat-output step and the user's requested artifact. Save a transcript only when requested, in the existing task evidence path. Report actual completed draft/review counts and same-model scope. No headless application, provider transport, credential discovery or service is activated.

## Optional blinded comparison helper

For an explicitly chosen balanced-position or paired-order comparison, read [offline contracts](references/contracts.md). The authored helper preserves current contracts, ties, abstention, malformed/missing-review handling and independent evidence checks:

    python3 "<this-skill>/scripts/blind_review.py" prepare input.json /owned/new-review
    python3 "<this-skill>/scripts/blind_review.py" summarize /owned/new-review reviews.json report.json

Balanced five-by-five covers every presentation position; paired mode checks a critic under reversal. Neither is Remy's exact shared-order peer-review prompt or proof of unbiased judging. Retain the source's three review questions alongside any chosen helper contract. The helper performs no model dispatch or evidence retrieval. Do not add it automatically when the original method meets the request.
