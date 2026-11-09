"""Public registry coverage and permission boundary contract."""
import base64,collections,csv,hashlib,json,pathlib,unittest
P=pathlib.Path;ROOT=P(__file__).resolve().parents[1]
class RegistryContract(unittest.TestCase):
 def test_vendored_distribution_record_is_complete_and_unchanged(self):
  vendor=ROOT/'vendor'
  with (vendor/'tomlkit-0.13.3.dist-info/RECORD').open(newline='') as stream:
   for name,digest,size in csv.reader(stream):
    file=vendor/name;self.assertTrue(file.is_file(),name)
    if digest:
     algorithm,value=digest.split('=',1);self.assertEqual(algorithm,'sha256');self.assertEqual(base64.urlsafe_b64encode(hashlib.sha256(file.read_bytes()).digest()).rstrip(b'=').decode(),value);self.assertEqual(file.stat().st_size,int(size))
 def test_complete_decisions_and_routes_preserve_permissions(self):
  manifest=json.loads((ROOT/'registry/manifest.json').read_text());routes=json.loads((ROOT/'registry/routes.json').read_text());discovery=json.loads((ROOT/'registry/discovery.json').read_text());components={x['id']:x for x in manifest['components']}
  self.assertEqual(len(components),242);self.assertEqual(len(manifest['skills']),202);self.assertEqual(len(discovery),535);self.assertEqual(set(routes),set(components));self.assertEqual(collections.Counter(x['deployment'] for x in components.values()),{'on demand':198,'trial':28,'substitute':7,'consult':9})
  tuples=[tuple(x[k] for k in ('candidate_id','source_repository','revision','source_path')) for x in manifest['skills']];self.assertEqual(len(set(tuples)),202)
  for id,c in components.items():
   route=routes[id];self.assertEqual(route['deployment'],c['deployment']);self.assertEqual(route['source']['revision'],c['revision']);self.assertEqual(route['source']['repository'],c['repository'])
   if c['deployment']!='on demand':
    self.assertNotIn('runtime_operations',route);self.assertNotIn('native_commands',route);self.assertNotIn('prepare',route)
   elif route['kind']=='native commissioning recipe':
    self.assertTrue(route.get('native_commands') or route.get('native_ui_steps'));self.assertIn('deactivate',route);self.assertIn('lock_resolution',route)
  for recipe in (ROOT/'recipes').rglob('recipe.json'):
   data=json.loads(recipe.read_text());self.assertEqual(components[data['id']]['deployment'],'on demand');self.assertEqual(data.get('reviewed_source_revision',data.get('revision')),components[data['id']]['revision'])
if __name__=='__main__':unittest.main()
