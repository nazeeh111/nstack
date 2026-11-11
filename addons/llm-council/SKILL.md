---
name: llm-council
description: "Run Remy’s original five-lens council: independent drafts, anonymous fresh peer reviews, Chairman verdict and optional transcript."
---

# Remy's LLM Council

This is `aiwithremy/claude-skills-llm-council` at `55ee36e89e0f3f780099ac50332fbb3ec8d14738`, separate from the two persona councils. The upstream has no license grant, so its complete original `SKILL.md` and `README.md` stay private. [The manifest](private-source.json) pins their bytes. Use the task-selected source root or `~/Library/Application Support/nstack/source-packs/remy-council/55ee36e89e0f3f780099ac50332fbb3ec8d14738/`. If absent, the free source-only recipe is:

    python3 "<this-skill>/scripts/fetch_source.py" /absolute/new/private/source-root

The parent must exist; `--source-dir /path/to/original/repository` verifies an existing checkout without network. The recipe installs no runtime and reads no credentials. Missing source is a capability gap, not permission to substitute a summary.

**Read and follow the complete original `SKILL.md`, including its advisor/reviewer/Chairman prompts, word limits, recommendation, output and transcript rules.** The following are execution bindings only; do not rewrite its lenses, tone, decision procedure or core method. [The method map](references/five-lens.md) is informational, not a replacement.

## Native host bindings

- Use the active host's supported tools and retain the user's model/effort. Map Claude/Glob/Read/subagents to their native equivalents. In Codex use `spawn_agent`, `fork_turns: "none"`, the framed question and assigned source lens; no model override. Use native continuation/wait tools. When five children cannot fit, use host-sized waves without sharing earlier drafts. Keep all five original drafts and five new anonymous reviewers; the Chairman is a separate fresh context. Report missing calls honestly; do not invent a completed five-by-five session.
- Context enrichment uses relevant authorized project files and supplied facts. `CLAUDE.md` means applicable project instructions such as `AGENTS.md`; do not inspect unrelated notes, generated host memory, accounts or credential stores. Keep the source neutral framing and perspective-specific prompts unchanged.
- Preserve the original shared randomized A–E review order and its three judgments. Preserve the direct Chairman recommendation and one first action, with the source right to disagree with the majority. Agreement is an analytical heuristic, not calibrated factual confidence or real expert endorsement; report actual execution mode and uncertainty honestly without replacing the source method with a different scoring or evidence framework.
- Follow the original chat-verdict step and optional transcript rule, including significant decisions worth referencing later. Save only to a task-owned project location, never the immutable skill. The source’s final HTML note conflicts with its explicit chat-only step; use the explicit step unless the user requests another artifact. No HTML service, provider transport, new credential or paid runtime is activated.

## Optional distinct comparison helper

Only when the user explicitly selects a balanced-position or paired-order comparison, read [contracts](references/contracts.md) and use the authored offline helper. It is a separate comparison utility, not Remy's default review protocol:

    python3 "<this-skill>/scripts/blind_review.py" prepare input.json /owned/new-review
    python3 "<this-skill>/scripts/blind_review.py" summarize /owned/new-review reviews.json report.json

The helper calls no model and retrieves no evidence. Keep its existing ties, abstention, malformed/missing-result and independent-evidence contracts when that distinct comparison is selected. [Source and rights](SOURCE.json) identify the original and these bindings.
