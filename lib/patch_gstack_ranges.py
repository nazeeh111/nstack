"""Audited source ranges containing retired controller protocols, at the exact pin.

Engineering/QA/product methods and substantive templates remain in full. This
runs on raw pinned Markdown exactly once, before normal native text adaptation.
"""
NATIVE_CONTEXT='''## Current project context

Use the actual requested target, local source/Git base, project instructions and relevant scoped knowledge. Infer a clear target from the conversation. Ask only when ambiguity materially changes the work. Preserve unrelated dirty work; no commit, stash or initialization is a review prerequisite. Research uses available native tools and records source provenance. No secondary memory/controller or background synchronization is configured.
'''
REVIEW='''## Optional independent challenge

For consequential uncertainty, give a native independent reviewer the actual plan/source snapshot, constraints, evidence and unresolved questions without the builder's persuasive narrative. Ask it to identify concrete failure modes, hidden assumptions, missing validation, alternatives and evidence that would change its recommendation. Preserve model/effort and existing delegation authority. Await an actually started review; report failure or unavailable coverage truthfully. The parent verifies findings, resolves authorized fixes and rechecks the final changed bytes. No provider switch or account setup is required.
'''
OUTPUT='''## Review output and continuation

Deliver the requested review artifact in a task-owned location. Preserve the original and accepted plan. Include architecture, code quality, shared-code, tests, performance and failure-mode findings supported by actual source, unresolved consequential decisions, agreed alternatives, observed checks and coverage limits. Read back saved output and independently check relevant behavior. A saved report is not an authenticated gstack receipt or publication authority. Resume from durable task state after interruption; reconcile partial writes before retry. Continue authorized implementation when that is the user's request; no mandatory skill chain, model recommendation or final approval ritual is added.
'''
PLAN_OUTPUT = """## Final planning decisions

Use Decision procedure to reconcile actual findings with requested scope and existing authority. Preserve accepted decisions and continue independent analysis while a consequential choice is pending. Proposed TODOs identify What, Why, Pros, Cons, Context and Depends on / blocked by; change a project TODO file only when that edit belongs to the request. No separate approval ledger is required.

## Required outputs

Prepare the requested review from the substantive sections below, scaled to actual complexity. Preserve the accepted plan and the current source/requirement identities. Save to the task-owned destination defined in Review record and write policy, then read it back against current inputs. Report actual unavailable/untested conditions and unsaved output. Continue already authorized implementation after dependent decisions are resolved; no logging, navigation or telemetry ritual is required.

### Output reference — review body

Include the relevant Architecture, Code Quality, Test and Performance findings and their source evidence, disposition and remaining risks. Distinguish proposed changes from completed work; keep optional advice separate from defects. A clean applicable section states that no issue was found; never invent work to fill it.

### NOT in scope

List considered work that was explicitly deferred, with one sentence explaining each deferral. Preserve accepted requirements and distinguish a deferred recommendation from an omitted requirement.

### What already exists

Link actual existing solutions and distinguish reuse from rebuilding. For accepted shared-code choices, retain the Code Quality/Test analysis: compatible contracts, callers, preserved differences, adoption/rollback, tests and whole-change cost. Explain safer separation or net growth without reopening unchanged accepted decisions.

### Diagrams

Diagram nontrivial flows, states and pipelines in a form suited to the artifact. Label actual/proposed entry points, boundaries, dependencies and failure paths; name the source files needing inline diagrams for complex behavior. Do not force a large diagram for a simple local change.

### Failure modes

For each new diagrammed path or integration, name a realistic production failure, its test/error-handling coverage and whether users see a clear error or a silent failure. A realistic silent failure with no test and no error handling is a critical gap to investigate. Keep proposed coverage and observed behavior distinct.

### Worktree parallelization strategy

Use sequential implementation by default when there is one primary module or fewer than two independent workstreams. If concurrency adds value and is authorized, give a dependency table by actual module:

| Step | Modules touched | Depends on |
| --- | --- | --- |
| Actual build step | Actual modules/directories | Prerequisite step or none |

Describe independent lanes, sequence shared modules, identify launch/wait/integration points and flag overlapping writes. A worktree is an isolation option, not a compulsory framework. Preserve unrelated dirty work and keep one writer per shared artifact.

## Implementation Tasks

Synthesize a flat, build-actionable list from the actual findings, with no padding. Reconcile an existing task list from the owning task before writing another. Each proposed task names priority, component, imperative change, source finding, concrete target files and a discriminating verification command or observation. Preserve current task IDs and dispositions where useful. Use estimates only when supported and needed; no fixed human/model speed ratio is assumed.

Example shape, to fill only with real findings:

- [ ] **T1 (P1)** — component — concrete change
  - Surfaced by: actual review section and source-backed finding
  - Files: actual/proposed target paths
  - Depends on: actual prerequisite or none
  - Verify: meaningful check and expected observation

P1 identifies a blocking defect, P2 an in-scope useful fix and P3 a follow-up recommendation. No actionable findings means no new implementation tasks. A task list or proposed fix is not completed implementation, publication authority or a registered aggregation artifact.

### Unresolved decisions

List unanswered/interrupted consequential choices and the exact missing information or authority. State their dependent work; continue independent tasks. Never silently default, double-count or claim an answer that was not given.

### Completion summary

Report the actual Scope Challenge result, checked/unverified premises, Architecture/Code Quality/Test/Performance findings, covered/unrun tests and diagrams, deferred scope, existing/reuse choices, critical failure-mode gaps, task dependencies, unresolved decisions and useful next action. Record optional independent review as completed, unavailable or not run with actual known route/model and coverage. Same-model contexts do not establish model diversity. Keep counts traceable to actual findings and evidence, and distinguish a saved review from a successful behavioral check.
"""

