import pathlib,tempfile,sys,unittest,zipfile,json,hashlib
P=pathlib.Path;ROOT=P(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'lib'));import python_source,runtime
class Fake:
 @staticmethod
 def sha(raw):return hashlib.sha256(raw).hexdigest()
class PythonSource(unittest.TestCase):
 def test_current_admission_and_source_are_rechecked(self):
  class Registry:
   def component(self,id):return self.current
  n=Registry();r={'revision':'a'*40,'source_repository':'owner/source'}
  n.current={'deployment':'trial','revision':'a'*40,'repository':'owner/source'}
  with self.assertRaisesRegex(ValueError,'trial/substitute'):runtime.admitted(n,'fixture',r)
  n.current['deployment']='on demand';n.current['revision']='b'*40
  with self.assertRaisesRegex(ValueError,'source revision'):runtime.admitted(n,'fixture',r)
  n.current['revision']='a'*40;runtime.admitted(n,'fixture',r)
 def test_wheel_identity_rejects_foreign_distribution_and_escape(self):
  with tempfile.TemporaryDirectory() as t:
   w=P(t)/'fixture.whl'
   with zipfile.ZipFile(w,'w') as z:z.writestr('fixture-1.dist-info/METADATA','Name: fixture\nVersion: 1.0\n')
   self.assertEqual(python_source.wheel_identity(w,'Fixture')['version'],'1.0')
   with self.assertRaisesRegex(ValueError,'distribution differs'):python_source.wheel_identity(w,'other')
   with zipfile.ZipFile(w,'a') as z:z.writestr('../escape','x')
   with self.assertRaisesRegex(ValueError,'Unsafe wheel path'):python_source.wheel_identity(w,'fixture')
 def test_environment_inventory_detects_injected_cache_and_symlinks(self):
  with tempfile.TemporaryDirectory() as t:
   root=P(t);(root/'venv/lib').mkdir(parents=True);(root/'wheels').mkdir();(root/'requirements.lock').write_text('runtime');(root/'build-requirements.lock').write_text('build');file=root/'venv/lib/module.py';file.write_text('value=1');before=python_source.files(Fake,root)
   cache=root/'venv/lib/__pycache__';cache.mkdir();(cache/'module.cpython-312.pyc').write_bytes(b'hostile cache');self.assertNotEqual(python_source.files(Fake,root),before)
   (root/'venv/lib/sitecustomize.py').symlink_to(file);self.assertIn('venv/lib/sitecustomize.py',python_source.files(Fake,root))
   (root/'build-source').mkdir();(root/'build-source/unhashed.py').write_text('value=2');(root/'venv/lib/source-link.py').symlink_to(root/'build-source/unhashed.py')
   with self.assertRaisesRegex(ValueError,'outside hashed trees'):python_source.files(Fake,root)
   (root/'venv/lib/source-link.py').unlink()
   (root/'venv/lib/escape').symlink_to(root.parent)
   with self.assertRaisesRegex(ValueError,'external runtime symlink'):python_source.files(Fake,root)
if __name__=='__main__':unittest.main()
