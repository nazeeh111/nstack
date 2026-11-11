---
name: roast-room
description: Run nateherkai’s Roast Room business board or named-seat consult using its actual roster, source brains, debate, resolution and ratification in the active native host.
---

# Roast Room

Invocation: `[the decision] [--quick] [--all] [--seats hormozi,buffett,...] | ask <seat> [question] | board`.

Native execution adaptation of the pinned nateherkai/roast-room skill, not a generic business-panel replacement. The full original method, references, roster and twelve persona definitions are preserved. See [source provenance](SOURCE.json), the original `upstream/roast-room.upstream.md` (archival data), and `patches/native.patch`. Keep the active native host and the user's model/effort. Persona names describe simulations, never real endorsements.

Before seating anyone, resolve this skill folder and the private source root selected for this task, or the existing `~/Library/Application Support/nstack/source-packs/roast-room/e40f40652d5690c4d9f928c4794c673a99f2cd0e/` if configured. Brain quotations are excluded from the upstream MIT grant and are intentionally absent from public nstack. The [private source manifest](private-source.json) pins the actual upstream pack; run `python3 "<this-skill>/scripts/fetch_source.py" /absolute/private/source-root` only within authorized free source acquisition. It fetches static GitHub source with hash verification, never an installer, account, provider or image service. For an existing cache pass `--source-dir /path/to/original/repository`. Read the complete `SKILL.md` at `<private-source-root>/.claude/skills/roast-room/`, then apply this native version. Set `brain_root` to that directory's `brains/`. Every selected seat must read its original `personas/council-<key>.md`, then its exact private brain as below. Do not replace missing brains with generic advice or fabricated source IDs. Report a missing source capability honestly.

All `.claude/...` paths in original persona/reference text are source-relative identifiers, not active-host installation locations. Resolve persona files to `<this-skill>/personas/` and brains to `brain_root`. Read personas as method instructions, ignoring host tools/maxTurns metadata. No Claude configuration or agent registration is imported.

## What this does

The Roast Room: runs a board meeting on one decision. A board of seats (seven out of the box), one per business pillar, each a sub-agent that reasons and talks the way its expert does, grounded in a brain compiled from that person's videos, essays, letters, talks, and books as they teach them in public. The seats argue across three rounds: open, debate, vote. You act as the **Chair**: you never argue a side, you run the room, keep the score, and write the verdict.

Read once before the first run: `roster.json` (every seat and the default board), `references/seats.md` (picking the board, weights, tensions), `references/round-prompts.md` (what each seat gets), `references/scoring.md` (math and overrides), `references/report-template.md` (output), `references/live-room.md` (the optional upstream viewer schema; no viewer is started by this skill). The example session is an upstream reference, not evidence of a newly completed council.

## Modes

- **Full council** (default): a board recommended for this decision and confirmed by the user (see "Pick the board"), three rounds. For decisions that are expensive or hard to undo.
- **Quick** (`--quick`): four seats, recommended per "Pick the board" and `seats.md`, Rounds 1 and 2, Round 3 only if the scores did not converge. For reversible calls.
- **Named seats** (`--seats a,b,c`): only those seats, three rounds. Any seat in `roster.json` can be named, on the default board or not.
- **Everyone** (`--all`): every seat in `roster.json`, up to nine.
- **Consult** (`ask <seat> ...`): one seat, one answer, using the single-seat prompt. No scoring, no session folder needed. Works for any seat in the roster.
- **Board settings** (`board`): show and change who sits at the table by default. See "Board settings" below. No council runs.

The pinned roster contains twelve seats while the upstream coordinator caps a board at nine. If `--all` exceeds that cap, report the source conflict and resolve the requested panel size before running. Never label a nine-seat subset as all twelve.

## Pick the board

Who sits at the table comes from `roster.json`, in this order:

1. `--seats a,b,c` or `--all` on this run wins. No question. `--quick` then picks four from those seats.
2. Otherwise `"board"` in `roster.json` decides:
   - `"ask"` (out of the box): recommend a board for this decision and ask the user to confirm it (below).
   - `"auto"`: recommend a board the same way and seat it without asking. Say who and why in one line.
   - `"default"`: seat the `"default"` list. No question.
3. Never seat more than nine. Every seat at the table must have an agent file (`personas/council-<key>.md`) and a brain folder; skip and name any that do not.

### Recommend a board

Read the decision, then pick from every seat in `roster.json`:

