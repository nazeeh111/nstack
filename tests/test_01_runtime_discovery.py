"""New runtime capabilities appear through metadata without editing01."""
import importlib.util,json,pathlib,tempfile,unittest
P=pathlib.Path;ROOT=P(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('routing',ROOT/'addons/01/scripts/capabilities.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class RuntimeDiscovery(unittest.TestCase):
 def test_new_runtime_description_and_activation_refresh_without_category_table(self):
  with tempfile.TemporaryDirectory()as temporary:
   state=P(temporary);(state/'native-tools').mkdir();index=state/'native-tools/index.json'
   index.write_text(json.dumps([{'name':'New project capability','description':'Stateful graph checkpoints and durable workflow control','activation':'On demand for interrupt and resume','recipe':'/example/recipe.py','instructions':'/example/README.md','environment':{'API_KEY':'synthetic-not-a-credential'}}]))
   first=mod.search(state,['checkpoints']);self.assertEqual(len(first['matches']),1);row=first['matches'][0];self.assertEqual(row['kind'],'runtime');self.assertEqual(row['recipe'],'/example/recipe.py');self.assertEqual(row['instructions'],'/example/README.md');self.assertNotIn('environment',row);self.assertNotIn('synthetic-not-a-credential',json.dumps(first))
   self.assertEqual(mod.search(state,['interrupt'])['total_matches'],1)
   index.write_text(json.dumps([{'name':'New project capability','description':'Different capability after source update'}]))
   self.assertEqual(mod.search(state,['checkpoints'])['total_matches'],0)
   updated=mod.search(state,['Different']);self.assertEqual(updated['total_matches'],1);self.assertNotEqual(first['sources'][0]['sha256'],updated['sources'][0]['sha256'])
 def test_runtime_invocation_and_guide_allowlist_preserves_inert_types(self):
  with tempfile.TemporaryDirectory() as temporary:
   state=P(temporary);(state/'native-tools').mkdir()
   rows=[{'name':'string-command','description':'beacon conversion','command':'/example/bin/converter','guide':'/example/guide.md','documentation':'/example/docs.md','environment':{'API_KEY':'synthetic-not-a-credential'}},
         {'name':'array-command','description':'beacon rendering','command':['python3','/example/render.py','--offline'],'invoke':['nstack','run','fixture','--']},
         {'name':'bad-command','description':'beacon unsupported','command':{'secret':'must-not-emit'},'invoke':['python3',{'secret':'must-not-emit'}]}]
   (state/'native-tools/index.json').write_text(json.dumps(rows))
   result=mod.search(state,['beacon']);found={row['name']:row for row in result['matches']}
   self.assertEqual(found['string-command']['command'],rows[0]['command'])
   self.assertEqual(found['string-command']['guide'],rows[0]['guide'])
   self.assertEqual(found['string-command']['documentation'],rows[0]['documentation'])
   self.assertEqual(found['array-command']['command'],rows[1]['command'])
   self.assertEqual(found['array-command']['invoke'],rows[1]['invoke'])
   self.assertNotIn('command',found['bad-command']);self.assertNotIn('invoke',found['bad-command'])
   self.assertNotIn('environment',json.dumps(result));self.assertNotIn('synthetic-not-a-credential',json.dumps(result));self.assertNotIn('must-not-emit',json.dumps(result))
if __name__=='__main__':unittest.main()
