"""Source-scoped security review ports; preserve independent evidence and coverage."""
import pathlib,re,shutil
P=pathlib.Path

def change(s,old,new):
 if old not in s:raise ValueError('Missing security port anchor: '+old[:80])
 return s.replace(old,new)
def patch(name,source,out):
 p=out/'SKILL.md';s=p.read_text();s=re.sub(r'(?m)^allowed-tools:.*\n','',s)
 if name=='differential-review':
  s=change(s,'| "No tests = not my problem" | Missing tests = elevated risk rating | Flag in report, elevate severity |','| "No tests = not my problem" | Missing tests leave uncertainty | Record coverage and run a discriminating probe; severity follows supported impact |')
  s=change(s,'| "Just a refactor, no security impact" | Refactors break invariants | Analyze as HIGH until proven LOW |','| "Just a refactor, no security impact" | Refactors can change invariants | Check affected runtime paths and allowed/denied behavior; classify supported risk |')
  start=s.index('## Agents');end=s.index('\n---',start)
  s=s[:start]+'''## Independent adversarial review

For consequential trust-boundary changes, use a fresh independent reviewer when it can catch material errors. Supply requirements, current diff/history and actual runtime evidence. Use supported host tools and existing model/effort choices. No namespaced Claude agent registration is required. Exercise allowed and denied tenant/account combinations and an attacker-controlled path that must remain denied; retain uncertainty for untested boundaries.
'''+s[end:]
  s=s.replace('Or delegate to: differential-review:adversarial-modeler agent','Or request an independent host-supported adversarial review')
 elif name=='dimensional-analysis':
  s=change(s,'The same workflow applies in Claude Code and Codex. Legacy `allowed-tools` frontmatter is Claude metadata, not a Codex permission grant.','Use this workflow in Codex. Upstream `allowed-tools` metadata does not grant Codex permissions.')
  s=change(s,'In Claude Code, use these registered namespaced plugin agent identifiers listed below as the dispatch type. In Codex, create workers','In Codex, create workers')
  s=change(s,"In Codex, use the host's plan or a workspace status file; Claude Code may use its existing `TodoWrite` tool.","In Codex, use the host's plan or a workspace status file.")
  s=change(s,'Requires native agent dispatch and a writable, explicitly scoped target.','Requires a readable, explicitly scoped target. Source writes require annotation authority. Independent scanner/validator review may use supported host dispatch when proportionate.')
  s=change(s,'Invoking this skill authorizes dimensional comments and workspace analysis artifacts, not unrelated code fixes.','A review invocation authorizes findings and a unit inventory. It does not by itself authorize source annotations or unrelated code fixes.')
  s=change(s,'Runtime policy and explicit user constraints take priority over the default full-auto behavior.','Runtime policy and explicit user constraints control every stage.')
  start=s.index('## Execution Mode');end=s.index('## Scope and Coverage Guarantees',start)
  s=s[:start]+'''## Execution Mode

Honor the caller's mode. Default to findings and a unit inventory without changing source. Annotation mode requires specific task authority; apply only within the declared files and preserve pre-existing edits. Keep the scanner and validator independent. In review mode, use the phase instructions to derive candidate units and propagation findings in task-local evidence, without executing their source-write steps. Unknown units stay unknown until supported; do not present a best guess as validation. Save only proportionate requested analysis artifacts. Record coverage and blocked files honestly.

'''+s[end:]
  s=s.replace('"mode": "full-auto"','"mode": "review"')
  prompts=out/'prompts';prompts.mkdir()
  for name in ['arithmetic-scanner','dimension-discoverer','dimension-annotator','dimension-propagator','dimension-validator']:
   src=source/'plugins/dimensional-analysis/agents'/f'{name}.md';shutil.copy2(src,prompts/src.name)
  s=s.replace('../../agents/','prompts/')
  for f in list((out/'references').glob('step*.md'))+list(prompts.glob('*.md')):
   f.write_text('> Execution scope: review is the default and does not write source annotations. Annotation/propagation writes below apply only in specifically authorized annotation mode. Keep scanner/validator independent and report unknown units and unprocessed scope.\n\n'+f.read_text().replace('../skills/dimensional-analysis/','../'))
 elif name=='semgrep':
  s=re.sub(r'description: >-\n(?:  .*\n)+', 'description: Read-only Semgrep security scan with actual ruleset/engine locks, coverage records, raw outputs and false-positive review. Existing explicit scan authority is sufficient; ask only for material missing scope or access.\n',s,count=1)
  s=re.sub(r'(?m)^2\. \*\*User must approve.*$', '2. **Honor existing scan authority.** Record exact target, engine, mode and rulesets. Proceed within that scope; ask only for material missing information, access or new spending.',s)
  s=s.replace('Step 3: Present plan + rulesets, get approval [⛔ HARD GATE]','Step 3: Record exact scoped rulesets and existing authority')
  s=change(s,'The approval gate stays in the session; the script is execution only and asks nothing. The\napproved list reaches it as a JSON file, so the scan cannot reach a ruleset the user declined.','Record the selected rulesets as JSON before execution. The script asks nothing and must stay within existing scan authority and any explicit exclusions.')
  start=s.index('## Running it as a Workflow');end=s.index('## Workflow\n',start)
  s=s[:start]+'''## Native unattended execution

Use the pinned local scripts directly rather than an unregistered plugin slash command. Detect languages and installed engine/version; use [rulesets](references/rulesets.md) and [scan modes](references/scan-modes.md). Record immutable engine/ruleset revisions and the target source revision. Use only a free available engine; paid Pro access stays conditional and is never purchased by this leaf. Do not globally install agents or hooks.

Run `bash scripts/run-scans.sh --target "$TARGET" --output-dir "$OUTPUT_DIR" --mode "$MODE" --rulesets "$RULESETS"` from this leaf, with absolute target/output/ruleset paths. The script owns metrics-off, include/exclude filtering, batching and per-process status. Inspect its actual help for any extra flags. No autofix is authorized by a scan request.

'''+s[end:]
  s=s.replace('| 3 | Present plan, get explicit approval | ⛔ HARD | AskUserQuestion |','| 3 | Record scoped plan, rulesets and existing authority | — | Actual target/source/engine/ruleset locks |')
  s=re.sub(r'(?m)^\*\*Task enforcement:\*\*.*$', 'Use proportionate host task tracking. Existing authority persists; do not invent an approval gate or mark failed/skipped coverage complete.',s)
  s=re.sub(r'(?m)^\| "User asked for scan.*$', '| "User asked for scan" | Proceed within that explicit scope, preserving stated exclusions and free-tool limits |',s)
  s=re.sub(r'(?m)^\| "Step 3 task.*$', '| "A stage is incomplete" | Preserve actual state; never fabricate acceptance |',s)
  s=re.sub(r'(?m)^\| "Just use default rulesets.*$', '| "Choose rulesets" | Use the source/stack and requested scope; record exact immutable revisions |',s)
  s=s.replace('- [ ] User explicitly approved the scan plan (Step 3 gate passed)','- [ ] Target, rulesets, engine, source revision and existing task authority recorded')
  s=s.replace('at the Step 3 gate','before execution')
  s=s.replace('use `semgrep-rule-creator` skill', 'use the project rule-authoring workflow and its tests; this leaf covers scanning')
  s=s.replace('use `semgrep-rule-variant-creator` skill', 'use the project rule-porting workflow and its tests; this leaf covers scanning')
  s=s.replace('Use `semgrep-rule-creator` skill', 'Use the project rule-authoring workflow and its tests; this leaf covers scanning')
  s=s.replace('Use `semgrep-rule-variant-creator` skill', 'Use the project rule-porting workflow and its tests; this leaf covers scanning')
  s=s.replace('Use Glob, not Bash', 'Use native scoped file discovery')
  s=s.replace('Assumptions cause scanning wrong directories/rulesets. Present plan for verification', 'Resolve target and rulesets from the task and source; ask only for material ambiguity')
  s=s.replace('Modifying approved list without consent breaks trust', 'Preserve explicit exclusions; resolve routine ruleset choices within existing scan authority')
  s=s.replace('Pro enables cross-file taint tracking and catches ~250% more true positives. Skipping the check means silently missing critical inter-file vulnerabilities.', 'Use already authorized Pro access only when available; record the actual engine and cross-file coverage. Do not buy access or infer coverage from a promotional multiplier.')
  s=s.replace('Cross-file analysis catches 250% more true positives; worth the time', 'Use existing authorized cross-file capability when relevant; report unavailable coverage')
  s=s.replace('Read-only Semgrep security scan with actual ruleset/engine locks, coverage records, raw outputs and false-positive review.', 'Read-only Semgrep security scan with explicit ruleset/engine provenance, coverage records, raw outputs and false-positive review.')
  workflow=out/'workflows/scan-workflow.md';t=workflow.read_text()
  start=t.index('## Task System Enforcement');end=t.index('## Step 1:',start)
  t=t[:start]+'''## Native execution and authority

Use proportionate native task tracking, not a named foreign-host task API. Preserve the ordered dependencies: source/language detection, ruleset selection, scoped plan, execution, merge and report. Existing explicit scan authority persists. Ask only for material missing scope, access or new spending. Resolve every script/reference path against the owning skill directory before running it; relative examples are resource locations, not a required shell working directory.

'''+t[end:]
  start=t.index('**First, select scan mode**');end=t.index('Record the selected mode.',start)
  t=t[:start]+'''Use the user's requested mode. For an ordinary full scan, choose run-all; use important-only for an explicitly focused security triage. Ask only when the requested coverage is materially ambiguous.

'''+t[end:]
  start=t.index('## Step 3: CRITICAL GATE');end=t.index('### Log Approved Rulesets',start)
  t=t[:start]+'''## Step 3: Record Scope, Provenance and Existing Authority

Record the exact absolute target/output paths, engine/version, scan mode, detected languages, rulesets and explicit exclusions. Keep the plan within the authorized request; no second approval is required for an already authorized scan. Ask only for material missing scope, access or new spending.

Before claiming reproducible rule locks, record the resolved rule revisions and content hashes actually used. Registry IDs and unversioned repository URLs are mutable references, not locks. If exact inputs cannot be established, disclose that limit rather than describing the scan as locked or complete.

'''+t[end:]
  t=t.replace('### Log Approved Rulesets','### Save the Executed Ruleset Plan')
  t=t.replace('After approval, write the approved plan', 'Within existing authority, write the resolved plan')
  t=t.replace('what the user approved and what runs are one artifact', 'the recorded plan and what runs are one artifact')
  t=t.replace('Fill in the plan that was just approved.', 'Fill in the scoped plan resolved above.')
  t=t.replace('> **Entry:** Step 3 approved — user explicitly confirmed the plan.', '> **Entry:** Step 3 recorded the scoped plan and existing authority.')
  t=t.replace('It is the plan the user approved at the Step 3 gate, and', 'It is the recorded scoped plan, and')
  t=t.replace('go back to Step 3 and get the change approved.', 'reconcile the change with scope and explicit exclusions before updating Step 3.')
  t=t.replace('because the approved plan is what produced them.', 'until the failure is diagnosed and the revised route is checked against the existing scope.')
  t=t.replace('**Detect languages** using Glob (not Bash).', '**Detect languages** using native scoped file discovery.')
  t=t.replace('# *after* the user has passed the hard gate, so a path this skill generated itself would send\n# them back through approval.', '# after scope resolution. Normalize it here rather than generating a path the runner rejects.')
  t=t.replace('# the user has approved anything.', '# execution starts.')
  workflow.write_text(t)
  for f in out.rglob('*.md'):
   t=f.read_text();t=t.replace('{baseDir}/','./' if f.parent==out else '../');f.write_text(t)
  s=s.replace('{baseDir}/','./')
 else:raise ValueError('Security leaf not mapped')
 p.write_text(s)
