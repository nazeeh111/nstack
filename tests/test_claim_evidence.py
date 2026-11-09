import pathlib,tempfile,unittest,sys,json
P=pathlib.Path;sys.path.insert(0,str(P(__file__).resolve().parents[1]/'lib'));import claim_evidence as e
class Evidence(unittest.TestCase):
 def test_structured_value_provenance_and_scope(self):
  with tempfile.TemporaryDirectory() as t:
   project=P(t);data=project/'data';data.mkdir();source=data/'producer.py';source.write_text('print(0.8)');artifact=data/'result.json';artifact.write_text('{"metrics":{"a/b":[0.8]}}')
   split=data/'split.json';split.write_text('{"train":["a"],"test":["b"]}');run=data/'run.json';run.write_text('{"command":["python","data/producer.py"],"status":"reported-complete"}');receipt={'split_path':'data/split.json','run_path':'data/run.json','unit':'seconds','metric':'rt60','split_sha256':e.digest(split),'run_sha256':e.digest(run),'command':['python','data/producer.py'],'artifact_sha256':e.digest(artifact),'sources':[{'path':'data/producer.py','sha256':e.digest(source)}]};f=data/'receipt.json';f.write_text(json.dumps(receipt));provenance={'path':'data/receipt.json','sha256':e.digest(f),**{k:receipt[k] for k in ('unit','metric','split_sha256','run_sha256','command')}}
   claim={'id':'clap','path':'data/result.json','format':'json','pointer':'/metrics/a~1b/0','value':0.8,'provenance':provenance};scope=e.Scope(project,['data']);self.assertEqual(scope.check(claim)['state'],'consistent-record')
   wrong={**claim,'provenance':{**provenance,'unit':'milliseconds'}};self.assertEqual(scope.check(wrong)['state'],'unknown');self.assertEqual(scope.check({**claim,'provenance':None})['state'],'unknown')
   source.write_text('print(1.1)');self.assertEqual(scope.check(claim)['state'],'unknown')
   (project/'private.txt').write_text('withheld');(data/'escape.json').symlink_to(project/'private.txt')
   self.assertIn('escapes',scope.check({**claim,'path':'data/escape.json'})['reason']);self.assertEqual(scope.check({**claim,'path':'data/*'})['state'],'unknown')
 def test_csv_key_and_lexical_presence_are_distinct(self):
  with tempfile.TemporaryDirectory() as t:
   p=P(t);f=p/'rows.csv';f.write_text('id,value\nx,0.8\nx,0.9\n');s=e.Scope(p,['.']);r=s.check({'id':'x','path':'rows.csv','format':'csv','column':'value','row_key':{'column':'id','value':'x'},'value':0.8});self.assertIn('ambiguous',r['reason']);self.assertEqual(s.check({'id':'x','path':'rows.csv','format':'text','value':'0.8'})['state'],'unknown')
 def test_pointer_and_boolean_semantics(self):
  self.assertEqual(e.pointer({'a~b':[2]},'/a~0b/0'),2);self.assertFalse(e.same_value(True,1))
  with self.assertRaises(e.Unknown):e.pointer([1],'/00')
  with self.assertRaises(e.Unknown):e.pointer({'x':2},'/x~2')
