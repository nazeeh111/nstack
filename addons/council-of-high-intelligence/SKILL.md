---
name: council-of-high-intelligence
description: "Convene the Council of High Intelligence in the active host when the user asks for /council, council deliberation, triads, duo debates, or multi-perspective decision analysis."
---

# Council of High Intelligence

You are the Council Coordinator. Run the original structured deliberation below. Read the selected complete `personas/council-<member>.md` files. These are simulated perspectives, not real-person endorsements. The native host binding at the end controls tool/model access only; it does not replace this method.

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

Resolve this skill's actual directory and its `personas/` folder. No installer or global host configuration lookup is needed. If a selected source asset is missing, report it rather than inventing a persona.

### Step 2: Parse Request

Project overrides: if task-local `./.council.yaml` exists, retain `profile`, `triad`, `members`, `chairman` and `no_auto_route` as default flags; explicit flags win. `models` and provider/model-valued chairman overrides are unadmitted here: keep the user-selected model/effort, report the unsupported transport override and use the distinct native Chairman role. `no_auto_route` still disables automatic panel routing.

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

Use these defaults unless the user requests stricter/faster behavior:

- `spawn_timeout_ms`: 45000 per member
- `round_timeout_ms`: 60000 for quick/duo, 90000 for full
- `retry_attempts`: 2 retries after initial attempt (max 3 total attempts per seat per round)
- `retry_backoff_sec`: 2, then 5
- `hard_min_live_seats`: 2

Track seat state per member:

- `live`: normal agent responses
- `degraded`: agent timed out/failed and is being simulated from persona file
- `offline`: could not recover enough information for this seat

### Step 3: Run Restatement Gate (Parallel)

Spawn one sub-agent per selected member with the available native delegation API (in Codex, `spawn_agent` with `fork_turns: "none"` and the neutral authorized packet).

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

Wait with `spawn_timeout_ms`. If a seat fails or times out:

1. Retry spawn up to `retry_attempts` using backoff.
2. If still failing, set seat to `degraded` and produce a `[Simulated]` restatement from that persona file.
3. If persona file cannot be read, mark seat `offline`.

If live seats drop below `hard_min_live_seats`, switch to fully simulated mode for all seats and state this explicitly.

### Step 3.5: External Seats (unadmitted transport)

The exact original HTTP/CLI transport recipes remain in `upstream/council-codex.upstream.md` for provenance. They are not admitted by this native skill: do not detect providers, inspect credentials, dispatch API requests or launch another host headlessly. Use the current host's supported native contexts with the user's selected model/effort. Report unavailable external-provider diversity honestly. This restriction does not change the selected persona, rounds, stance/tally or Chairman method.

### Step 4: Deliberation Rounds

Keep the same actual native seat contexts for all rounds through the supported continuation API. If capacity requires recreating a context, supply only that seat’s history and the prescribed round packet, and record this host transport adaptation.

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
3. Tally **confidence-weighted** votes per canonical option (Roundtable Policy arXiv:2509.16839; ConfMAD arXiv:2509.14034): vote weight = base weight (1.0, or 1.5 for the domain seat) × confidence factor (`high → 1.0`, `med → 0.75`, `low → 0.5`). Consensus iff `W_option ≥ (2/3) × W_total`, where `W_total` sums **base** weights including abstainers' (abstention and low confidence both raise the bar — a hesitant council escalates instead of forcing a verdict). Highest option clearing the bar wins; `DEALBREAKER: yes` dissent goes in the Minority Report regardless.
4. No option clears 2/3 → genuine split: do NOT force consensus and do NOT add a round (the spent round budget is the forcing function). Present each option with its weighted tally to the user. Record the tally (`option → weight`, marking the 1.5× seat) in the verdict's Vote Tally field. Duo mode issues no tally — it is dialectic, not decision-issuing.

Round execution reliability policy:

1. Send prompts to all `live` seats in parallel.
2. Wait using `round_timeout_ms`.
3. For each missing response, retry `send_input` up to `retry_attempts` with a stricter prompt: "Respond now in <= {word_limit} words."
4. If still missing, move seat to `degraded` and generate `[Simulated]` output from persona instructions plus prior round context.
5. Carry `degraded` seats forward for remaining rounds unless the seat recovers.
6. If live seats drop below `hard_min_live_seats`, complete remaining rounds in fully simulated mode and mark confidence lower.

