"""Codex ports of the three selected independent research-review stages."""
import pathlib,re,textwrap,shutil
P=pathlib.Path

def prompt(text):
 start=text.index('  message: |\n')+len('  message: |\n');end=text.index('\n```',start)
 return textwrap.dedent(text[start:end]).strip()+'\n'

def patch(name,out):
 p=out/'SKILL.md';original=p.read_text();refs=out/'references';refs.mkdir(exist_ok=True)
 if name in ('experiment-audit','result-to-claim'):
  review=prompt(original);(refs/'review-prompt.md').write_text('# Independent read-only review prompt\n\nUse the actual supplied artifacts as evidence. Preserve current user model/effort choices. No runtime routing or network service is selected by this prompt.\n\n'+review)
  if name=='experiment-audit':
   method=original[original.index('## Why This Exists'):original.index('## Constants')];method=re.sub(r'## Core Principle.*','',method,flags=re.S)
   description='Independently audit experiment ground truth, normalization, result provenance, dead evaluation paths and scope before making a claim.'
   body='''# Experiment integrity audit

Collect the actual original data, split artifacts, preprocessing, evaluation entrypoint, configs, outputs and raw logs. Record artifact hashes and the current producing commit/runtime lock. Distinguish reported results from re-executed results; a file's existence does not establish that its claimed producer ran.

'''+method+'''
## Independent review

Give a fresh read-only reviewer the requirements and artifacts plus [the original scoped review questions](references/review-prompt.md). Preserve user model/effort selections and use supported host tools. The builder's persuasive narrative is not evidence. No ARIS router, model-family acceptance rule, forced trace graph, queue or secondary runtime is required. Preserve any explicit user-requested independent review condition; if unavailable, state the actual gap.

Keep the four integrity probes, original data/splits/entrypoint, raw logs and failure consequences for each claim. Check an independent result producer where feasible. Ground truth derived from outputs must be labeled as a proxy. Reject post-hoc score normalization, orphan metrics and unreachable evaluation paths as support for the affected claims. Unknown provenance remains unknown; it does not establish fabrication.

'''
  else:
   description='Map observed experiment results to the strongest supportable claim, fair baseline, contrary evidence and missing evidence.'
   body='''# Result to claim

Read actual project results, fair baseline sources, intended claims, configs, split/run hashes and material caveats. Use the narrow input/output handoff from an experiment audit when available; absent audit evidence remains absent. Do not query a tracking service, upload traces or start new jobs merely to review a claim.

## Deterministic evidence reconciliation

Use `python3 tools/evidence_check.py PROJECT CLAIMS_JSON --root RESULTS_ROOT --root SOURCE_ROOT` from this leaf. Roots are explicit project-relative directories. Each claim names its exact JSON Pointer or CSV header/unique row key, value and hashed provenance receipt. The receipt must bind unit, metric, split/run paths and hashes, producing argv, artifact hash and producing source hashes. See [the schema](references/evidence-schema.md). The helper never executes the recorded command. `consistent-record` means structured records agree; it cannot establish execution, causal provenance, fair splitting or the claim itself. Any missing/ambiguous/inconsistent input is `unknown`, never an inference of fabrication. Bypass an unsuitable helper and inspect structured evidence directly rather than substituting a lexical hit.

## Claim judgment

Supply the requirements and actual evidence to a fresh read-only reviewer using [the selected evaluation questions](references/review-prompt.md). Preserve existing model/effort choices; no ARIS or reviewer-family plumbing is required. Report yes, partial, no or unknown with what the results support, what they do not support, contrary evidence, confounds, the strongest defensible revision and the smallest resolving experiment. A single dataset does not establish broad generalization. Deterministic evidence consistency never upgrades semantic acceptance by itself.

Record the decision in the project's existing notes only where a durable handoff needs it. Do not create compulsory duplicate output files, mutate generated knowledge graphs, update a queue, publish data or automatically launch another pipeline. Follow the requested task's authority for any further experiment or revision.

'''
   tools=out/'tools';tools.mkdir(exist_ok=True);shutil.copy2(P(__file__).parent/'claim_evidence.py',tools/'evidence_check.py')
   (refs/'evidence-schema.md').write_text('''# Structured evidence schema

Claims JSON is an array. Each record has id, path, format, value and provenance. JSON adds pointer (RFC6901); CSV adds column and row_key:{column,value}. All paths are project-relative and must resolve within explicit --root directories. Globs must identify one regular file; symlink escapes and ambiguous rows are rejected before reading content.

provenance is {path,sha256,unit,metric,split_sha256,run_sha256,command}. Its path identifies a JSON receipt whose SHA256 matches. The receipt repeats these fields and adds split_path,run_path,artifact_sha256,sources:[{path,sha256}]. The actual split/run/source/artifact bytes must match their hashes. command is a nonempty argv array, recorded data only. Retain actual runtime execution logs and inspect causal lineage independently. A source file with the right text is not proof it generated the result.
''')
  from patch_hf import SPLIT
  p.write_text('---\nname: '+name+'\ndescription: '+description+'\n---\n\n'+body+'\n'+SPLIT)
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
