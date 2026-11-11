"""Offline preservation checks for remaining source ports; no external service or simulator."""
import ast, hashlib, json, math, os, pathlib, shutil, subprocess, sys, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'lib'))
import patch_business, patch_hardware, patch_conditional, patch_dcc
from closure import validate
P=pathlib.Path
PINS={'seo':('AgriciDaniel/claude-seo','6be93f45064ffbadced572b5d5c95f55fd263af0'),
      'ads':('AgriciDaniel/claude-ads','fc3908e786c318776df89a3a098333da377364be'),
      'marketing':('coreyhaines31/marketingskills','88c79f6528a9347420e57ceb1fff9a60de651768'),
      'hardware':('aklofas/kicad-happy','c451943f72d91a4a9fbf4aa48bda0f730011f6d8')}
class RemainingPorts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.sources={}
  for key,(repo,pin) in PINS.items():
   source=P(os.environ.get('NSTACK_'+key.upper()+'_SOURCE',P.home()/'Library/Application Support/nstack/sources'/repo.replace('/','--')/pin))
   if not (source/'.nstack-source.json').is_file():raise unittest.SkipTest('Exact offline cache unavailable: '+repo)
   receipt=json.loads((source/'.nstack-source.json').read_text());assert (receipt['repository'],receipt['revision'])==(repo,pin)
   for rel,digest in receipt['files'].items():
    assert hashlib.sha256((source/rel).read_bytes()).hexdigest()==digest,(repo,rel)
   cls.sources[key]=source
 def leaf(self,key,name,transform):
  temp=tempfile.TemporaryDirectory(prefix='nstack-method-preservation-',dir='/private/tmp');self.addCleanup(temp.cleanup)
  source=self.sources[key];out=P(temp.name)/name;shutil.copytree(source/'skills'/name,out)
  original=(out/'SKILL.md').read_text();transform(source,out);return out,original
 def check_role_sources(self,key,out):
  rows=json.loads((out/'references/domain-prompts-source.json').read_text())
  for row in rows:
   self.assertEqual((out/row['path']).read_bytes(),(self.sources[key]/row['source_path']).read_bytes())
   self.assertEqual(hashlib.sha256((out/row['path']).read_bytes()).hexdigest(),row['sha256'])
  validate(out)
  self.assertEqual(len(list(out.rglob('SKILL.md'))),1)
  return rows
 def test_seo_full_domain_plan_and_exact_prompts_are_retained(self):
  out,raw=self.leaf('seo','seo-audit',lambda source,out:patch_business.patch('P347','seo-audit',source,out));active=(out/'SKILL.md').read_text()
  roles=__import__('re').findall(r'^   - `(seo-[a-z-]+)`',raw,__import__('re').M)
  self.assertEqual(len(roles),17)
  for role in roles:self.assertIn('`'+role+'`',active)
  for clause in ['otherwise run inline sequentially','Max pages: 500','Concurrent requests: 5','always include in full audits','Always offer PDF generation']:
   self.assertIn(clause,active)
  self.assertNotIn('auth.py --check',active)
  self.assertEqual(len(self.check_role_sources('seo',out)),18)
 def test_ads_original_independent_worker_contract_is_active(self):
  out,raw=self.leaf('ads','ads-audit',lambda source,out:patch_business.patch('P351','ads-audit',source,out));active=(out/'SKILL.md').read_text()
  self.assertTrue(active.startswith(raw));self.assertEqual(len(self.check_role_sources('ads',out)),18)
  self.assertIn('Dispatch independent platform workers and cross-platform workers in parallel.',active)
  self.assertIn('Use a dedicated worker for every selected platform:',active)
 def test_marketing_startup_and_diagnosis_are_not_rewritten(self):
  for name in ['product-marketing','copywriting']:
   out,raw=self.leaf('marketing',name,lambda source,out:patch_business.patch('P343',name,source,out))
   self.assertEqual((out/'SKILL.md').read_text(),raw)
  out,raw=self.leaf('marketing','pricing',lambda source,out:patch_business.patch('P343','pricing',source,out))
  active=(out/'SKILL.md').read_text();self.assertIn('### The $10 / $100 / $1,000 rule of thumb',active)
  ref=(out/'references/pricing-models.md').read_text();original=(self.sources['marketing']/'skills/pricing/references/pricing-models.md').read_text()
  note='\n\nSource claim, not an established general rule: the cited churn relationship and roughly 2x discount effect require verification for the actual market; do not infer causation or a price change from them alone.'
  self.assertEqual(ref.replace(note,''),original)
 def test_upstream_divider_payloads_keep_metadata_and_numerical_verdicts(self):
  out,raw=self.leaf('hardware','spice',lambda source,out:patch_hardware.patch('spice',source,out))
  text=(out/'scripts/spice_results.py').read_text();tree=ast.parse(text);ns={}
  nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('evaluate_voltage_divider','evaluate_feedback_network')]
  exec(compile(ast.Module(body=nodes,type_ignores=[]),str(out/'scripts/spice_results.py'),'exec'),ns)
  det={'ratio':.5,'r_top':{'ref':'R1','ohms':1000},'r_bottom':{'ref':'R2','ohms':1000},'top_net':'+5V','mid_net':'FB','bottom_net':'GND','mid_point_connections':[{'component':'U1','pin_name':'FB'}], '_context':{'findings':[{'detector':'detect_power_regulators','ref':'U1','vref_source':'fixture','estimated_vout':5,'topology':'buck','output_rail':'+5V'}]}}
  for name in ['evaluate_voltage_divider','evaluate_feedback_network']:
   f=ns[name]
   for expected,measured,error,status in [(2.5,2.5,0,'pass'),(-2.5,-2.5,0,'pass'),(-2.5,-1,60,'fail'),(2.5,2.49,.4,'warn'),(2.5,1,60,'fail'),(2.5,1,0,'skip'),(None,2.5,0,'skip'),(2.5,math.nan,0,'skip'),(math.inf,2.5,0,'skip')]:
    result=f(det,{'expected':expected,'vout_sim':measured,'error_pct':error})
    self.assertEqual(result['status'],status,(name,expected,measured,result))
    self.assertEqual(result['components'],['R1','R2'])
   if name.endswith('feedback_network'):
    result=f(det,{'expected':2.5,'vout_sim':2.5,'error_pct':0});self.assertEqual(result['regulator'],'U1');self.assertEqual(result['regulator_info']['topology'],'buck')
  self.assertNotIn('nstack_accepted_circuit_model',text)
  # The real upstream generators produce this supported expectation field.
  # Generate netlist text only; never launch a simulator or hardware driver.
  program='''import json,sys
sys.dont_write_bytecode=True
sys.path.insert(0,sys.argv[1])
sys.path.extend([sys.argv[3]+"/skills/kicad/scripts",sys.argv[3]+"/skills/datasheets/scripts"])
from spice_templates import generate_voltage_divider,generate_feedback_network
det=json.loads(sys.argv[2])
cases=[]
for f in (generate_voltage_divider,generate_feedback_network):
 for source,vin in [(det,3.3),(dict(det,top_net="SUPPLY"),-5)]:
  bench=f(source,"fixture.out",vin=vin)
  cases.append(dict(bench.extra_vars,error_expression=[m[2] for m in bench.measurements if m[0]=="error_pct"][0]))
print(json.dumps(cases))
'''
  result=subprocess.run([sys.executable,'-B','-c',program,str(out/'scripts'),json.dumps(det),str(self.sources['hardware'])],capture_output=True,text=True,timeout=10)
  self.assertEqual(result.returncode,0,result.stderr)
  for index,data in enumerate(json.loads(result.stdout)):
   self.assertEqual(float(data['expected']),2.5 if index%2==0 else -2.5)
   self.assertIn(' / 2.5 * 100',data['error_expression'])
if __name__=='__main__':unittest.main()
