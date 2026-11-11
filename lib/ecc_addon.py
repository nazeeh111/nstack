"""Two explicitly requested ECC additions; no ECC controller or hooks."""
import hashlib,json,pathlib,re
P=pathlib.Path
REPOSITORY='affaan-m/ECC'
REVISION='b38be6a7f6350964d59328b52f0624e1d1d552d1'
DESCRIPTIONS={
 'codebase-onboarding':'Explain an unfamiliar codebase with a source-backed onboarding guide, entrypoints, request lifecycle, conventions and task-to-file map. Use for an actual onboarding request; do not initialize project policy automatically.',
 'eval-harness':'Define and audit agent or prompt quality evaluations, negative controls and regression evidence. Includes offline capsule/replay utilities; candidate execution gate is unavailable and must remain closed.'}

BINDINGS = {
 'codebase-onboarding': """# Native host binding

Follow the complete upstream four-phase method and produce both outputs: the onboarding guide and starter project instructions. Claude/Claude Code and CLAUDE.md in the original map to the active host and AGENTS.md; native file listing/rg/read tools replace named source tools. Keep the user's model/effort and actual repository scope.

If AGENTS.md already exists, read it and preserve its bytes and unrelated instructions. Produce the second output as AGENTS.starter.md (or an owned task sideartifact) rather than automatically overwriting or changing existing policy; merge only within actual requested edit authority. If absent, the requested onboarding may produce the source's starter AGENTS.md. Keep source examples as examples, not detected facts. No credential-store or .env-value inspection, migration/server/account operation, controller/hooks or global initialization follows from onboarding.

The exact original is UPSTREAM_SKILL.md; active core changes only host names and this binding link.
""",
 'eval-harness': """# Native host binding

Follow the complete original EDD method below, including continuous development checks, its pass@k/pass^k targets and security human-review rule. Claude/Claude Code means the selected active host/model; native tools replace source tool names. Do not replace the method with a different grading framework or optional thresholds. Examples do not claim measured project results.

The source /eval operations are conceptual workflow names, not installed slash commands. Resolve .claude/evals to an explicit task-owned project evaluation directory, not another host's configuration. This entry lives at skills/eval-harness inside its bundle; scripts/, schemas/, examples/ and docs/ resolve two levels above it. Invoke actual retained helpers by absolute path and write only to the task-owned directory.

Retained Node helpers are unchanged. Their candidate execution gate is unavailable on every OS (gate.isolation_required): keep it closed, never bypass it, and never execute reward-hack fixtures as setup. Offline capsule/replay/receipt utilities do not establish isolation, truthful execution or promotion. Record mode directly invokes implementations; use only reviewed bounded local functions and synthetic/sanitized data. No provider signup, credentials, new spending, account operations or publication authority comes from this skill. Report missing capabilities instead of fabricating evaluation results.

The exact original is UPSTREAM_SKILL.md; active core changes only host names and this binding link.
"""
}

def definition(n,name):
 if name not in DESCRIPTIONS:raise ValueError('Unknown ECC addon')
 source=n.acquire(REPOSITORY,REVISION);entry=P('skills')/name/'SKILL.md';raw=(source/entry).read_text()
 # Preserve the complete frontmatter, method and examples. Only host names change.
 adapted=raw.replace('Claude Code','active host').replace('CLAUDE.md','AGENTS.md').replace('Claude','active host')
 end=adapted.index('\n---\n',4)+5
 adapted=adapted[:end]+'\n> Native tools/paths and execution limits: read [NATIVE-BINDINGS.md](NATIVE-BINDINGS.md). The original method follows.\n'+adapted[end:]
 parts=[str(entry),'LICENSE']
 if name=='eval-harness':parts+=['scripts/eval-harness.js','scripts/lib/eval-harness','schemas/capsule-envelope.schema.json','docs/architecture/eval-harness-frameworks.md','examples/eval-harness']
 frozen={}
 for part in parts:
  f=source/part
  for p in ([f] if f.is_file() else sorted(f.rglob('*'))):
   if p.is_symlink():raise ValueError('Linked ECC source is not allowed')
   if p.is_file():frozen[str(p.relative_to(source))]=(p.read_bytes(),0o555 if p.stat().st_mode & 0o111 else 0o444)
 if str(entry) not in frozen or 'LICENSE' not in frozen:raise ValueError('ECC owning source missing')
 import difflib
 patch=''.join(difflib.unified_diff(raw.splitlines(True),adapted.splitlines(True),fromfile='upstream/'+str(entry),tofile='native/'+str(entry)))
 binding=entry.parent/'NATIVE-BINDINGS.md';original=entry.parent/'UPSTREAM_SKILL.md';diff=entry.parent/'HOST-BINDING.patch'
 provenance={'repository':REPOSITORY,'revision':REVISION,'source_path':str(entry),'license':'MIT',
  'adaptation':'Complete original method/frontmatter retained with host-name substitutions and separate native tool/path/privacy/isolation bindings. Two onboarding outputs and original EDD rules preserved.',
  'source_files':{k:hashlib.sha256(v[0]).hexdigest() for k,v in frozen.items()},
  'native_bindings':str(binding),'original':str(original),'diff':str(diff),
  'native_entry_sha256':hashlib.sha256(adapted.encode()).hexdigest(),
  'native_bindings_sha256':hashlib.sha256(BINDINGS[name].encode()).hexdigest()}
 overrides={str(entry):adapted.encode(),str(original):raw.encode(),str(binding):BINDINGS[name].encode(),str(diff):patch.encode(),'SOURCE.json':(json.dumps(provenance,sort_keys=True,indent=2)+'\n').encode()}
 return {'source':source,'entry':entry.parent,'provenance':provenance,'overrides':overrides,'frozen_files':frozen}