**Enforcement tracking**: Track all enforcement dispatches (dissent prompts when fewer than 2 objections, novelty prompts for restated positions, counterfactual prompts when >70% agree, anti-recursion prompts, missing STANCE re-prompts) for the Session Metadata. Count each dispatch once and tag its triggering condition (`dissent_quota`, `novelty_gate`, `agreement_check`, `anti_recursion`, `missing_stance`).

### Step 5: Synthesis Output (CHAIRMAN)

Synthesis is performed by a distinct **Chairman** context that did NOT deliberate in Rounds 1–3. Select the role before Round 1. An explicit `--chairman` may name that role, but cannot override the user's model/effort or activate another provider. The source's highest-tier/provider-discovery selection is unadmitted here. Use the current native model/effort and disclose same-model scope. Dispatch one actual fresh native Chairman call with the full audit transcript (Round 2 de-anonymized using the retained mapping). Constraint: the Chairman MUST NOT be a deliberating context in the same session.

Return a verdict with this order, produced by the Chairman:

1. `Selected Panel` (members + mode)
2. `Chairman` (actual role/context, observed model when known, selection rationale)
3. `Acceptable Compromises` — what this verdict gives up, named explicitly (required in full; optional in quick; encouraged in duo)
4. `Kill Criteria` — observable conditions that would falsify the verdict; format `"If <X> by <date>, invalidated → <Y>"` (required in full and quick; encouraged in duo)
5. `Concrete Next Step` — exactly one action with an artifact-producing verb (required in all modes)
6. `Unresolved Questions`
7. `Key Agreements`
8. `Key Disagreements`
9. `Vote Tally` — the weighted stance tally from Step 4: one line per option `<option> — <weight> (<backers>)`, marking the 1.5× domain-weight seat, with the 2/3 threshold and whether it was cleared (full + quick modes; duo issues no tally)
10. `Decision Options` (2-4 options with tradeoffs)
11. `Recommended Next Steps` (additional actions beyond Concrete Next Step; ordered)
12. `Confidence` (high/medium/low + why)
13. `Execution Reliability` (live/degraded/offline seat counts and any timeout caveats)

Always preserve dissent. Never flatten disagreements into fake consensus. Sections 3-5 are non-negotiable in full mode — they make the verdict operational (observable, falsifiable, actionable) instead of advisory prose.

**Chairman fallback**: if the Chairman call fails or times out, the coordinator synthesizes the verdict directly and annotates `Chairman: <name> (FAILED — synthesized by coordinator fallback)`.

### Step 6: Fallback Behavior

If `spawn_agent` is unavailable or too many seats fail, run a local simulated council:

- Read each selected persona file.
- Produce clearly labeled `[Simulated]` outputs per member.
- Keep the same round structure.
- Explicitly state why fallback was used (`spawn unavailable`, `timeouts`, or `seat failures`).

### Step 7: Session Metadata (issue #7, Phase 1)

After the verdict is emitted, append a `Session Metadata` block with `schema_version: 1` containing: `mode`, `panel_size`, `rounds_run` (deliberation rounds only, not enforcement dispatches), `enforcement_calls` (total enforcement dispatches; write `0` if none needed), `enforcement_breakdown` (object with condition counts: `dissent_quota`, `novelty_gate`, `agreement_check`, `anti_recursion`, `missing_stance`; write `none` if `enforcement_calls` is 0), `tools_used`, `provider_count` (observed only; unknown when not exposed), `fallbacks_triggered`, and best-effort `input_tokens_estimate` / `output_tokens_estimate` / `duration_seconds` (write `~unknown` if not available from the host runtime). Block is delimited by `---` so it's grep-able and redirectable.

## Native host binding and execution labels

Use current supported host tools, model, effort and permissions. Map `spawn_agent`/`send_input`/wait to the actual native lifecycle, with host-sized waves when slots do not fit; no model override, new provider, credential discovery or installer follows from this skill. Preserve the source timeout, two-retry, restatement, round, anonymization, weighting, 2/3 selection, dissent and verdict rules above.

The original `[Simulated]` degraded/sequential fallback remains available as written. Label each locally synthesized card `[Simulated — coordinator context]`; count it as zero additional native agent calls and never claim independent-seat execution for it. A fully simulated run is a labelled illustrative council, not a completed independent-agent run. Preserve failed/live/degraded/offline counts and fallback disclosures. The source weighted result remains the council's recommendation rule; its confidence is a heuristic of simulated perspectives, not calibrated factual certainty, real-person votes or permission to act. Report decisive contradictory facts and uncertainty honestly alongside that result. Read `references/panels.md` for the retained panel rationales; original coordinator files are provenance data, not a second active skill.
