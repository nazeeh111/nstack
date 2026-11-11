"""Offline source-method replay for P001 and MCP builder; no target runtime."""
import hashlib,json,pathlib,re,sys,tempfile,tomllib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'lib')]
from skill_build import materialize
from closure import validate
from native_setup import selection
from patch_native34 import prose_only
P=pathlib.Path
def natural(text,name):return re.sub(r'(?m)^name:.*$', 'name: '+name,text,count=1)

class MethodFidelity(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.registry=json.loads((ROOT/'registry/manifest.json').read_text());comps={c['id']:c for c in cls.registry['components']};cls.temp=tempfile.TemporaryDirectory(prefix='nstack-method-fidelity-');cls.addClassCleanup(cls.temp.cleanup);cls.outputs={};cls.sources={}
  plain_science={'uncertainty-and-units','hypothesis-generation','experimental-design','statistical-power','citation-management','lab-hardware-cad','scientific-writing','statistical-analysis','qutip'}
  targets=[s for name,s in selection() if(s['candidate_id']=='P001' and s['delivery']=='narrow-patched leaf')or(s['candidate_id']=='L010' and P(s['source_path']).parent.name=='mcp-builder')or(s['candidate_id']=='P195' and P(s['source_path']).parent.name=='differential-review')or(s['candidate_id']=='L014' and s['delivery']=='narrow-patched leaf')or(s['candidate_id']=='L050' and P(s['source_path']).parent.name=='physical-ai-physics-selection')or(s['candidate_id']=='P112' and P(s['source_path']).parent.name in plain_science)or s['candidate_id'] in('P328','X-CREATIVE-COLORFIGURES','P200','P056','P295','P183')]
  refs=[s for s in cls.registry['skills']if s['candidate_id']=='P001' and s['delivery']=='selective-merge reference']
  for s in targets+refs:
   key=(s['source_repository'],s['revision']);source=P.home()/'Library/Application Support/nstack/sources'/key[0].replace('/','--')/key[1]
   if not(source/'.nstack-source.json').is_file():raise unittest.SkipTest('Pinned offline source absent: '+str(key))
   receipt=json.loads((source/'.nstack-source.json').read_text());assert(receipt['repository'],receipt['revision'])==key
   cls.sources[key]=source
   # Exact selected closure and named reference only; do not execute or acquire source.
   for f in (source/P(s['source_path']).parent).rglob('*'):
    if f.is_file()and f.name!='.nstack-source.json':assert hashlib.sha256(f.read_bytes()).hexdigest()==receipt['files'][str(f.relative_to(source))]
  for s in targets:
   source=cls.sources[s['source_repository'],s['revision']];name=s.get('native_name')or P(s['source_path']).parent.name or s['source_repository'].split('/')[-1];out=P(cls.temp.name)/name;out.mkdir()
   support={r['source_repository']:cls.sources[r['source_repository'],r['revision']]for r in refs}
   entry=materialize(source,out,s,comps[s['candidate_id']],cls.registry,support)or'.';cls.outputs[name]=(source/s['source_path'],out,out/entry/'SKILL.md')

 def test_reproduction_method_is_exact_original(self):
  raw,out,entry=self.outputs['diagnosing-bugs'];self.assertEqual(natural(entry.read_text(),'diagnosing-bugs'),raw.read_text())
  # Includes unavailable-loop handling, red-capable observed command and minimization transitions.
  self.assertIn('Do **not** proceed to hypothesise without a loop.',entry.read_text())

 def test_tdd_only_changes_unavailable_host_dispatch(self):
  raw,out,entry=self.outputs['tdd'];expected=raw.read_text().replace('call the Skill tool with "codebase-design"','read the selected "codebase-design" skill')
  self.assertEqual(natural(entry.read_text(),'tdd'),expected)
  self.assertIn('No test is written at an unconfirmed seam.',entry.read_text())

 def test_design_vocabulary_and_independent_comparison_are_retained(self):
  raw,out,entry=self.outputs['codebase-design'];active=entry.read_text();self.assertTrue(natural(active,'codebase-design').startswith(raw.read_text()))
  self.assertEqual((out/'DESIGN-IT-TWICE.md').read_bytes(),(raw.parent/'DESIGN-IT-TWICE.md').read_bytes())
  deep=(raw.parent/'DEEPENING.md').read_text();expected=re.sub(r'(?m)^.*Old unit tests.*$', 'Retire existing internal tests only after demonstrating behavior parity and a discriminating replacement. Retain public, safety and compatibility probes where they cover behavior the replacement does not.',deep)
  self.assertEqual((out/'DEEPENING.md').read_text(),expected)
  self.assertNotEqual(deep,expected)
  self.assertIn('Caldo’s diagnostic inventory',active)

 def test_mcp_domain_method_and_evaluation_are_exact(self):
  raw,out,entry=self.outputs['mcp-builder'];source=raw.read_text();active=entry.read_text()
  for start,end in [('### 1.1 Understand Modern MCP Design','### 1.2 Study MCP Protocol Documentation'),('#### 1.4 Plan Your Implementation','### Phase 2: Implementation'),('### Phase 4: Create Evaluations',None)]:
   a=source.index(start);b=source.index(end,a+len(start))if end else len(source);expected=source[a:b].replace('Use web search and WebFetch as needed.','Use native primary-source documentation retrieval as needed.')
   self.assertIn(expected,active)
  for rel in ['reference/evaluation.md','reference/mcp_best_practices.md','reference/python_mcp_server.md','reference/node_mcp_server.md','reference/node_mcp_server_v2.md']:
   self.assertEqual((out/rel).read_bytes(),(raw.parent/rel).read_bytes(),rel)
  self.assertNotIn('## Target protocol acceptance',active)
  self.assertIn('Respect the project\'s locked SDK',active)
  self.assertNotIn('Use WebFetch to load',active)

 def test_actual_bundle_support_resolves(self):
  self.assertEqual(len(self.outputs),22)
  for name,(raw,out,entry)in self.outputs.items():
   with self.subTest(name=name):validate(out)

 def test_original_report_format_and_synthesis_count_survive(self):
  raw,out,entry=self.outputs['differential-review'];source=raw.read_text();active=entry.read_text()
  for line in source.splitlines():
   if any(t in line for t in ['Output-Driven','Always write report','Report file generated','Always generate the output file','Output report only to chat']):self.assertIn(line,active)
  self.assertIn('severity follows supported impact',active)
  raw,out,entry=self.outputs['synthesize-research'];self.assertIn('For each major finding (aim for 5-8):',entry.read_text())

 def test_physics_selection_method_is_exact_source(self):
  raw,out,entry=self.outputs['physical-ai-physics-selection'];self.assertEqual(natural(entry.read_text(),'physical-ai-physics-selection'),raw.read_text())

 def test_scientific_domain_methods_have_no_added_acceptance_essays(self):
  names=['uncertainty-and-units','hypothesis-generation','experimental-design','statistical-power','citation-management','lab-hardware-cad','scientific-writing','statistical-analysis','qutip']
  for name in names:
   with self.subTest(name=name):
    raw,out,entry=self.outputs[name];expected=raw.read_text()
    if '## Citing Scientific Agent Skills' in expected:expected=expected[:expected.index('## Citing Scientific Agent Skills')].rstrip()+'\n'
    expected=re.sub(r'(?m)^allowed-tools:.*\n','',expected)
    self.assertEqual(natural(entry.read_text(),name),expected)

 def test_visual_source_confirmation_and_iteration_limits_survive(self):
  raw,out,entry=self.outputs['colorfigures'];source=raw.read_text();active=entry.read_text()
  # Only the selected activation description/name may differ.
  def body(text):return text.split('\n---\n',1)[1]
  self.assertEqual(body(active),body(source))
  raw,out,entry=self.outputs['diagram-design'];source=raw.read_text();active=entry.read_text();a=source.index('### Confirm before drawing');b=source.index('\n---',a)
  self.assertIn(source[a:b],active)
  self.assertEqual((out/'scripts/verify-geometry.py').read_bytes(),(raw.parents[2]/'scripts/verify-geometry.py').read_bytes())

 def test_taste_original_imagery_house_rules_and_inspector_survive(self):
  raw,out,entry=self.outputs['taste-skill'];source=raw.read_text();active=entry.read_text()
  self.assertEqual(active.split('\n---\n',1)[1],source.split('\n---\n',1)[1])
  self.assertEqual((out/'scripts/inspect.mjs').read_bytes(),(raw.parent/'scripts/inspect.mjs').read_bytes())

 def test_native_entries_use_actual_bindings_without_repeated_scope_essay(self):
  for name in ['worktrunk','godot-production-checks']:
   raw,out,entry=self.outputs[name];active=entry.read_text()
   self.assertNotIn('Use this specialist on demand',active);self.assertNotIn('## Native execution',active)
  raw,out,entry=self.outputs['worktrunk'];self.assertIn('use existing available Codex access',entry.read_text())
  raw,out,entry=self.outputs['godot-production-checks'];self.assertEqual((out/'upstream'/raw.relative_to(self.sources['htdt/godogen','40542b6c8efbdc40112c2b004fbaa6d67141846d'])).read_bytes(),raw.read_bytes())

 def test_all_97_originally_valid_toml_examples_still_parse(self):
  checked=0
  for name in ['worktrunk','cocoindex']:
   raw,out,entry=self.outputs[name]
   for original in raw.parent.rglob('*.md'):
    current=entry.parent/original.relative_to(raw.parent)
    before=re.findall(r'(?ms)^```toml[^\n]*\n(.*?)^```',original.read_text());after=re.findall(r'(?ms)^```toml[^\n]*\n(.*?)^```',current.read_text())
    self.assertEqual(len(before),len(after),str(original))
    for source,active in zip(before,after):
     try:tomllib.loads(source)
     except tomllib.TOMLDecodeError:continue  # Source may deliberately show a fragment.
     tomllib.loads(active);checked+=1
     config=tomllib.loads(active)
     command=config.get('commit',{}).get('generation',{}).get('command','')
     if command.startswith('codex '):self.assertEqual(command,'codex exec --ephemeral --sandbox=read-only -')
  self.assertEqual(checked,97)
  raw,out,entry=self.outputs['worktrunk']
  text=(entry.parent/'reference/llm-commits.md').read_text();self.assertNotIn('Create `~/.codex/worktrunk-commit-instructions',text);self.assertNotIn('Requires `jq`',text)

 def test_prose_host_port_preserves_fenced_executable_bytes(self):
  fixture='Claude Code\n```toml\ncommand = "claude -p --model=haiku"\n```\n~~~yaml\nmodel: opus\nsubagent_type: reviewer\n~~~\nCLAUDE.md\n'
  expected=fixture.replace('Claude Code\n','Codex\n',1).removesuffix('CLAUDE.md\n')+'AGENTS.md\n'
  self.assertEqual(prose_only(fixture,lambda t:t.replace('Claude Code','Codex').replace('CLAUDE.md','AGENTS.md')),expected)

if __name__=='__main__':unittest.main()
