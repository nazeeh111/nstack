import importlib.util,pathlib,tempfile,unittest,os
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('maps',ROOT/'recipes/maps_scraper.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Maps(unittest.TestCase):
 def test_existing_output_and_multiline_query_preserve_bytes(self):
  with tempfile.TemporaryDirectory() as t:
   p=pathlib.Path(t);(p/'original').write_text('keep')
   with self.assertRaisesRegex(ValueError,'already exists'):m.run_query(p/'binary','public query',p,geo='0,0')
   with self.assertRaisesRegex(ValueError,'one nonempty'):m.run_query(p/'binary','one\ntwo',p/'new',geo='0,0')
   self.assertEqual((p/'original').read_text(),'keep');self.assertFalse((p/'new').exists())
 def test_failure_keeps_partial_results_and_drops_sensitive_environment(self):
  with tempfile.TemporaryDirectory() as t:
   root=pathlib.Path(t);binary=root/'binary';binary.write_bytes(b'test only');out=root/'output'
   def fail(cmd,**kw):
    self.assertEqual(kw['env']['DISABLE_TELEMETRY'],'1');self.assertNotIn('MY_AWS_ACCESS_KEY',kw['env']);self.assertNotIn('HTTP_PROXY',kw['env']);(out/'results.jsonl').write_text('{"title":"Partial public place"}\n{truncated');return type('Result',(),{'returncode':1})()
   with patch.dict(os.environ,{'MY_AWS_ACCESS_KEY':'synthetic-never-forward','HTTP_PROXY':'synthetic-never-forward'}),patch.object(m.subprocess,'run',side_effect=fail):r=m.run_query(binary,'public place',out,geo='0,0')
   self.assertEqual(r['status'],'incomplete');self.assertEqual(r['rows'],1);self.assertEqual(r['invalid_records'],1);self.assertTrue((out/'run.json').exists());self.assertIn('Partial public place',(out/'results.jsonl').read_text())
if __name__=='__main__':unittest.main()
