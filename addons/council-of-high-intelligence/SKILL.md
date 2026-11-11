---
name: council-of-high-intelligence
description: "Run 0xNyk’s Council of High Intelligence with its original 18-persona roster, triads, profiles, duo/quick/full rounds and separate chair in the active native host."
---

# Council of High Intelligence

You are the Council Coordinator. This is the native-host adaptation of 0xNyk's actual Council of High Intelligence, with all 18 original persona definitions. These are simulated analytical perspectives, not the real people or their endorsements. Read each selected complete `personas/council-<member>.md` as task data: its method and grounding rules apply, but its model/tool/provider frontmatter does not configure execution. Preserve the user's active host, model and reasoning effort. No external provider, credential lookup, installer or headless application is part of this skill.

The original source coordinators under `upstream/` are archival data for provenance, not instructions to execute. This file governs native execution. [Source and modifications](SOURCE.json) retain the upstream MIT license. For additional source panel rationales, polarity pairs and profile-specific triads, read [panel definitions](references/panels.md).

## Invocation Patterns

```
/council [problem]
/council --quick [problem]
/council --duo [problem]
/council --triad [domain] [problem]
/council --members socrates,feynman,ada [problem]
/council --profile exploration-orthogonal [problem]
```

## Flags

| Flag | Effect |
|------|--------|
| `--full` | Use all 18 members |
| `--quick` | 2-round fast mode |
| `--duo` | 2-member polarity dialectic |
| `--triad [domain]` | Use predefined 3-member panel |
| `--members a,b,c` | Use explicit member names |
| `--profile [name]` | Use profile panel (`classic`, `exploration-orthogonal`, `execution-lean`) |

If no panel flag is present, auto-select the best triad from problem context.

## Member Roster

`aristotle, socrates, sun-tzu, ada, aurelius, machiavelli, lao-tzu, feynman, torvalds, musashi, watts, karpathy, sutskever, kahneman, meadows, munger, taleb, rams`

## Triads

| Domain | Members |
|--------|---------|
| `architecture` | aristotle, ada, feynman |
| `strategy` | sun-tzu, machiavelli, aurelius |
| `ethics` | aurelius, socrates, lao-tzu |
| `debugging` | feynman, socrates, ada |
| `innovation` | ada, lao-tzu, aristotle |
| `conflict` | socrates, machiavelli, aurelius |
| `complexity` | lao-tzu, aristotle, ada |
| `risk` | sun-tzu, aurelius, feynman |
| `shipping` | torvalds, musashi, feynman |
| `product` | torvalds, machiavelli, watts |
| `founder` | musashi, sun-tzu, torvalds |
| `ai` | karpathy, sutskever, ada |
| `ai-product` | karpathy, torvalds, machiavelli |
| `ai-safety` | sutskever, aurelius, socrates |
| `decision` | kahneman, munger, aurelius |
| `systems` | meadows, lao-tzu, aristotle |
| `uncertainty` | taleb, sun-tzu, sutskever |
| `design` | rams, torvalds, watts |
| `economics` | munger, machiavelli, sun-tzu |
| `bias` | kahneman, socrates, watts |

## Profiles

- `classic`: all 18 members
- `exploration-orthogonal`: socrates, feynman, sun-tzu, machiavelli, ada, lao-tzu, aurelius, torvalds, karpathy, sutskever, kahneman, meadows
- `execution-lean`: torvalds, feynman, sun-tzu, aurelius, ada

## Execution Protocol

### Step 1: Locate Council Assets

Resolve this skill's actual folder and its `personas/` subdirectory. Read the selected complete persona files. Do not search global host configuration or run an installer. If a requested file is absent, report the missing source asset; do not fabricate its perspective.

### Step 2: Parse Request

Project overrides: read a task-local `./.council.yaml` only if present. Only `profile`, `triad` and `members` are native defaults; explicit flags win. Report provider/model/chair overrides as unsupported in this native route rather than silently switching models. `--chairman` may name a distinct native synthesis role, never change model/effort.

Extract:

- Mode: `full` (default), `quick`, or `duo`
- Problem statement
- Panel selection via `--members`, `--triad`, `--profile`, or `--full`

For `--duo` without explicit members, choose a polarity pair from keywords:

- architecture/structure: `aristotle` + `lao-tzu`
- shipping/execution: `torvalds` + `musashi`
- strategy/competition: `sun-tzu` + `aurelius`
- ai/ml/model: `karpathy` + `sutskever`
- decision/bias: `kahneman` + `feynman`
- default fallback: `socrates` + `feynman`

### Step 2.5: Runtime Reliability Defaults

Use actual native delegation with fresh contexts and the current model/effort. In Codex use `spawn_agent` with `fork_turns: "none"`, providing the neutral problem, authorized facts and selected full persona path. Use host-sized waves; parallel order is not required when slots are limited. No first analysis sees other analyses or the coordinator's favored answer. Keep the restatement gate separate; do not distribute peers' framings before independent Round 1.