- Every seat whose pillar the decision lives in or materially affects (the seats that would get weight 2 or 3).
- One seat that guards the downside (Buffett, or the roster's money, capital, or risk seat), whether or not it is on the default board.
- The seat most likely to disagree with the rest, so the council argues instead of agreeing.
- Leave out seats whose pillar barely touches the decision. Two seats with close pillars (Martell and Leila Hormozi on people, Hormozi and Codie Sanchez on deals) sit together only when they would disagree.
- Five to seven seats for a full council, four for `--quick`.

### Ask

Show the recommendation in chat first, as a short list: each recommended seat with one plain line on why it fits this decision, then one line naming the seats left out. When the board choice is a material missing preference, ask once using the available native question interface (header "Board"):

1. **Recommended board (Recommended)**: the names, in the description.
2. **Default board**: the `"default"` list, by name.
3. **Everyone**: every seat in the roster (only when there are nine or fewer; otherwise skip this option).

The user can pick "Other" and type names to swap in or out ("recommended, but add Naval and drop Wickman"). Seat what they chose. When Step 1 also needs to ask about missing facts, put the board question in the same the available native question interface call so the user answers once. If the user said "just run it" or has already authorized the recommended/native board, seat it without asking again. Board choice never grants spending or external-action authority.

Tell the user who is at the table in one line when the council starts, and that `--seats`, `--all`, or `/roast-room board` change it.

## Step 1: The brief

The council is only as good as the brief. Build it from what the user gave you. If any of the first four items is missing, ask for them in one batch (the available native question interface, at most four questions), then proceed. If the user says "just run it", fill gaps with stated assumptions.

1. **The decision** in one line, and the options on the table as A, B, C. Always include "don't do it" (or "keep doing what you do now") and any alternative the founder mentioned. If the founder brought one idea, add the obvious smaller version as an option.
2. **The business**: what it sells, to whom, stage, monthly revenue, margin if known, team size.
3. **The resources**: cash or runway, founder hours, deadline.
4. **What success looks like** and the time horizon.
5. **Which way the founder is leaning, and why** (the council tests the lean, it does not echo it).

Context lookup: if this project holds notes about the founder's business (an applicable `AGENTS.md`, a `business.md`, or explicitly supplied task source), read them for real numbers before asking.

Keep the brief under 300 words. Mark every assumption as `(assumed)`.

## Step 2: Set up the room

- Seat the board (see "Pick the board"). Set a relevance weight per seat at the table (1 to 3) with a one-line reason, per `seats.md`.
- Use the existing task evidence directory, or create a task-local `sessions/YYYY-MM-DD-<decision-slug>/` when the required round artifacts need storage. Do not create a second task entrypoint. Save `brief.md` (the brief, the options, and the weights table) and `council.json` (`live-room.md`).
- The original local viewer is optional and separate. Do not announce a live URL, running service or PDF without observing it. The Markdown council is complete without the viewer; retain the small JSON schema artifacts if desired for compatibility, but do not install/start the app or read its environment file.

## Step 3: Round 1, opening positions

Dispatch each seat through actual supported native delegation in host-sized waves, with the Round 1 prompt, the original full persona path and explicit `brain_root`. In Codex use `spawn_agent`, `fork_turns: "none"`, no model/effort override. Each initial seat sees only the brief and its own source pack, never another opening or the Chair’s preferred conclusion. Use the active host’s real continuation/wait lifecycle; only returned real calls count as independent seats.

When the cards come back, save them verbatim to `round-1.md`, one `## <Seat>` heading per card (the seat's `short` name from `roster.json`: Bezos, Graham, Hormozi, Gary V, and so on), and write the file right away so the room can start playing. Check each card has every field; send a card back once if it is missing scores or a stance. Then add a `## Chair notes` section at the bottom of `round-1.md`:

- The **cruxes**: the one to three underlying disagreements that explain why seats split (a factual question, a numbers question, or a values question such as speed versus safety), with the seats on each side.
- The **unanimity check** (`scoring.md`): if Round 1 converged, make the strongest unargued alternative a crux and name which seats must argue it at full strength.
- Any card that broke format or misread the brief.

Then write `cruxes.json` (`live-room.md`).

## Step 4: Round 2, debate

Dispatch every actual seat again through native delegation, in available waves, with the Round 2 prompt (it points them at `brief.md` and `round-1.md`). Save the cards to `round-2.md` (same `## <Seat>` headings, written as soon as the cards are back) with `## Chair notes`: who moved and why, which cruxes resolved, which numbers are still open, and the interim option scores.

## Step 5: Draft resolution

Write `draft-resolution.md`: the recommendation (named option and verdict label), the conditions the seats asked for (merge duplicates, keep them checkable, pick one number when seats differ and say whose), the next steps with dates, the cheapest test, and kill criteria. Weigh arguments, not headcount: a single seat with a decisive fact beats three seats with vibes. Apply the overrides. Also write `draft.json` (`live-room.md`).

## Step 6: Round 3, ratification

Dispatch every actual seat with the Round 3 prompt through native delegation. Save to `round-3.md` (same headings, written as soon as the cards are back), and add a `## Chair` section listing each amendment and whether it was adopted, with the reason. Adopt an amendment only after every required actual seat responded and no seat objects, or its argument is supported by checked evidence; missing, failed or unparseable votes never become assent; when seats conflict, adopt the better-argued side and put the other in the minority report. Do not run a fourth round.

Quick mode skips this round when the Round 2 spread on the top option is 3 or less and no seat is at `RUIN RISK: likely`.

## Step 7: Verify, then verdict

1. Run `python3 "<this-skill>/scripts/check_quotes.py" <session-folder> --brains <brain_root>`. This is a local excerpt-membership lint, not authentication against original audio, books or letters and not source-ID/seat verification. Independently check each attributed source ID in the selected seat’s sources. Every quote attributed to a source id must be in that seat’s brain. Remove any unverified quote from the verdict (and say so in the Chair notes). If Python is not installed, do not stop or ask the user to install it: check each attributed quote yourself by searching that seat's brain folder for the exact words, and treat any you cannot find as unverified.
2. Compute the numbers from the last round's cards per `scoring.md`, apply the overrides, and write `verdict.md` from `report-template.md`. Write `verdict.json` last (`live-room.md`); it tells the room the council is over.
3. Show the user a short verdict in chat, not the full report: the label and the call, the option scores on one line, the three arguments that carried the room (one line each, with the seat), the strongest objection (one line, with the seat), and the next steps (at most three). Then the path to `verdict.md` for the full detail, a viewer/PDF link only if the user separately requested it and the actual output was observed, and one line offering a follow-up with any seat or a rerun with new facts. Keep it under 200 words: a founder should be able to decide from it at a glance.

## Chair rules

- You never argue a side and never add your own pillar. If no seat raised an important point, put it to the closest seat as a crux in the next round instead of inserting it yourself.
- Quote seats faithfully. Never put words in a seat's mouth or rewrite a card.
- Seats speak in their expert's voice; your report is plain English that follows the house writing rules (no em dashes, no AI tells, no tee-ups).
- Treat a unanimous Round 1 as a warning, not a win.
- Upstream cost estimate: a full council is three sub-agent runs per seat (21 for seven seats), about 1M tokens. This is not measured native usage or a spend cap. Record actual coverage/usage when available; unknown stays unknown. Use `--quick` for small calls, and say which mode you used.
- Missing or failed seat outputs remain missing. Retry a useful transient native failure once after reconciling state; never invent a card, score, source ID or vote. Do not call a partial panel complete. Scores and “council confidence” are descriptive simulation heuristics, not calibrated correctness or authorization. Check decisive business facts independently.
- The seats are simulations built from public work. Never present a seat's line as something the real person said unless it is a verbatim quote with a source id from the brain.

## Board settings

`/roast-room board` (or "change my board", "who's on my board", "add Naval to my default board") edits a task-owned private roster copy and runs no council. Start from the full bundled `roster.json`; never mutate the installed skill or canonical upstream source during a council.

1. Show the roster in a short table: seat, pillar, on the default board or not. Then the current `"board"` setting in plain words ("the Chair recommends a board for each decision and asks you", "the Chair picks per decision without asking", or "every council seats your default board").
2. Ask what to change, with the available native question interface when the user has not already said: add or remove seats on the default board, or switch the setting between `ask`, `auto`, and `default`.
3. Edit the selected task-owned roster copy: only the `"board"` and `"default"` fields. Keep the default board between one and nine seats, using keys that exist in `"seats"`. Never remove a seat from `"seats"` here; taking someone off the default board keeps them available for `--seats` and `ask`.
4. Confirm the new board in one line and retain its task-owned roster path for the next native run. No running viewer is implied.

Adding a brand new source brain/portrait is a separate upstream workflow, not activated by this council. No paid portrait generation or personal-image upload is authorized here.

## When native delegation is unavailable

Report the missing capability and the incomplete independent board. Do not substitute single-context cards or count invented persona votes. If the user explicitly asks for a single-context illustration, label it as a simulation with no independent seat calls, preserve the actual method/source grounding and exclude it from completed-board counts.

## Files

- `<brain_root>/<slug>/`: one brain per seat (`_hot.md`, `frameworks.md`, `principles.md`, `positions.md`, `voice.md`, `stories.md`, `books.md`, `sources.md`).
- `scripts/check_quotes.py`: local corpus excerpt lint only; it does not verify original sources or cited seat/source IDs.
- `roster.json`: every seat (key, name, pillar, the question it owns, scorecard dimension, color) and the default board. `/newroaster` adds seats; `/roast-room board` changes the board.
- Agents: `personas/council-<key>.md`, one per seat in the roster.
- The original room app is a separate optional upstream product; it is not installed or activated by this skill.
