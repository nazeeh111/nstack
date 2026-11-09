"""Source-scoped security review ports; preserve independent evidence and coverage."""
import pathlib,re,shutil
P=pathlib.Path

def change(s,old,new):
 if old not in s:raise ValueError('Missing security port anchor: '+old[:80])
 return s.replace(old,new)
def patch(name,source,out):
 p=out/'SKILL.md';s=p.read_text();s=re.sub(r'(?m)^allowed-tools:.*\n','',s)
 if name=='differential-review':
  s=change(s,'5. **Output-Driven**: Always generate comprehensive markdown report file','5. **Evidence-Driven**: Keep findings reviewable. A concise chat result is sufficient for a tiny review; save a report when its scope or requested handoff merits one.')
  s=change(s,'| "No tests = not my problem" | Missing tests = elevated risk rating | Flag in report, elevate severity |','| "No tests = not my problem" | Missing tests leave uncertainty | Record coverage and run a discriminating probe; severity follows supported impact |')
  s=change(s,'| "Just a refactor, no security impact" | Refactors break invariants | Analyze as HIGH until proven LOW |','| "Just a refactor, no security impact" | Refactors can change invariants | Check affected runtime paths and allowed/denied behavior; classify supported risk |')
  s=change(s,'| "I\'ll explain verbally" | No artifact = findings lost | Always write report |','| "I\'ll explain verbally" | Evidence must be reviewable | Use concise source-linked findings, with a durable file when needed |')
  start=s.index('## Agents');end=s.index('\n---',start)
  s=s[:start]+'''## Independent adversarial review

For consequential trust-boundary changes, use a fresh independent reviewer when it can catch material errors. Supply requirements, current diff/history and actual runtime evidence. Use supported host tools and existing model/effort choices. No namespaced Claude agent registration is required. Exercise allowed and denied tenant/account combinations and an attacker-controlled path that must remain denied; retain uncertainty for untested boundaries.
'''+s[end:]
  s=s.replace('Or delegate to: differential-review:adversarial-modeler agent','Or request an independent host-supported adversarial review')
  s=s.replace('- [ ] Report file generated','- [ ] Findings and evidence delivered in the proportionate requested form')
  s=s.replace('- Always generate the output file','- Save an output file when the scope or requested handoff needs it')
  s=s.replace('- Output report only to chat (file required)','- Omit material evidence or fail to save a file when one is required by the task')
 elif name=='dimensional-analysis':
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
  for f in out.rglob('*.md'):
   t=f.read_text();t=t.replace('{baseDir}/','./' if f.parent==out else '../');f.write_text(t)
  s=s.replace('{baseDir}/','./')
 else:raise ValueError('Security leaf not mapped')
 p.write_text(s)
