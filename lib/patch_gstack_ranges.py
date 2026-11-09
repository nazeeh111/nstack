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
# Inclusive original-source line ranges. Only these files at the selected pin
# enter this port; range headers are recorded in the implementation review.
RANGES={
 'qa/SKILL.md':[(23,79,NATIVE_CONTEXT),(110,171,''),(260,298,NATIVE_CONTEXT),(345,359,'### Relevant evidence\n\nRead current scoped source and prior blocker evidence before repair.\n'),(499,525,'')],
 'review/SKILL.md':[(41,107,NATIVE_CONTEXT),(138,197,''),(385,470,NATIVE_CONTEXT),(850,949,OUTPUT),(950,976,'')],
 'plan-eng-review/SKILL.md':[(26,270,NATIVE_CONTEXT),(308,338,''),(349,395,''),(418,467,''),(481,504,OUTPUT),(511,552,'')],
 'office-hours/SKILL.md':[(50,174,NATIVE_CONTEXT),(220,258,''),(278,344,NATIVE_CONTEXT),(399,445,''),(580,622,'### Founder evidence\n\nGround the synthesis in actual answers; do not create a profile store or guess relationship history.\n'),(627,673,OUTPUT)],
 'plan-eng-review/sections/review-sections.md':[(8,125,NATIVE_CONTEXT),(181,385,'## Material decisions\n\nResolve routine choices from source and existing authority. Present concrete alternatives and ask only for an unresolved consequential decision or information. Preserve actual answers and scope in the task record; do not repeat approvals already given.\n'),(867,1103,REVIEW),(1104,1551,OUTPUT)],
 'review/sections/plan-completion.md':[(5,40,NATIVE_CONTEXT),(178,196,'')],
 'office-hours/sections/visual-design.md':[(3,128,'## Visual design exploration\n\nRead the actual design brief, identity and references, including project DESIGN.md when relevant. Explore a few meaningfully different directions only when useful; preserve each variant in a task-owned folder. Generate previews with available native image/browser/artifact tools. Inspect the actual preview, collect material preference feedback and revise the selected source. No design daemon, board URL, provider account or paid-image allowance is required.\n'),(169,181,'Use the native browser or supported local renderer to inspect the actual editable HTML sketch. Save only task-owned screenshots/export files and verify the rendered page.\n'),(197,282,REVIEW)],
 'office-hours/sections/design-and-handoff.md':[(3,50,'## Phase 5: Design document\n\nSave the requested design in its owning task folder, preserve prior accepted artifacts and inspect the saved content. Keep private material private. Use the full relevant template below.\n'),(169,354,REVIEW),(361,383,'Use actual known task/user context for the next step; do not infer a profile tier or relationship history.\n'),(655,706,'## Next action\n\nGive the concrete useful next task. Continue if already requested and authorized; no funnel or prescribed skill chain.\n')],
}

def patch(text,file):
 key=next((key for key in RANGES if file.as_posix().endswith('/'+key)),None)
 if not key:return text
 lines=text.splitlines(keepends=True);result=[];pos=0
 for start,end,replacement in RANGES[key]:
  if len(lines)<end:raise ValueError('Pinned gstack range changed: '+key)
  result.extend(lines[pos:start-1]);result.append(replacement+'\n');pos=end
 result.extend(lines[pos:]);return ''.join(result)
