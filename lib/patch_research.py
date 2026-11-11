"""Minimal native bindings for the selected upstream research methods."""
import difflib,hashlib,json,pathlib,re,shutil,textwrap
P=pathlib.Path
REPOSITORY='wanshuiyin/Auto-claude-code-research-in-sleep'
REVISION='f76ec8d6b77792e2242cca049e08d0cbb7d54e19'
BINDINGS="""# Native execution bindings

Use the current host's supported reviewer tools and user-selected model/effort.
Source examples do not authorize model changes, another provider, credential
access, new spending, or installing an ARIS controller. Keep every upstream
independence and review-family condition: if a required route is unavailable,
report that checkpoint pending rather than silently changing its acceptance rule.
Use task-owned output paths and retain the source's report fields and tracing.
A missing related skill/runtime is a capability gap, not an executed stage.

The original deterministic evidence checker is bundled at tools/evidence_check.py.
Invoke it by its absolute installed path with the explicit project directory and
batch file. Its value-existence result does not establish semantic claim support;
apply the independent review and integrity/confidence rules in the upstream method.
Before a checker run, resolve every batch source/glob against the authorized project
and reject outside-root paths, symlink escapes, credentials/configuration or private
knowledge targets. A generated citation path does not grant file-access authority.
External model/account transport helpers remain unadmitted; use supported native
connections only within their actual task and spending authority.
"""

def prompt(text):
 start=text.index('  message: |\n')+len('  message: |\n');end=text.index('\n```',start)
 return textwrap.dedent(text[start:end]).strip()+'\n'

def neutral(text):
 # Model names in execution examples are bindings, not changes to review methods.
 text=text.replace('Claude Code session','native host session')
 text=text.replace('spawn_agent:\n  model: gpt-6-astra\n  reasoning_effort: ultra\n  message: |','spawn_agent:\n  message: |')
 text=text.replace('Uses fresh-agent GPT-6-Astra review','Uses fresh independent-agent review')
 text=text.replace('"codex-gpt-6-astra"','"<actual executor model>"').replace('"gpt-6-astra"','"<actual reviewer model>"').replace('"gpt-6-astra-ultra"','"<actual reviewer model and effort>"')
 text=text.replace('"ultra"','"<actual reviewer effort>"')
 return text

def retain_method(name,original,out):
 active=neutral(original)
 end=active.index('\n---\n',4)+5 if active.startswith('---\n')else 0
 active=active[:end]+'\n> Native tool bindings: read [NATIVE-BINDINGS.md](NATIVE-BINDINGS.md).\n\n'+active[end:]
 (out/'SKILL.md').write_text(active)
 (out/'NATIVE-BINDINGS.md').write_text(BINDINGS)
 archive=out/'upstream/SKILL.md.reference.txt';archive.parent.mkdir(exist_ok=True);archive.write_text(original)
 (out/'NATIVE-PORT.patch').write_text(''.join(difflib.unified_diff(original.splitlines(keepends=True),active.splitlines(keepends=True),fromfile='upstream/SKILL.md',tofile='SKILL.md')))
 (out/'NATIVE-ADAPTATION.json').write_text(json.dumps({'repository':REPOSITORY,'revision':REVISION,'source_path':'skills/skills-codex/'+name+'/SKILL.md','adaptation':'upstream-method-minimal-native-binding-v2','source_sha256':hashlib.sha256(original.encode()).hexdigest(),'adapted_sha256':hashlib.sha256(active.encode()).hexdigest(),'archival_original':'upstream/SKILL.md.reference.txt','operative_domain_method':'SKILL.md','adapted_hash_stage':'natural native entry name','port_sha256':hashlib.sha256(P(__file__).read_bytes()).hexdigest()},sort_keys=True,indent=2)+'\n')

def port_review_method(name,original,out):
 retain_method(name,original,out)
 refs=out/'references';refs.mkdir(exist_ok=True)
 (refs/'review-prompt.md').write_text('# Independent read-only review prompt\n\n'+prompt(original))
 if name=='result-to-claim':
  import nstack
  source=nstack.acquire(REPOSITORY,REVISION)
  tools=out/'tools';tools.mkdir(exist_ok=True)
  shutil.copy2(source/'tools/evidence_check.py',tools/'evidence_check.py')

def patch(name,out):
 # Upstream names required shared protocols in plain text as well as links.
 # Retain the actual common documentation/helpers, not invented substitutes.
 import nstack
 source=nstack.acquire(REPOSITORY,REVISION)
 if out.parts[-3:]!=('skills','skills-codex',name):raise ValueError('Research support requires its source-relative entry layout')
 root=out.parents[2]
 for rel in ('skills/skills-codex/shared-references','skills/shared-references','tools'):
  shutil.copytree(source/rel,root/rel,dirs_exist_ok=True)
 original=(out/'SKILL.md').read_text()
 if name in ('experiment-audit','result-to-claim'):port_review_method(name,original,out)
 elif name=='lean-formalize':retain_method(name,original,out)
 else:raise ValueError('Research leaf is not mapped')