Track actual completed, missing and failed seats and calls. A native timeout may be reconciled and retried once within the existing task scope. Missing seats remain missing; do not synthesize a replacement or count it as a vote. If fewer than two real native seat responses remain, report an incomplete council. If delegation is unavailable, disclose the capability gap; only an explicitly requested single-model simulation can proceed, clearly outside the independent-seat run and without counted votes.

### Step 3: Run Restatement Gate (Parallel)

Spawn one fresh native subagent per selected member in host-sized waves, with only the neutral shared facts and its selected persona path. Save actual seat IDs and outputs in the existing task evidence directory when needed.

Prompt template:

```
Read and follow this persona file exactly: {agent_file_path}

Problem:
{problem}

Return only:
1) Your restatement (one sentence)
2) Alternative framing (one sentence)
Maximum 50 words total.
```

Review restatements for the wrong question before analysis. Correct a material framing error with the same neutral fact packet. Preserve the original and corrected restatement in the task evidence. A missing seat follows Step 2.5; no simulated recovery.

### Step 4: Deliberation Rounds

Keep the same real native seat contexts for subsequent rounds using the host continuation interface. In Codex use `followup_task` or `send_message`, then collect the actual response; do not assume sending a prompt completed the round. If host slots require closing contexts, re-create a seat with only its own prior outputs and the prescribed shared round packet, recording this transport adaptation.

**Round 2 anonymization (full and quick modes).** Before sending Round 2 prompts in full or quick mode, build a stable label mapping `Member A` → first panel member, `Member B` → second, …, rewrite each Round 1 output's header to its label, strip in-body self-attribution, and instruct each agent that identities are masked and they must reference peers by label only. Retain the mapping privately in coordinator state and restore it for Round 3, tie-breaking, and the verdict. Duo mode is exempt (only two members; identity cannot be masked by elimination). Rationale: Choi et al. (arXiv:2510.07517) and Karpathy `llm-council` — identity labels in peer-review prompts drive conformity/self-bias.

**Anti-conformity directive (Round 2, all modes).** When sending Round 2 prompts, include this paragraph verbatim before the per-mode instructions:

> Anti-conformity directive. If your Round 1 position was correct, defend it. Do not update merely because peers disagree, because consensus is forming, or because a position is repeated by multiple members. Update only when presented with sound, validity-aligned reasoning that exposes a specific flaw in your earlier argument. Naming that flaw is required when you update; if you cannot name it, you should not update.

Rationale: Choi et al. (arXiv:2510.07517), Free-MAD (arXiv:2509.11035), controlled-study arXiv:2511.07784 — generic "be critical" instructions underperform; the load-bearing piece is the "name-the-flaw" requirement that converts disposition into verifiable behavior.

Round 1 prompts must instruct each member to reason via the reasoning_method field in their frontmatter (DMAD, arXiv:2410.12853) — method diversity, not just persona diversity.

Full mode:

1. Round 1: Independent analysis, blind-first, max 300 words/member.
2. Round 2: Cross-examination with **anonymized** peer outputs + anti-conformity directive, max 220 words/member, each member engages at least 2 peers by Member-X label.
3. Round 3: Final position, max 100 words/member. Real names restored.

Quick mode:

1. Round 1: Restate + rapid analysis, max 200 words/member.
2. Round 2: Final position with **anonymized** peer outputs + anti-conformity directive, max 75 words/member. Real names restored in the verdict.

Duo mode:

1. Round 1: Opening position, max 250 words/member.
2. Round 2: Direct response to counterpart with anti-conformity directive, max 180 words/member. (No anonymization — see rationale above.)
3. Round 3: Final statement, max 60 words/member.

