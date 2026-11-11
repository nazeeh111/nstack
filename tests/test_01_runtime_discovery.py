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
if __name__=='__main__':unittest.main()
