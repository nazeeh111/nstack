"""Offline replay of the exact selected OfficeCLI/P343 source methods, not runtimes."""
import difflib, hashlib, json, os, pathlib, re, subprocess, sys, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'lib')]
from skill_build import materialize
from closure import validate
from patch_prospecting import FILES
P=pathlib.Path
SOURCES={'P333':('iOfficeAI/OfficeCLI','c56512c8c7b76fe284f09940e4cd492470099d3e','NSTACK_OFFICE_SOURCE'),'P343':('coreyhaines31/marketingskills','88c79f6528a9347420e57ceb1fff9a60de651768','NSTACK_MARKETING_SOURCE')}

def block(text,start,end):return text[text.index(start):text.index(end,text.index(start)+len(start))]

class SourceFidelity(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.sources={}
  for cid,(repo,pin,key) in SOURCES.items():
   p=P(os.environ.get(key,P.home()/'Library/Application Support/nstack/sources'/repo.replace('/','--')/pin))
   if not (p/'.nstack-source.json').exists():raise unittest.SkipTest('Exact offline source unavailable; no acquisition: '+repo)
   receipt=json.loads((p/'.nstack-source.json').read_text());assert (receipt['repository'],receipt['revision'])==(repo,pin)
   for rel,digest in receipt['files'].items():
    if hashlib.sha256((p/rel).read_bytes()).hexdigest()!=digest:raise AssertionError('Pinned source drift: '+rel)
   cls.sources[cid]=p
  cls.temp=tempfile.TemporaryDirectory(prefix='nstack-source-fidelity-');cls.addClassCleanup(cls.temp.cleanup)
  cls.registry=json.loads((ROOT/'registry/manifest.json').read_text());comps={c['id']:c for c in cls.registry['components']};cls.outputs={}
  for spec in cls.registry['skills']:
   if spec['candidate_id']!='P333' and not(spec['candidate_id']=='P343' and P(spec['source_path']).parent.name in ('prospecting','cold-email')):continue
   name=P(spec['source_path']).parent.name if spec['source_path']!='SKILL.md' else 'officecli'
   out=P(cls.temp.name)/name;out.mkdir();entry=materialize(cls.sources[spec['candidate_id']],out,spec,comps[spec['candidate_id']],cls.registry);cls.outputs[name]=(out,out/entry/'SKILL.md',spec)

 def test_every_real_bundle_links_and_source_receipt_are_complete(self):
  self.assertEqual(len(self.outputs),6)
  for name,(out,entry,spec) in self.outputs.items():
   with self.subTest(name=name):
    validate(out);receipt=json.loads((out/'SOURCE-ADAPTATION.json').read_text());self.assertEqual(receipt['revision'],spec['revision'])
    records=receipt.get('files',[receipt]);self.assertEqual(len(records),8 if spec['candidate_id']=='P343' else 1)
    for row in records:
     raw=(self.sources[spec['candidate_id']]/row['source_path']).read_bytes();active=(out/row['active_path']).read_bytes()
     self.assertEqual((out/row['archive']).read_bytes(),raw)
     self.assertEqual(hashlib.sha256(raw).hexdigest(),row['source_sha256']);self.assertEqual(hashlib.sha256(active).hexdigest(),row['active_sha256'])
     expected=''.join(difflib.unified_diff(raw.decode().splitlines(True),active.decode().splitlines(True),fromfile=row['source_path'],tofile=row['active_path']))
     self.assertEqual((out/row['diff']).read_text(),expected)
    self.assertIn('License',(out/'LICENSE').read_text())

 def test_office_actual_format_methods_are_retained_byte_for_byte(self):
  spans={'officecli':[('## L1: Create, Read & Inspect','## Watch & Interactive Selection'),('## L2: DOM Operations','## L3: Raw XML')],
   'officecli-docx':[('### Fields (PAGE','### Headers & Footers'),('### Tables','### Lists'),('## Raw-set XML appendix','### Help pointer')],
   'officecli-xlsx':[('## CSV / bulk import','## Reading & Analysis'),('### Named ranges','### Charts'),('### Charts','### Conditional formatting')],
   'officecli-pptx':[('### Charts','### Pictures'),('### Connectors','### Hyperlinks'),('### Deck-level recipes','## QA')]}
  for name,ranges in spans.items():
   out,entry,spec=self.outputs[name];raw=(self.sources['P333']/spec['source_path']).read_text();active=entry.read_text()
   for a,b in ranges:self.assertEqual(block(active,a,b),block(raw,a,b),(name,a))
   source_lines=[l for l in raw.splitlines() if l.strip()];active_lines=set(active.splitlines());retained=sum(l in active_lines for l in source_lines)/len(source_lines)
   self.assertGreater(retained,.82,(name,retained))

 def test_office_corrected_runtime_conflicts_leave_checks_and_methods(self):
  for name in ['officecli','officecli-docx','officecli-xlsx','officecli-pptx']:
   text=self.outputs[name][1].read_text();self.assertIn('OFFICECLI_NO_AUTO_RESIDENT=1',text);self.assertIn('actual artifact',text)
   self.assertNotIn('`load_skill` once',text);self.assertNotIn('**Before doc work, check Specialized Skills**',text)
   self.assertIsNone(re.search(r'(?m)^officecli open ',text))
   self.assertNotIn('curl -fsSL',text);self.assertNotIn('irm https:',text);self.assertNotIn('max 3 cycles',text)
   self.assertNotIn('workflow or permission grant',text);self.assertNotIn('syntax/reference material',text)
  xlsx=self.outputs['officecli-xlsx'][1].read_text();self.assertIn('calculateAll',xlsx);self.assertIn('storeAsURL',xlsx)
  self.assertNotIn('re-touch the formula via `set` (forces recompute) or manually set',xlsx)
  self.assertNotIn('No exceptions — guard denominators',xlsx)
  self.assertIn('### Formula verification checklist',xlsx)

 def test_restored_real_shell_methods_still_parse_without_execution(self):
  # Parse complete concrete source-derived recipes; placeholders/help signatures are not runnable scripts.
  selected={'officecli-xlsx':[('## CSV / bulk import','## Reading & Analysis'),('### Charts','### Conditional formatting')],
            'officecli-docx':[('### Fields (PAGE','### Headers & Footers')],
            'officecli-pptx':[('### Deck-level recipes','## QA')]}
  count=0
  for name,ranges in selected.items():
   text=self.outputs[name][1].read_text()
   for a,b in ranges:
    for code in re.findall(r'(?ms)^```(?:bash|sh)\n(.*?)^```',block(text,a,b)):
     result=subprocess.run(['/bin/bash','-n'],input=code,text=True,capture_output=True);self.assertEqual(result.returncode,0,result.stderr);count+=1
  self.assertGreaterEqual(count,7)

 def test_marketing_original_domain_procedures_survive_exact_selected_scope(self):
  out,entry,spec=self.outputs['cold-email'];raw=(self.sources['P343']/spec['source_path']).read_text();active=entry.read_text()
  for a,b in [('### Write like a peer','### One ask'),('## Voice & Tone','## Structure'),('## Quality Check','## What to Avoid')]:self.assertEqual(block(active,a,b),block(raw,a,b))
  self.assertIn('**Observation → Problem → Proof → Ask**',active);self.assertIn('## Subject Lines',active)
  checks={FILES[2]:['## Step 2 — Mine the five signal buckets','**Explicit demand**','**Workaround**','### Prospect stages'],FILES[3]:['## Where the useful facts are','**Facts first, angle second.**','**Quote, don\'t paraphrase'],FILES[4]:['## Four Levels of Personalization','## Research Signal Stack','**Step 2:** Build a 3x3 template','## The "So What?" Test'],FILES[5]:['## Classify every reply','## Objections in reply to cold outreach','"How did you get my email?"'],FILES[7]:['## Coding Scheme','## Sources and Their Bias','## Report Format','**One primary reason per deal**']}
  for rel,needles in checks.items():
   text=(out/rel).read_text()
   for needle in needles:self.assertIn(needle,text,(rel,needle))
  self.assertEqual({str(p.relative_to(out)) for p in (out/'skills').rglob('*') if p.is_file()},set(FILES))
  life=(out/FILES[6]).read_text();self.assertIn('## Outbound Stages',life);self.assertNotIn('## MQL Criteria',life);self.assertNotIn('same definition as inbound',life);self.assertIn('source-backed criteria',life)
  self.assertEqual((self.outputs['prospecting'][0]/'SOURCE-ADAPTATION.json').read_bytes(),(out/'SOURCE-ADAPTATION.json').read_bytes())

 def test_marketing_refs_carry_authority_and_stop_state_without_provider_graph(self):
  out=self.outputs['prospecting'][0]
  for rel in FILES:
   text=(out/rel).read_text();self.assertIn('## Native scope',text)
   self.assertNotIn('tools/REGISTRY.md',text)
   for excluded in ['sourcing-and-enrichment.md','multichannel-cadence.md','frameworks.md','creative-review-page.md']:self.assertNotIn(']('+excluded,text)
  reply=(out/FILES[5]).read_text();self.assertIn('Pause without automatic resumption',reply);self.assertIn('Unknown provider outcomes remain held',reply);self.assertIn('no inherited send authority',reply)
  self.assertNotIn('Before an agent sends anything on its own',reply)
  result=subprocess.run([sys.executable,str(ROOT/'tests/check_p343_closure.py'),str(out)],capture_output=True,text=True);self.assertEqual(result.returncode,0,result.stdout+result.stderr)

if __name__=='__main__':unittest.main()