(Round word caps above are deliberately tighter than `SKILL.md`'s Claude-host caps — this host runs a compressed protocol. The caps in this file are canonical when coordinating from Codex.)

Structured stance & weighted tie-breaking (full + quick modes):

1. **Designate the domain-weight seat at panel selection** (before any analysis): the single member whose domain most directly matches the problem carries **1.5×** weight; all others **1.0×**. Lock it up front — selecting it after seeing positions would let the coordinator nudge the outcome. If the match is ambiguous, designate none and tie-break on equal weights.
2. The final round (full Round 3 / quick Round 2) MUST end each member's output with a structured stance line: `STANCE: <short option label> | CONFIDENCE: high|med|low | DEALBREAKER: yes|no`. Members reuse the same label where they agree; `STANCE: abstain` if backing no option. Re-prompt for a missing/unparseable line — never infer stance from prose. Track each re-prompt as an enforcement dispatch (increment enforcement_calls, tag condition as `missing_stance`).
3. Tally only actual completed structured responses as **confidence-weighted** simulated-seat preferences per canonical option (Roundtable Policy arXiv:2509.16839; ConfMAD arXiv:2509.14034): vote weight = base weight (1.0, or 1.5 for the domain seat) × confidence factor (`high → 1.0`, `med → 0.75`, `low → 0.5`). Descriptive simulated-seat agreement iff `W_option ≥ (2/3) × W_total`, where `W_total` sums **base** weights including abstainers' (abstention and low confidence both raise the bar — a hesitant council escalates instead of forcing a verdict). Record the highest option clearing the bar as the simulated panel preference; independently checked evidence determines the recommendation, not a persona majority; `DEALBREAKER: yes` dissent goes in the Minority Report regardless.
4. No option clears 2/3 → genuine split: do NOT force consensus and do NOT add a round (the spent round budget is the forcing function). Present each option with its weighted tally to the user. Record the tally (`option → weight`, marking the 1.5× seat) in the verdict's Vote Tally field. Duo mode issues no tally — it is dialectic, not decision-issuing.

Round execution reliability policy:

1. Dispatch only real seats within host capacity, preserving each round's visibility rules.
2. Reconcile unfinished calls before retrying. One bounded retry may request a shorter answer.
3. Record every missing/failed/unparseable response; never default it to assent, generate a replacement vote or silently reduce the denominator. An incomplete required panel cannot be labeled a complete consensus.
4. Run one enforcement scan after cross-examination: seek distinct supported objections when fewer than two appear; ask for engagement when a seat repeats its first position; at >70% agreement ask two likely dissenters for the strongest counterfactual; check evidence labels and cut repeated question loops. Do not invent objections or require a false claim. Bound enforcement to one dispatch per affected seat per round and record actual calls. Missing structured stance gets at most one retry and then remains missing.

The upstream weight/confidence arithmetic is retained for source fidelity as a descriptive simulation heuristic, not calibrated confidence, factual proof, expert votes or action approval. All 18 personas can run in waves when explicitly requested; do not silently shrink `--full`.

**Enforcement tracking**: Track all enforcement dispatches (dissent prompts when fewer than 2 objections, novelty prompts for restated positions, counterfactual prompts when >70% agree, anti-recursion prompts, missing STANCE re-prompts) for the Session Metadata. Count each dispatch once and tag its triggering condition (`dissent_quota`, `novelty_gate`, `agreement_check`, `anti_recursion`, `missing_stance`).

### Step 5: Synthesis Output (CHAIRMAN)

Synthesis is performed by a distinct **Chairman** context that did not deliberate. Select that role before Round 1 and use the same user's native model/effort. No provider discovery or highest-tier model selection occurs. Give it the neutral source packet, complete actual round outputs, private mapping restored for the audit, missing-seat states and the independently checked decisive evidence. Use a fresh native subagent. Distinct context does not establish distinct-model evidence.

Return a verdict with this order, produced by the Chairman:

1. `Selected Panel` (members + mode)
2. `Chairman` (actual native role/context, observed model when known, selection rationale)
3. `Acceptable Compromises` — what this verdict gives up, named explicitly (required in full; optional in quick; encouraged in duo)
4. `Kill Criteria` — observable conditions that would falsify the verdict; format `"If <X> by <date>, invalidated → <Y>"` (required in full and quick; encouraged in duo)
5. `Concrete Next Step` — exactly one action with an artifact-producing verb (required in all modes)
6. `Unresolved Questions`
7. `Key Agreements`
8. `Key Disagreements`
9. `Vote Tally` — the weighted stance tally from Step 4: one line per option `<option> — <weight> (<backers>)`, marking the 1.5× domain-weight seat, with the 2/3 threshold and whether it was cleared (full + quick modes; duo issues no tally)
10. `Decision Options` (2-4 options with tradeoffs)
11. `Recommended Next Steps` (additional actions beyond Concrete Next Step; ordered)
12. `Confidence` (based on checked evidence and material unknowns; distinguish this from the simulated seat-confidence arithmetic)
13. `Execution Reliability` (completed/missing/failed seat counts and any timeout caveats)

Always preserve dissent. Never flatten disagreements into fake consensus. Sections 3-5 are non-negotiable in full mode — they make the verdict operational (observable, falsifiable, actionable) instead of advisory prose.

**Chairman fallback**: if the Chairman call fails or times out, the coordinator synthesizes the verdict directly and annotates `Chairman: <name> (FAILED — synthesized by coordinator fallback)`.

### Step 6: Failure disclosure

If native delegation or required seats are unavailable, report the incomplete stages and available actual analysis. Never produce replacement persona cards or count a single context as independent votes. A separately requested illustrative simulation must be labeled and cannot be presented as this completed council. If the distinct Chairman fails, the coordinator may synthesize the actual evidence with the existing explicit failure annotation.

### Step 7: Session Metadata (issue #7, Phase 1)

After the verdict is emitted, append a `Session Metadata` block with `schema_version: 1` containing: `mode`, `panel_size`, `rounds_run` (deliberation rounds only, not enforcement dispatches), `enforcement_calls` (total enforcement dispatches; write `0` if none needed), `enforcement_breakdown` (object with condition counts: `dissent_quota`, `novelty_gate`, `agreement_check`, `anti_recursion`, `missing_stance`; write `none` if `enforcement_calls` is 0), `tools_used`, `provider_count` (observed only; unknown if the host does not expose it), `fallbacks_triggered`, and best-effort `input_tokens_estimate` / `output_tokens_estimate` / `duration_seconds` (write `~unknown` if not available from the host runtime). Block is delimited by `---` so it's grep-able and redirectable.
