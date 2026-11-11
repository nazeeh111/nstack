import hashlib,json,pathlib,sys,tempfile,unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'lib')]
import academic_addon as a
import native_setup as native
class AcademicAddon(unittest.TestCase):
 def fixture(self,base):
  for name in a.DESCRIPTIONS:
   d=base/name;d.mkdir();(d/'SKILL.md').write_text('---\nname: '+name+'\ndescription: upstream broad trigger\n---\n# Skill\n'+('Roles 3-5 and the QC rechecks use Claude.\n---\n' if name=='sr-screener' else '')+'<!-- routing-core:begin -->\nOriginal cross-phase routing and screening boundary.\n<!-- routing-core:end -->\nUse DOI or WebSearch in a fresh Claude Code session.\n')
  (base/'shared').mkdir();(base/'shared/required.md').write_text('required shared reference');(base/'LICENSE').write_text('CC-BY-NC-4.0 fixture');(base/'.nstack-source.json').write_text('{}')
  files={str(p.relative_to(base)):hashlib.sha256(p.read_bytes()).hexdigest() for p in base.rglob('*') if p.is_file() and p.name!='.nstack-source.json'}
  return hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()
 def test_all_five_are_native_and_preserve_full_source_and_original_entry(self):
  with tempfile.TemporaryDirectory() as temp:
   source=pathlib.Path(temp);digest=self.fixture(source)
   with patch.object(a,'SOURCE_TREE_SHA256',digest),patch.object(native.nstack,'acquire',return_value=source):
    for name in a.DESCRIPTIONS:
     spec=a.definition(native.nstack,name);files=native.addon_files(spec);entry=files[name+'/SKILL.md'][0].decode()
     self.assertIn('fresh native host session',entry);self.assertNotIn('fresh Codex session',entry);self.assertIn('Original cross-phase routing and screening boundary.',entry);self.assertIn('scripts/cross_model_codex_transport.py',files['NATIVE-BINDINGS.md'][0].decode());self.assertIn(name+'/NATIVE-PORT.patch',files)
     original=(source/name/'SKILL.md').read_text();expected=original.replace('Claude Code session','native host session');prefix,body=entry.split('> Native host execution: read [bindings](../NATIVE-BINDINGS.md).\n\n',1);self.assertEqual(body,expected[4:].split('\n---\n',1)[1]);self.assertEqual(prefix,original[:original.index('\n---\n',4)+5]+'\n')
     self.assertEqual(files[name+'/UPSTREAM_SKILL.md'][0],(source/name/'SKILL.md').read_bytes());self.assertIn('shared/required.md',files);self.assertIn('UPSTREAM-SOURCE.json',files);self.assertNotIn('.nstack-source.json',files)
 def test_rewritten_source_receipt_does_not_authenticate_changed_pinned_content(self):
  with tempfile.TemporaryDirectory() as temp:
   source=pathlib.Path(temp);digest=self.fixture(source);(source/'shared/required.md').write_text('altered');(source/'.nstack-source.json').write_text('{"claimed":"valid"}')
   with patch.object(a,'SOURCE_TREE_SHA256',digest),patch.object(native.nstack,'acquire',return_value=source):
    with self.assertRaisesRegex(ValueError,'reviewed pinned tree'):a.definition(native.nstack,'academic-paper')
 def test_cache_edit_after_verification_cannot_change_consumed_bytes(self):
  with tempfile.TemporaryDirectory() as temp:
   source=pathlib.Path(temp);digest=self.fixture(source);original=(source/'shared/required.md').read_bytes()
   with patch.object(a,'SOURCE_TREE_SHA256',digest),patch.object(native.nstack,'acquire',return_value=source):
    spec=a.definition(native.nstack,'academic-paper');(source/'shared/required.md').write_text('changed after verification')
    self.assertEqual(native.addon_files(spec)['shared/required.md'][0],original)
if __name__=='__main__':unittest.main()
