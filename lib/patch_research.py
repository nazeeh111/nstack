"""Codex ports of the three selected independent research-review stages."""
import hashlib,json,pathlib,re,textwrap,shutil
P=pathlib.Path

def prompt(text):
 start=text.index('  message: |\n')+len('  message: |\n');end=text.index('\n```',start)
 return textwrap.dedent(text[start:end]).strip()+'\n'


def change_once(text, old, new):
 if text.count(old)!=1:raise ValueError('Pinned research method anchor changed: '+old[:80])
 return text.replace(old,new)

def port_section(text,start,end,replacement):
 if text.count(start)!=1 or text.count(end)!=1:raise ValueError('Pinned research section changed: '+start)
 a=text.index(start);b=text.index(end,a+len(start))
 return text[:a]+replacement.rstrip()+'\n\n'+text[b:]

def port_review_method(name,original,out):
 """Retain the actual upstream audit/claim method; adapt only host plumbing."""
 refs=out/'references';refs.mkdir(exist_ok=True)
 review=prompt(original)
 (refs/'review-prompt.md').write_text('# Independent read-only review prompt\n\n'+review)
 if name=='experiment-audit':
  description='Audit experiment integrity using independent source review of ground truth, normalization, results, reachable evaluation code and actual scope.'
  body='# Experiment Audit: Fresh-Agent Integrity Verification\n\n'+original[original.index('## Why This Exists'):]
  body=port_section(body,'## Constants','## Workflow','')
  body=change_once(body,'**The executor (Codex) collects file paths. A fresh Codex reviewer reads code and judges integrity. The executor does NOT participate in integrity judgment; this base route is same-family/provisional.**','**The executor collects original file paths. A fresh read-only reviewer reads code and judges integrity independently. Do not replace that review with the executor\'s persuasive summary. Record the actual reviewer, scope and limits; a fresh context does not establish model-family diversity.**')
  body=change_once(body,'This follows `shared-references/reviewer-independence.md` and `shared-references/experiment-integrity.md`.','The checklist, evaluation classifications, report schema and downstream integrity tags below form the operative method.')
  body=body.replace('### Step 2: Send to Reviewer (GPT-6-Astra via Codex MCP)','### Step 2: Send to an independent native reviewer')
  body=body.replace('### Step 1: Collect Artifacts (Executor — Codex)','### Step 1: Collect Artifacts (Executor)')
  body=body.replace('### Step 3: Parse and Write Report (Executor — Codex)','### Step 3: Parse and record the report (Executor)')
  body=change_once(body,"Parse the reviewer's response and write `EXPERIMENT_AUDIT.md`:","Parse the reviewer's response using this report structure in the project's existing report. `EXPERIMENT_AUDIT.md` is a conventional name, not a compulsory duplicate file:")
  body=change_once(body,'Also write `EXPERIMENT_AUDIT.json` for machine consumption:','When a downstream consumer needs structured data, retain this JSON schema in the owning task artifact:')
  body=body.replace('### Automatic in /research-pipeline (advisory, never blocks)','### Existing project pipeline integration (advisory)')
  body=change_once(body,'When integrated into the pipeline, this skill runs automatically after `/experiment-bridge` and before `/auto-review-loop`:','If the owning project already has an authorized experiment/review pipeline, retain these transitions and integrity tags. This skill does not install or start that pipeline:')
  body=change_once(body,'**Never blocks the pipeline.** Even on FAIL, the pipeline continues — but claims carry visible integrity tags.','**Advisory continuation:** independent pipeline work can continue on FAIL with visible integrity tags. This does not confirm an affected claim or advance it toward submission; the claim gate below reconciles the raw support judgment with integrity and confidence.')
  a=body.index('### Read by /result-to-claim (if exists)');b=body.index('## Key Rules',a)
  body=body[:a]+'''### Read by result-to-claim (if an audit exists)

```text
if a completed integrity audit exists in the project record:
    read integrity_status and affected claim IDs
    attach integrity_status to the independent claim-review verdict
    preserve raw_claim_supported as the actual reviewer's yes/partial/no result
    if integrity_status == "fail":
        confidence = "low"
        effective_claim_status = "inconclusive"
        display raw support with [INTEGRITY CONCERN]; never display it as confirmed
    if integrity_status == "warn":
        preserve the warning and its affected evidence in the verdict
else:
    integrity_status = "unavailable"
    mark the verdict provisional — no integrity audit
```

### Read by paper writing (if an audit exists)

Carry the audit source, affected claim IDs and integrity tags into the evidence review. A failed integrity audit keeps the effective claim status inconclusive even when raw support was yes. A footnote alone does not resolve the concern or make that claim ready for submission. Unaffected writing and independently supported claims can continue within the task.

'''+body[b:]
  body=change_once(body,'- **Never block**: warn loudly, never halt the pipeline.','- **Advisory continuation**: report integrity concerns and continue unaffected work; do not treat an affected inconclusive claim as confirmed or ready for submission.')
  body=body.replace('**File-as-switch**: no EXPERIMENT_AUDIT.md = skill was never run = zero impact on existing behavior.','**Absent audit**: no completed audit evidence means integrity status is unavailable. Preserve the project\'s existing report location; do not infer completion from a filename.')
  body=change_once(body,'- **Review class**: base Codex is same-family provisional; a completed positive selected review may claim cross-family accepted only with known different model families.','- **Review class**: record the actual independent review scope and known identities. Do not infer cross-family evidence from a fresh context or let model agreement substitute for source evidence.')
  body=body.replace('See `shared-references/experiment-integrity.md` for the full integrity protocol.','Preserve the per-check status, claim impact and integrity tags above when handing this result to claim review.')
 else:
  description='Judge what experimental results support, reconcile integrity-audit findings, and route supported, partial, unsupported or inconclusive claims to the appropriate next action.'
  body='# Result-to-Claim Gate\n\n'+original[original.index('## When to Use'):]
  body=change_once(body,'1. **W&B** (preferred):','1. **Existing authorized tracker** (for example, W&B; use task-provided exports without adding a service):')
  body=port_section(body,'### Step 1.5: Deterministic evidence pre-check','### Step 2: Codex Judgment',"""### Step 1.5: Deterministic evidence pre-check

Resolve this loaded skill's actual directory, then use its sibling checker by absolute path. Replace `<skill-dir>` below with that resolved directory; do not assume the task project or process working directory contains this tool. Use explicit project-owned roots:

```bash
python3 "<skill-dir>/tools/evidence_check.py" PROJECT CLAIMS_JSON --root RESULTS_ROOT --root SOURCE_ROOT
```

Each claim binds an exact JSON Pointer or CSV column/unique row key, value and hashed provenance receipt. The receipt binds unit, metric, split/run paths and hashes, producing argv, source hashes and result hash. See [the schema](references/evidence-schema.md). The checker never executes recorded commands. Missing, ambiguous or inconsistent evidence is `unknown`, not fabrication. `consistent-record` establishes structured agreement only, not execution, fair splitting, causal provenance or semantic claim support. Pass the actual pre-check result to the independent reviewer. If the helper is unsuitable, inspect the structured evidence directly rather than substituting a lexical match.
""")
  body=body.replace('### Step 2: Codex Judgment','### Step 2: Independent native judgment')
  body=change_once(body,'Send the collected results to a secondary Codex agent for objective evaluation:','Send the collected results and original source locators to a fresh read-only native reviewer for independent evaluation:')
  body=body.replace('secondary Codex response','independent reviewer response')
  body=change_once(body,'**Skip this step if `EXPERIMENT_AUDIT.json` does not exist.**','**Read the actual completed integrity audit if available, whether it uses this conventional JSON filename or the owning project\'s equivalent report. If unavailable, retain `integrity_status: unavailable`; do not invent a pass.**')
  body=body.replace('low" regardless of Codex judgment','low" regardless of the claim-support judgment')
  body=change_once(body,'See `shared-references/experiment-integrity.md` for the full integrity protocol.','A failed integrity audit forces confidence low; under the rules below that is inconclusive, even if the raw support field says yes. Warnings remain visible, and an absent audit remains explicitly provisional. Preserve the audit source and affected claim IDs.')
  body=change_once(body,'3. Design and run supplementary experiments to fill evidence gaps','3. Design supplementary experiments to fill evidence gaps; execute only within the existing experiment scope and budget')
  body=change_once(body,'2. If ablation studies are incomplete → trigger `/ablation-planner`','2. If ablation studies are incomplete → recommend or continue the project\'s selected ablation planning within existing authority')
  body=port_section(body,'### Step 5: Update Research Wiki (if active)','## Rules',"""### Step 5: Update the existing research record when needed

Preserve the project's canonical findings and claim records rather than creating a new wiki, graph or queue. Record experiment identity, verdict, confidence, metrics, reasoning, source/run hashes and the audit/producing evidence. Preserve these source distinctions:

1. An experiment's empirical support or invalidation is separate from a claim's formal-proof status. A yes/partial/no experiment verdict never changes a theorem to proved or disproved.
2. Update the owning experiment record before attaching its evidence to claim IDs; do not create orphan links or overwrite richer idea content.
3. Record positive/mixed/negative outcomes, failure/risk notes, lessons and reusable components in their existing owner. Repeated failed/partial ideas can justify reconsidering the hypothesis; this is a recommendation, not an automatic new pipeline.

Use supported project operations only within existing authority. No generated-graph rebuild, shared queue write or extra service follows from the review.
""")
  body=change_once(body,'- **The secondary Codex agent is the judge, not the local executor.** The local executor collects evidence and routes; the reviewer agent evaluates. This prevents post-hoc rationalization.','- **The independent reviewer judges; the executor collects original evidence and applies the verdict.** Do not replace an unavailable reviewer with the builder\'s own favorable judgment.')
  body=body.replace('If Codex says "partial"','If the reviewer says "partial"')
  body=change_once(body,'- If `confidence` is low, treat the judgment as inconclusive and add experiments rather than committing to a claim.','- If `confidence` is low, treat the judgment as inconclusive; identify the smallest additional evidence to collect within existing authority rather than committing to a claim.')
  body=change_once(body,'- Always record the verdict and reasoning in findings.md, regardless of outcome.',"- Record the verdict and reasoning in the project's existing findings location, regardless of outcome; no duplicate findings.md is required.")
  a=body.index('- **Fail closed if the reviewer is unavailable.**');b=body.index('- Record the verdict',a)
  body=body[:a]+"- **If the reviewer is unavailable**, record `REVIEW_UNAVAILABLE` with the attempted scope and actual error. Do not emit a substitute positive claim judgment or advance a submission-facing claim. Continue independently useful non-submission evidence collection within existing authority; no model downgrade, provider setup or new paid call is implied.\n"+body[b:]
  tools=out/'tools';tools.mkdir(exist_ok=True);shutil.copy2(P(__file__).parent/'claim_evidence.py',tools/'evidence_check.py')
  (refs/'evidence-schema.md').write_text("""# Structured evidence schema

Claims JSON is an array. Each record has id, path, format, value and provenance. JSON adds pointer (RFC6901); CSV adds column and row_key:{column,value}. All paths are project-relative and must resolve within explicit --root directories. Globs identify one regular file; symlink escapes and ambiguous rows are rejected before reading content.

provenance is {path,sha256,unit,metric,split_sha256,run_sha256,command}. Its path identifies a JSON receipt whose SHA256 matches. The receipt repeats these fields and adds split_path,run_path,artifact_sha256,sources:[{path,sha256}]. Actual split/run/source/artifact bytes must match. command is a nonempty argv array, recorded data only. Retain execution logs and inspect causal lineage independently; matching text does not prove production.
""")
 # Host invocation metadata is replaced, while every original domain question
 # remains in the operative review packet and report schema.
 body=body.replace('> Resolve this reviewer slot first; the following is the `backend=codex` example.','Use this packet with the supported native reviewer interface and the current user-selected model/effort:')
 body=body.replace('spawn_agent:\n  model: gpt-6-astra\n  reasoning_effort: ultra\n  message: |','Independent read-only review packet:\n  message: |')
 body=body.replace('"codex-gpt-6-astra"','"<actual executor model>"').replace('"gpt-6-astra"','"<actual reviewer model>"').replace('"openai"','"<actual family, if known>"').replace('"ultra"','"<actual reviewer effort>"').replace('"gpt-6-astra-ultra"','"<actual reviewer and effort>"')
 body=body.replace('.aris/traces/experiment-audit/2026-04-10_run01/','<owning task review evidence path>')
 a=body.index('## Review Tracing')
 body=body[:a]+"""## Review Tracing

Retain the original reviewer packet, raw returned response, normalized checks/verdict, routing action, input hashes and actual reviewer identity/scope in the owning task's existing evidence location. An existing report can hold these fields; no compulsory duplicate files, ARIS trace directory, queue or graph is required. A transport error is not a completed review. Preserve any explicit user-requested reviewer condition and report unavailable coverage.
"""
 binding="""Use the current native host, user-selected model/effort and existing task authority. Keep the source's artifact collection, independent questions, report fields and verdict transitions below. No ARIS model router, remote tracker, queue, wiki or automatic experiment is activated. Explicit user-requested review requirements remain controlling; an unavailable review remains unavailable.\n\n"""
 title_end=body.index('\n\n')+2;body=body[:title_end]+binding+body[title_end:]
 from patch_hf import SPLIT
 active='---\nname: '+name+'\ndescription: '+description+'\n---\n\n'+body+'\n'+SPLIT
 path=out/'SKILL.md';path.write_text(active)
 archive=out/'upstream/SKILL.md.reference.txt';archive.parent.mkdir(exist_ok=True);archive.write_text(original)
 (out/'NATIVE-ADAPTATION.json').write_text(json.dumps({'repository':'wanshuiyin/Auto-claude-code-research-in-sleep','revision':'f76ec8d6b77792e2242cca049e08d0cbb7d54e19','source_path':'skills/skills-codex/'+name+'/SKILL.md','adaptation':'source-preserving-research-method-v1','source_sha256':hashlib.sha256(original.encode()).hexdigest(),'adapted_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'archival_original':'upstream/SKILL.md.reference.txt','operative_domain_method':'SKILL.md','adapted_hash_stage':'natural native entry name','port_sha256':hashlib.sha256(P(__file__).read_bytes()).hexdigest()},sort_keys=True,indent=2)+'\n')


def patch(name,out):
 p=out/'SKILL.md';original=p.read_text();refs=out/'references';refs.mkdir(exist_ok=True)
 if name in ('experiment-audit','result-to-claim'):
  port_review_method(name,original,out)
 elif name=='lean-formalize':
  header=original[:original.index('\n---',4)+4];header=re.sub(r'(?m)^allowed-tools:.*\n','',header)
  body=original[original.index('## When to use Lean'):]
  start=body.index('### Host execution and review');end=body.index('## 5. Verify the actual final target',start)
  body=body[:start]+'''### Host execution and independent review

Use the existing host/project conventions and current user-selected models/effort. Keep narrow lemma input/output contracts and independent statement alignment, proof obligations and exported theorem review where needed. No reviewer-family plumbing, routing overlay, shared queue or ARIS writes are required. Record the actual scope and limits of each review. Explicit user-requested reviewer conditions remain controlling; model agreement is not a proof.

'''+body[end:]
  body=body.replace('cross-family adversarial','independent adversarial')
  body=body.replace('Same-family\nopinions remain provisional; cross-family opinions are additional review\nevidence, not mathematical truth certificates.', 'Every model opinion is scoped review evidence, not a mathematical truth certificate. Record actual independent review and honor explicit user conditions without introducing a model-family acceptance rule.')
  body=re.sub(r'If a research wiki is active,.*?(?=Literature\nsearch)', 'Use the owning project\'s existing canonical notes for a durable claim correction; preserve source provenance and do not overwrite generated graphs. ',body,flags=re.S)
  body=body.replace('Use `proof-checker` for the existing ARIS proof-audit/submission role.','Keep an independent paper proof review distinct from Lean statement validation and experimental forensics.')
  body=body.replace("Apply an invoked ARIS loop's", "Apply the invoked project's")
  # No default cross-provider checkpoint condition is introduced by this port.
  body=re.sub(r'(?m)^.*base route.*same-family.*$', 'Record actual reviewer scope and remaining uncertainty.',body)
  p.write_text(header+'\n\n# Lean Formalize\n\n'+body)
  ref=refs/'adversarial-review.md';t=ref.read_text()
  start=t.index('## Checkpoint A');end=t.index('## A review response',start)
  checkpoints=t[start:end]
  # Retain the mathematical packets and probes, not provider bridge recipes.
  tail=t[end:]
  tail=re.sub(r'When an\nARIS reviewer contract.*?mathematical evidence\.', 'Any explicitly requested review contract remains controlling; judge the actual mathematical evidence.',tail,flags=re.S)
  tail=re.sub(r"Use the invoked ARIS loop's.*?Do not resubmit", 'Use the applicable user/project budget and actual availability. Do not resubmit',tail,flags=re.S)
  tail=tail.replace('Same-family help\ndoes not fulfill the missing cross-family review.', 'If the user explicitly required a particular reviewer, another reviewer does not silently replace that requirement.')
  ref.write_text('''# Independent adversarial review in a Lean proof project

Use proportionate independent review of statement alignment, load-bearing
arguments and final assembly. Preserve current user-selected models/effort and
existing authority. No ARIS routing, provider registry, compulsory model family
or automatic three-call sequence is introduced. Reuse unchanged evidence.
If the user explicitly requested a reviewer or independence condition, track it
and state any unmet condition. Model agreement never proves mathematics.

Give a fresh reviewer original sources and requirements without the builder's
persuasive account. Supply target, definitions, actual callers, lemma bodies,
axiom output and relevant logs. Distinguish source access, actual execution,
transport failure and mathematical findings. Use supported native tools only;
no paid service, bridge setup or remote disclosure is implied by this note.

'''+checkpoints+tail)
 else:raise ValueError('Research leaf is not mapped')
