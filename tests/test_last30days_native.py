"""Exact pinned-source anonymous adapter tests. No live accounts/network/provider calls."""
import difflib,hashlib,importlib.util,json,os,pathlib,shutil,subprocess,sys,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'lib')]
from skill_build import materialize
from closure import validate
PIN='71dc2a1529f23dfe7b0d0e3b3e11d4a7e8afd428'
P=pathlib.Path
class Last30daysNative(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.source=P(os.environ.get('NSTACK_LAST30DAYS_SOURCE',P.home()/'Library/Application Support/nstack/sources/mvanhorn--last30days-skill'/PIN))
  if not(cls.source/'.nstack-source.json').is_file():raise unittest.SkipTest('Exact pinned offline source unavailable; no acquisition')
  receipt=json.loads((cls.source/'.nstack-source.json').read_text());assert receipt['revision']==PIN
  for rel,h in receipt['files'].items():assert hashlib.sha256((cls.source/rel).read_bytes()).hexdigest()==h,rel
  cls.temp=tempfile.TemporaryDirectory(prefix='nstack-l30d-test-');cls.addClassCleanup(cls.temp.cleanup);cls.out=P(cls.temp.name).resolve()/'bundle';cls.out.mkdir();m=json.loads((ROOT/'registry/manifest.json').read_text());s=next(s for s in m['skills']if s['candidate_id']=='P111'and s['delivery']=='narrow-patched leaf');c=next(c for c in m['components']if c['id']=='P111');entry=materialize(cls.source,cls.out,s,c,m);cls.leaf=cls.out/entry;cls.wrapper=cls.leaf/'scripts/native_research.py'
  spec=importlib.util.spec_from_file_location('l30d_adapter_test',cls.wrapper);cls.adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.adapter)
 def test_full_pinned_engine_and_runtime_modules_unmodified_and_bound(self):
  validate(self.out);raw=self.source/'skills/last30days';seal=json.loads((self.out/'source/LAST30DAYS-NATIVE-PORT.json').read_text())
  for rel,h in seal['unmodified_script_hashes'].items():
   self.assertEqual((self.leaf/'scripts'/rel).read_bytes(),(raw/'scripts'/rel).read_bytes());self.assertEqual(hashlib.sha256((self.leaf/'scripts'/rel).read_bytes()).hexdigest(),h)
  self.assertEqual(hashlib.sha256(self.wrapper.read_bytes()).hexdigest(),seal['wrapper_sha256'])
 def test_changed_docs_have_exact_originals_and_replayable_diffs(self):
  raw=self.source/'skills/last30days';root=self.out/'source';seal=json.loads((root/'LAST30DAYS-NATIVE-PORT.json').read_text())
  for rel,row in seal['changes'].items():
   original=(raw/rel).read_bytes();active=(self.leaf/rel).read_bytes();self.assertEqual((root/row['archive']).read_bytes(),original)
   self.assertEqual(hashlib.sha256(original).hexdigest(),row['source_sha256']);self.assertEqual(hashlib.sha256(active).hexdigest(),row['adapted_sha256'])
   self.assertEqual((root/row['diff']).read_text(),''.join(difflib.unified_diff(original.decode().splitlines(True),active.decode().splitlines(True),fromfile=rel,tofile='skills/last30days/'+rel)))
 def test_domain_source_query_and_synthesis_methods_retained(self):
  for rel in ['references/research-runbook.md','references/synthesis.md','references/comparison.md','references/recommendations.md']:
   raw=(self.source/'skills/last30days'/rel).read_text();adapted=(self.leaf/rel).read_text()
   # Existing native host wording edits precede this patch; method retention is line based and substantial.
   lines=[l for l in raw.splitlines()if l.strip()];self.assertGreater(sum(l in adapted for l in lines)/len(lines),.85,rel)
  main=(self.leaf/'SKILL.md').read_text();self.assertNotIn('FIRST-RUN GATE',main);self.assertNotIn('grep -q "SETUP_COMPLETE',main);self.assertNotIn('Run the installed Python engine for research',main)
  self.assertIn('native_research.py',main);self.assertIn('never fall back to the direct engine',main);self.assertIn('###', (self.leaf/'references/research-runbook.md').read_text())
 def test_clean_environment_rejects_host_credentials_configs_tools_and_account_lanes(self):
  root=P(self.temp.name).resolve();env=self.adapter.clean_environment(root/'fresh-home',root/'work')
  self.assertEqual(env['LAST30DAYS_CONFIG_DIR'],'');self.assertEqual(env['LAST30DAYS_SKIP_KEYCHAIN'],'1');self.assertEqual(env['LAST30DAYS_TRUST_PROJECT_CONFIG'],'0')
  self.assertEqual(env['PATH'],str(root/'work/bin'));self.assertEqual(env['FROM_BROWSER'],'off');self.assertEqual(env['LAST30DAYS_DISCOVERY_QUEUE'],'off')
  self.assertNotIn('OPENAI_API_KEY',env);self.assertNotIn('LAST30DAYS_KEYCHAIN_ALIASES',env);self.assertNotIn('PASSWORD_STORE_DIR',env)
  self.assertEqual(set(self.adapter.ALLOWED),{'reddit','hackernews','polymarket'})
  with self.assertRaises(ValueError):self.adapter.query_plan('topic',['hackernews'],json.dumps({'subqueries':[{'sources':['x'],'search_query':'q','ranking_query':'q'}]}))
 def test_actual_upstream_mock_engine_cannot_touch_fake_credential_helpers_or_network(self):
  if sys.version_info<(3,12):self.skipTest('Actual pinned engine requires existing Python3.12+')
  if sys.platform!='darwin' or not P('/usr/bin/sandbox-exec').is_file():self.skipTest('Offline target fixture requires macOS OS network denial')
  root=P(self.temp.name).resolve()/'canary-fixture';root.mkdir();home=root/'host-home';(home/'.config/last30days').mkdir(parents=True);(home/'.config/last30days/.env').write_text('OPENAI_API_KEY=SYNTHETIC-NEVER-READ\n');bin=root/'host-bin';bin.mkdir();canary=root/'credential-helper-called'
  for name in ['security','pass','grok','gh','brightdata']:
   p=bin/name;p.write_text('#!/bin/sh\necho called >> '+str(canary)+'\nexit 99\n');p.chmod(0o755)
  env={'HOME':str(home),'PATH':str(bin),'OPENAI_API_KEY':'SYNTHETIC-NEVER-INHERIT','XAI_API_KEY':'SYNTHETIC-NEVER-INHERIT','LAST30DAYS_KEYCHAIN_ALIASES':'SYNTHETIC-NEVER-INHERIT','PASSWORD_STORE_DIR':str(root/'synthetic-password-store'),'LANG':'en_US.UTF-8'}
  out=root/'result';r=subprocess.run(['/usr/bin/sandbox-exec','-p','(version 1) (allow default) (deny network*)',sys.executable,'-I','-B',str(self.wrapper),'public fixture','--source','hackernews','--mock','--outdir',str(out)],env=env,cwd=root,capture_output=True,text=True,timeout=45)
  self.assertEqual(r.returncode,0,r.stdout+r.stderr);receipt=json.loads((out/'run.json').read_text());self.assertEqual(receipt['status'],'synthetic_fixture_only');self.assertTrue(receipt['mock']);self.assertFalse(canary.exists());self.assertTrue((out/'stdout.json').stat().st_size>10)
  self.assertNotIn('SYNTHETIC-NEVER', (out/'stdout.json').read_text()+(out/'stderr.log').read_text())
 def test_actual_config_loader_negative_control_detects_synthetic_stores(self):
  root=P(self.temp.name).resolve()/'config-control';root.mkdir();host=root/'host';(host/'.config/last30days').mkdir(parents=True);(host/'.config/last30days/.env').write_text('OPENAI_API_KEY=SYNTHETIC-CONFIG-ONLY\n')
  bin=root/'fake-bin';bin.mkdir();canary=root/'fake-pass-called'
  for name in ['security','pass']:
   p=bin/name;p.write_text('#!/bin/sh\necho called >> '+str(canary)+'\nexit 1\n');p.chmod(0o755)
  code='import sys;sys.path.insert(0,'+repr(str(self.leaf/'scripts'))+');from lib import env;c=env.get_config();'
  negative={'HOME':str(host),'PATH':str(bin),'LAST30DAYS_SKIP_KEYCHAIN':'1','LANG':'en_US.UTF-8'}
  r=subprocess.run([sys.executable,'-I','-B','-c',code+'assert c["OPENAI_API_KEY"]=="SYNTHETIC-CONFIG-ONLY"'],env=negative,cwd=root,capture_output=True,text=True)
  self.assertEqual(r.returncode,0,r.stderr);self.assertTrue(canary.exists());calls=canary.read_bytes()
  work=root/'clean';work.mkdir();(work/'home').mkdir();(work/'bin').mkdir();(work/'tmp').mkdir()
  clean=self.adapter.clean_environment(work/'home',work)
  r=subprocess.run([sys.executable,'-I','-B','-c',code+'assert not c.get("OPENAI_API_KEY");assert not c.get("AUTH_TOKEN");assert not c.get("GITHUB_TOKEN");assert c.get("FROM_BROWSER")=="off";from lib import providers,pipeline;runtime,client=providers.resolve_runtime(c,"quick");assert runtime.reasoning_provider=="local" and client is None;assert {"reddit","hackernews","polymarket"}<=set(pipeline.available_sources(c,local_only=True))'],env=clean,cwd=work,capture_output=True,text=True)
  self.assertEqual(r.returncode,0,r.stderr);self.assertEqual(canary.read_bytes(),calls)
 def test_wrapper_has_no_engine_flag_passthrough_and_checks_source_drift(self):
  out=P(self.temp.name).resolve()/'forbidden-result';r=subprocess.run([sys.executable,'-I','-B',str(self.wrapper),'topic','--outdir',str(out),'--setup'],capture_output=True,text=True);self.assertEqual(r.returncode,2);self.assertFalse(out.exists())
  temp=P(self.temp.name).resolve()/'tampered';shutil.copytree(self.leaf/'scripts',temp);(temp/'last30days.py').write_text('raise SystemExit("must not run")\n')
  r=subprocess.run([sys.executable,'-I','-B',str(temp/'native_research.py'),'topic','--outdir',str(out)],capture_output=True,text=True);self.assertEqual(r.returncode,2);self.assertIn('Reviewed engine/source changed',r.stderr);self.assertFalse(out.exists())
if __name__=='__main__':unittest.main()
