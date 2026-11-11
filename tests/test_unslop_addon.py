import pathlib,hashlib,json,tempfile,sys,unittest,difflib
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'lib')]
import native_setup as native
import unslop_addon as a
class UnslopAddon(unittest.TestCase):
 def test_active_entry_preserves_pinned_method_except_explicit_tool_binding(self):
  addon=ROOT/'addons/unslop';active=(addon/'SKILL.md').read_text()
  start=active.index('## Host tool binding\n');end=active.index('Vibecoded UI fails',start)
  original=active[:start]+active[end:]
  self.assertEqual(hashlib.sha256(original.encode()).hexdigest(),'19afd7f1841316ddff3f854ea8ead675c738e08b30c41e51a8f1822fa0111947')
  expected=''.join(difflib.unified_diff(original.splitlines(keepends=True),active.splitlines(keepends=True),fromfile='upstream/skills/unslop/SKILL.md',tofile='active/skills/unslop/SKILL.md'))
  self.assertEqual((addon/'PORT.patch').read_text(),expected)
  self.assertIn('reference-only',active[start:end]);self.assertIn('capability gap',active[start:end])
  self.assertIn('at most three times',original);self.assertIn('wait for their answer before editing',original)
 def fixture(self,root):
  for name,raw in {'LICENSE':'CC-BY-4.0 fixture','skills/unslop/SKILL.md':'---\nname: unslop\ndescription: upstream\n---\nOriginal method','skills/unslop/references/tokens.md':'original tokens','skills/unslop/references/refs/example.webp':'original visual','skills/unslop/scripts/story.mjs':'original helper'}.items():
   p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(raw)
  files={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()};return hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest()
 def test_complete_support_original_attribution_and_frozen_bytes(self):
  with tempfile.TemporaryDirectory() as t:
   root=pathlib.Path(t);digest=self.fixture(root)
   with patch.object(a,'SOURCE_TREE_SHA256',digest),patch.object(native.nstack,'acquire',return_value=root):
    spec=native.addon_definition('unslop');original=(root/'skills/unslop/references/tokens.md').read_bytes();(root/'skills/unslop/references/tokens.md').write_text('changed cache after verification');files=native.addon_files(spec)
    self.assertEqual(files['skills/unslop/references/tokens.md'][0],original)
    self.assertEqual(files['skills/unslop/UPSTREAM_SKILL.md'][0],(root/'skills/unslop/SKILL.md').read_bytes())
    self.assertEqual(files['skills/unslop/SKILL.md'][0],(ROOT/'addons/unslop/SKILL.md').read_bytes())
    self.assertEqual(files['skills/unslop/PORT.patch'][0],(ROOT/'addons/unslop/PORT.patch').read_bytes())
    self.assertIn('skills/unslop/references/refs/example.webp',files);self.assertIn('LICENSE',files)
    self.assertEqual(spec['provenance']['license'],'CC-BY-4.0');self.assertEqual(spec['entry'],pathlib.Path('skills/unslop'))
 def test_cache_receipt_cannot_authorize_modified_source(self):
  with tempfile.TemporaryDirectory() as t:
   root=pathlib.Path(t);digest=self.fixture(root);(root/'skills/unslop/references/tokens.md').write_text('tampered');(root/'.nstack-source.json').write_text('{"claimed":"valid"}')
   with patch.object(a,'SOURCE_TREE_SHA256',digest),patch.object(native.nstack,'acquire',return_value=root):
    with self.assertRaisesRegex(ValueError,'reviewed pinned tree'):a.definition(native.nstack)
if __name__=='__main__':unittest.main()