# Inclusive original-source line ranges. Only these files at the selected pin
# enter this port; range headers are recorded in the implementation review.
RANGES={
 'qa/SKILL.md':[(23,79,NATIVE_CONTEXT),(110,171,''),(260,298,NATIVE_CONTEXT),(345,359,'### Relevant evidence\n\nRead current scoped source and prior blocker evidence before repair.\n'),(499,525,'')],
 'review/SKILL.md':[(41,107,NATIVE_CONTEXT),(138,197,''),(385,470,NATIVE_CONTEXT),(850,949,OUTPUT),(950,976,'')],
 'plan-eng-review/SKILL.md':[(26,270,NATIVE_CONTEXT),(308,338,''),(349,395,''),(418,467,''),(481,504,OUTPUT),(511,552,'')],
 'office-hours/SKILL.md':[(50,174,NATIVE_CONTEXT),(220,258,''),(278,344,NATIVE_CONTEXT),(399,445,''),(580,622,'### Founder evidence\n\nGround the synthesis in actual answers; do not create a profile store or guess relationship history.\n'),(627,673,OUTPUT)],
 'plan-eng-review/sections/review-sections.md':[(8,125,NATIVE_CONTEXT),(181,385,'## Material decisions\n\nResolve routine choices from source and existing authority. Present concrete alternatives and ask only for an unresolved consequential decision or information. Preserve actual answers and scope in the task record; do not repeat approvals already given.\n'),(867,1103,REVIEW),(1104,1551,PLAN_OUTPUT)],
 'review/sections/plan-completion.md':[(5,40,NATIVE_CONTEXT),(178,196,'')],
 'office-hours/sections/visual-design.md':[(3,128,'## Visual design exploration\n\nRead the actual design brief, identity and references, including project DESIGN.md when relevant. Explore a few meaningfully different directions only when useful; preserve each variant in a task-owned folder. Generate previews with available native image/browser/artifact tools. Inspect the actual preview, collect material preference feedback and revise the selected source. Use existing authorized tools without acquiring another service.\n'),(169,181,'Use the native browser or supported local renderer to inspect the actual editable HTML sketch. Save only task-owned screenshots/export files and verify the rendered page.\n'),(197,282,REVIEW)],
 'office-hours/sections/design-and-handoff.md':[(3,50,'## Phase 5: Design document\n\nSave the requested design in its owning task folder, preserve prior accepted artifacts and inspect the saved content. Keep private material private. Use the full relevant template below.\n'),(169,354,REVIEW),(355,654,'## Phase 6: Handoff\n\nDeliver the requested design, source-backed decisions, unresolved questions and useful next action. Use actual supplied context only. Do not invent a session tier, relationship history or builder profile, run a profile/config logger, recommend unsolicited promotions, or open application/signup pages. Continue already authorized work; no additional approval ritual is imposed.\n'),(655,706,'## Next action\n\nGive the concrete useful next task. Continue if already requested and authorized; no funnel or prescribed skill chain.\n')],
}

