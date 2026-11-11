"""Offline source-fidelity regressions for selected Postgres/research methods.

These check actual materialized operative instructions against the pinned source,
not a word-count proxy. They do not run SQL, models, providers or project writes.
"""
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'lib')]
from closure import validate
from skill_build import materialize
from patch_research import prompt

CACHE=pathlib.Path(os.environ.get('NSTACK_SOURCE_METHODS_CACHE',pathlib.Path.home()/'Library/Application Support/nstack/sources'))
SHA=lambda b:hashlib.sha256(b).hexdigest()


class SourceMethods(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.registry=json.loads((ROOT/'registry/manifest.json').read_text())
  cls.temp=tempfile.TemporaryDirectory(prefix='nstack-source-methods-')
  cls.addClassCleanup(cls.temp.cleanup)
  cls.base=pathlib.Path(cls.temp.name);cls.out={};cls.source={}
  for spec in cls.registry['skills']:
   name=pathlib.Path(spec['source_path']).parent.name
   if not (spec['candidate_id']=='P037' or (spec['candidate_id']=='P119' and name in ('experiment-audit','result-to-claim'))):continue
   source=CACHE/spec['source_repository'].replace('/','--')/spec['revision']
   if not (source/'.nstack-source.json').is_file():raise unittest.SkipTest('Exact offline source unavailable; no acquisition: '+spec['source_repository'])
   receipt=json.loads((source/'.nstack-source.json').read_text())
   if receipt['revision']!=spec['revision'] or receipt['repository']!=spec['source_repository']:raise AssertionError('Wrong source identity')
   needed=[spec['source_path']]
   if spec['candidate_id']=='P037':needed += [str(pathlib.Path(spec['source_path']).parent/'references'/x) for x in ('query-missing-indexes.md','security-rls-basics.md','monitor-explain-analyze.md')]
   for rel in needed:
    file=source/rel
    if file.is_symlink() or SHA(file.read_bytes())!=receipt['files'][rel]:raise AssertionError('Pinned method changed: '+rel)
   out=cls.base/name;out.mkdir()
   component=next(x for x in cls.registry['components'] if x['id']==spec['candidate_id'])
   materialize(source,out,spec,component,cls.registry)
   # Match the installed natural entry-name adaptation before checking seals.
   skill=out/'SKILL.md';skill.write_text(re.sub(r'(?m)^name:.*$','name: '+name,skill.read_text(),count=1))
   cls.out[name]=out;cls.source[name]=source/spec['source_path']

 def test_postgres_keeps_executable_index_and_plan_teaching_examples(self):
  root=self.out['supabase-postgres-best-practices']/'references'
  query=(root/'query-missing-indexes.md').read_text()
  for sql in ['create index orders_customer_id_idx on orders (customer_id);','select * from orders where customer_id = 123;','select c.name, o.total','join orders o on o.customer_id = c.id;']:
   self.assertIn(sql,query)
  self.assertNotIn('exponentially slower',query)
  self.assertNotIn('100-1000x',query)
  self.assertNotIn('always index',query)
  plan=(root/'monitor-explain-analyze.md').read_text()
  self.assertIn('explain (format text)',plan)
  self.assertIn('explain (analyze, buffers, format text)',plan)
  # Preserve actual plan interpretation, not just a generic instruction to measure.
  for example in ['actual time=0.015..450.123 rows=50 loops=1','Rows Removed by Filter: 999950','Buffers: shared hit=5000 read=15000','Sort Method: external merge','Nested Loop with high loops']:
   self.assertIn(example,plan)
  self.assertLess(plan.index('explain (format text)'),plan.index('explain (analyze, buffers, format text)'))
  self.assertIn('executes the query and its functions',plan)
  self.assertNotIn('needs more memory',plan)

 def test_row_security_keeps_sql_with_a_trusted_identity_boundary(self):
  text=(self.out['supabase-postgres-best-practices']/'references/security-rls-basics.md').read_text()
  for sql in ['alter table orders enable row level security;','create policy orders_user_policy on orders','to authenticated','using (user_id = auth.uid())','with check (user_id = auth.uid());','alter table orders force row level security;']:
   self.assertIn(sql,text)
  self.assertNotIn("set app.current_user_id = '123';",text)
  self.assertNotIn("using (user_id = current_setting('app.current_user_id')",text)
  for condition in ['issuer, audience, signature and expiry','BYPASSRLS','attempted user_id changes','own-row SELECT/INSERT/UPDATE/DELETE','negative test']:
   self.assertIn(condition,text)

 def test_every_original_audit_and_claim_review_question_remains_operative(self):
  for name in ('experiment-audit','result-to-claim'):
   source=self.source[name].read_text();active=(self.out[name]/'SKILL.md').read_text()
   questions=[line.strip() for line in prompt(source).splitlines() if re.match(r'^\s*\d+\.',line)]
   self.assertGreater(len(questions),6)
   for question in questions:self.assertIn(question,active,(name,question))
  audit=(self.out['experiment-audit']/'SKILL.md').read_text()
  for classification in ['real_gt','synthetic_proxy','self_supervised_proxy','simulation_only','human_eval']:
   self.assertIn(classification,audit)
  self.assertIn('DO NOT summarize, interpret, or explain any file content',audit)
  self.assertIn('exact file:line references',audit)

 def test_audit_report_preserves_the_complete_structured_source_schema(self):
  def schema_keys(value):
   if isinstance(value,dict):return {k:schema_keys(v) for k,v in value.items()}
   if isinstance(value,list):return [schema_keys(v) for v in value]
   return None
  source=self.source['experiment-audit'].read_text();active=(self.out['experiment-audit']/'SKILL.md').read_text()
  code=lambda text:json.loads(re.search(r'```json\n(.*?)\n```',text,re.S)[1])
  self.assertEqual(schema_keys(code(source)),schema_keys(code(active)))

 def test_claim_integrity_reconciliation_and_each_next_action_are_preserved(self):
  text=(self.out['result-to-claim']/'SKILL.md').read_text()
  for step in ['Step 3: Parse and Normalize','Step 3.5: Check Experiment Integrity','Step 4: Route Based on Verdict']:
   self.assertIn(step,text)
  self.assertIn('downgrade confidence to "low" regardless of the claim-support judgment',text)
  self.assertIn('if integrity_status == "warn"',text)
  self.assertIn('provisional — no integrity audit run',text)
  self.assertIn('If `confidence` is low, treat the judgment as inconclusive',text)
  for branch,content in [('#### `no`',['What was tested, what failed, hypotheses for why','Constraints for future attempts','pivot to next idea']),('#### `partial`',['reflect what IS supported','supplementary experiments','Re-run result-to-claim','Multiple rounds of `partial`','narrow the claim scope or switch ideas']),('#### `yes`',['Record confirmed claim','ablation studies are incomplete','ready for paper writing'])]:
   section=text[text.index(branch):].split('\n#### ',1)[0].split('\n### Step 5:',1)[0]
   for item in content:self.assertIn(item,section)
  self.assertIn('formal-proof status',text)
  self.assertIn('REVIEW_UNAVAILABLE',text)
  self.assertIn('no duplicate findings.md is required',text)

 def test_audit_and_claim_handoff_agree_and_checker_works_outside_its_folder(self):
  audit=(self.out['experiment-audit']/'SKILL.md').read_text()
  self.assertIn('preserve raw_claim_supported',audit)
  self.assertIn('confidence = "low"',audit)
  self.assertIn('effective_claim_status = "inconclusive"',audit)
  self.assertIn('A footnote alone does not resolve the concern',audit)
  self.assertNotIn('warn loudly, never halt the pipeline',audit)
  claim=(self.out['result-to-claim']/'SKILL.md').read_text()
  self.assertIn('"<skill-dir>/tools/evidence_check.py"',claim)
  self.assertNotIn('python3 tools/evidence_check.py',claim)
  unrelated=self.base/'unrelated-working-directory';unrelated.mkdir()
  checker=(self.out['result-to-claim']/'tools/evidence_check.py').resolve()
  result=subprocess.run([sys.executable,'-B',str(checker),'--help'],cwd=unrelated,capture_output=True,text=True,timeout=10)
  self.assertEqual(result.returncode,0,result.stderr)
  self.assertIn('--root',result.stdout)

 def test_archives_are_exact_and_provenance_binds_actual_operating_files(self):
  for name,out in self.out.items():
   validate(out)
   record=json.loads((out/'NATIVE-ADAPTATION.json').read_text())
   module='patch_lightweight.py' if name=='supabase-postgres-best-practices' else 'patch_research.py'
   self.assertEqual(record['port_sha256'],SHA((ROOT/'lib'/module).read_bytes()))
   if name=='supabase-postgres-best-practices':
    for rel,mod in record['modifications'].items():
     original=self.source[name].parent/rel
     self.assertEqual((out/mod['archival_original']).read_bytes(),original.read_bytes())
     self.assertEqual(mod['source_sha256'],SHA(original.read_bytes()))
     self.assertEqual(mod['adapted_sha256'],SHA((out/rel).read_bytes()))
   else:
    self.assertEqual((out/record['archival_original']).read_bytes(),self.source[name].read_bytes())
    self.assertEqual(record['source_sha256'],SHA(self.source[name].read_bytes()))
    self.assertEqual(record['adapted_sha256'],SHA((out/'SKILL.md').read_bytes()))
   self.assertEqual(len(list(out.rglob('SKILL.md'))),1)


if __name__=='__main__':unittest.main()
