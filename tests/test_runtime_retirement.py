import importlib.util,pathlib,tempfile,sys,json,unittest
from unittest.mock import patch
P=pathlib.Path;ROOT=P(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'lib'));import runtime
spec=importlib.util.spec_from_file_location('nstack',ROOT/'nstack.py');n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
class Retirement(unittest.TestCase):
 def test_interruption_after_rename_reconciles_without_losing_bytes(self):
  original=n.STATE
  try:
   with tempfile.TemporaryDirectory() as t:
    n.STATE=P(t).resolve();prefix=n.STATE/'runtimes/P318/rt60';prefix.mkdir(parents=True);(prefix/'requirements.lock').write_text('fixture lock');(prefix/'local-note.txt').write_text('preserve');(prefix/'nstack-retirement.json').write_text('precious note')
    r,folder=runtime.recipe(n,'P318','rt60');source=n.STATE/'sources'/r['source_repository'].replace('/','--')/r['revision'];module=source/r['source_path'];module.parent.mkdir(parents=True);module.write_text('trusted module');n.dump(source/'.nstack-source.json',{'files':{r['source_path']:n.sha(module.read_bytes())}})
    receipt={'id':'P318','operation':'rt60','revision':r['revision'],'module':str(module),'module_sha256':n.sha(module.read_bytes()),'requirements_sha256':n.sha((prefix/'requirements.lock').read_bytes()),'recipe_sha256':n.sha((folder/'recipe.json').read_bytes())};n.dump(n.STATE/'locks/P318-rt60.json',receipt)
    rename=runtime.os.rename
    class Interrupted(BaseException):pass
    def crash_after_move(a,b):rename(a,b);raise Interrupted()
    with patch.object(runtime.os,'rename',side_effect=crash_after_move):
     with self.assertRaises(Interrupted):runtime.remove(n,'P318','rt60')
    self.assertFalse(prefix.exists());self.assertTrue((n.STATE/'locks/P318-rt60.json').exists())
    result=runtime.remove(n,'P318','rt60');retained=P(result['retained']);self.assertEqual((retained/'local-note.txt').read_text(),'preserve');self.assertEqual((retained/'nstack-retirement.json').read_text(),'precious note');self.assertFalse((n.STATE/'locks/P318-rt60.json').exists());self.assertEqual(n.load(n.STATE/'runtime-retirements/P318-rt60.json')['phase'],'complete');self.assertEqual(runtime.remove(n,'P318','rt60')['state'],'absent')
  finally:n.STATE=original
 def test_exact_owned_runtime_retains_bytes_and_repeat(self):
  original=n.STATE
  with tempfile.TemporaryDirectory() as t:
   n.STATE=P(t).resolve();prefix=n.STATE/'runtimes/P318/rt60';prefix.mkdir(parents=True);lock=prefix/'requirements.lock';lock.write_text('fixture lock');personal=prefix/'local-note.txt';personal.write_text('Preserve this unexpected addition')
   r,folder=runtime.recipe(n,'P318','rt60');source=n.STATE/'sources'/r['source_repository'].replace('/','--')/r['revision'];module=source/r['source_path'];module.parent.mkdir(parents=True);module.write_text('trusted module');n.dump(source/'.nstack-source.json',{'files':{r['source_path']:n.sha(module.read_bytes())}});receipt={'id':'P318','operation':'rt60','revision':r['revision'],'module':str(module),'module_sha256':n.sha(module.read_bytes()),'requirements_sha256':n.sha(lock.read_bytes()),'recipe_sha256':n.sha((folder/'recipe.json').read_bytes())};n.dump(n.STATE/'locks/P318-rt60.json',receipt)
   module.write_text('tampered')
   with self.assertRaisesRegex(ValueError,'changed'):runtime.remove(n,'P318','rt60')
   self.assertTrue(prefix.exists());module.write_text('trusted module');result=runtime.remove(n,'P318','rt60');retired=P(result['retained']);self.assertFalse(prefix.exists());self.assertEqual((retired/'local-note.txt').read_text(),'Preserve this unexpected addition');self.assertEqual(n.load(n.STATE/'runtime-retirements/P318-rt60.json')['phase'],'complete');self.assertFalse((n.STATE/'locks/P318-rt60.json').exists());self.assertEqual(runtime.remove(n,'P318','rt60')['state'],'absent')
  n.STATE=original
 def test_unrecorded_runtime_is_not_retired(self):
  original=n.STATE
  try:
   with tempfile.TemporaryDirectory() as t:
    n.STATE=P(t).resolve();prefix=n.STATE/'runtimes/P318/rt60';prefix.mkdir(parents=True)
    with self.assertRaisesRegex(ValueError,'Unrecorded'):runtime.remove(n,'P318','rt60')
    self.assertTrue(prefix.is_dir())
  finally:n.STATE=original