def patch(text,file):
 if file.as_posix().endswith('/docs/review-policy.md'):
  file.with_name('review-policy.upstream-reference.txt').write_bytes(text.encode())
  return native_review_policy(text)
 key=next((key for key in RANGES if file.as_posix().endswith('/'+key)),None)
 if not key:return text
 lines=text.splitlines(keepends=True);result=[];pos=0
 for start,end,replacement in RANGES[key]:
  if len(lines)<end:raise ValueError('Pinned gstack range changed: '+key)
  result.extend(lines[pos:start-1]);result.append(replacement+'\n');pos=end
 result.extend(lines[pos:]);return ''.join(result)


def native_review_policy(original):
 """Keep substantive policy; retire the uninstalled shipping controller contract."""
 floor=original[original.index('## The blocking floor'):original.index('## How `/ship` converges')]
 floor=floor.replace('ship/sections/review-army.md`, ', '').replace('`review/sections/review-army.md`, ', '`review/sections/review-army.md`, ')
 # Runtime/tool-specific precedence is not a native enforcement claim.
 floor=floor.replace('the specialist still reports each untested cell CRITICAL so `gstack-state-matrix check` proves the matrix complete, and `gstack-state-matrix findings` maps it to INFORMATIONAL per matrix cell before the merge;', 'report untested state-matrix cells as coverage gaps; assess a demonstrated broken transition separately;')
 risk=original[original.index('| Class | Signal |'):original.index('An input the classifier cannot read')]
 risk=risk.replace('`SCOPE_AUTH` from `gstack-diff-scope`', 'source-visible authentication scope').replace('`SCOPE_AUTH`','authentication scope')
 risk=risk.replace('a hunk the gate scan tagged:', 'a source hunk affecting a gate:')
 risk=risk.replace('or a call to a paid provider `lib/pricing.ts` prices.', 'or a call to a paid provider.')
 risk=risk.replace('(the full list is `MONEY_USD_WORDS` in `lib/review-risk.ts`)', '(inspect the actual identifier and its effect)')
 rules=original[original.index('## Two checklist rules with ids'):original.index('<a id="porting-a-contributors-work">')]
 text='''# Native review policy

Adapted from garrytan/gstack at622e8b1f76d293b647eca7b33d9dd060ab618b21, docs/review-policy.md. The full byte-exact original is retained in `review-policy.upstream-reference.txt` as archival implementation evidence. It does not install or activate the original controller. Use the native method below for actual work.

'''+floor+'''## Native convergence and evidence

Review the actual requested diff and source snapshot. Resolve concrete defects within existing task authority; a review-only request reports findings. After authorized repairs, re-read affected source/callers and re-run meaningful checks. Reuse unchanged accepted decisions. Stop repeating clean unchanged checks; report persistent blockers and missing coverage honestly. A time/call budget never approves a blocker. No fixed fanout, extra provider, shipping queue, approval ledger or publication action is implied.

Keep actual requirements, input/base/source identities, reviewer coverage, raw findings, reasons for disagreement, decisions, changes and observed check results in task-local evidence. Do not omit a distinct failure, lower severity through deduplication, infer a clean review from an empty or failed reply, or fabricate a capture/dispatch receipt. Reconcile final findings against the current changed bytes. An independent opinion corroborates a source-backed finding; agreement does not prove it. Native permissions and the user's model/effort remain controlling.

## Risk-focused review

Money, gate, authentication and secret code deserve focused inspection of actual effects and preventing controls. Use relevant specialist checklists when their depth helps and independent native review when consequential and authorized. The following source-derived signals guide selection; they are not an installed automatic classifier:

'''+risk+'''Record which classes and paths were inspected and any unread scope. A missing classifier does not prove the absence of a risk class. Review changed inputs, failure paths and removing controls as carefully as additions. Keep authorized fixtures in scope and disclose actual exclusions; do not silently review only a truncated diff.

'''+rules+'''## Attribution and handoff

Preserve original contributor credit and existing commits. Record the actual diff and checks; staging, committing, issue filing, posting or publication needs its own specific authority. Hand off the requested artifact and unresolved conditions without claiming an authenticated upstream receipt.
'''
 # Preserve domain prose that later generic legacy slash-command filtering would
 # otherwise delete as a whole line. These mentions are context, not commands.
 return text.replace('/ship','upstream shipping').replace('ship/sections/review-army.md','review/sections/review-army.md')
