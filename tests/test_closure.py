import pathlib,tempfile,sys,unittest
P=pathlib.Path;sys.path.insert(0,str(P(__file__).resolve().parents[1]/'lib'));import closure
class Closure(unittest.TestCase):
 def test_mirrored_sibling_support_is_outside_exposed_leaf(self):
  with tempfile.TemporaryDirectory() as t:
   root=P(t).resolve();src=root/'source';out=root/'release';leaf=out/'skills/chosen';leaf.mkdir(parents=True);(leaf/'SKILL.md').write_text('[support](../other/SKILL.md)');sibling=src/'skills/other';sibling.mkdir(parents=True);(sibling/'SKILL.md').write_text('[details](details.md)');(sibling/'details.md').write_text('Pinned support');(src/'LICENSE').write_text('Grant')
   closure.support(src,out);closure.validate(out);self.assertTrue((out/'skills/other/details.md').exists());self.assertFalse((leaf/'other').exists());self.assertTrue((out/'LICENSE').exists())
   (leaf/'SKILL.md').write_text('[escape](../../../outside)')
   with self.assertRaisesRegex(ValueError,'escapes'):closure.support(src,out)
 def test_eligible_sibling_uses_patched_callback(self):
  with tempfile.TemporaryDirectory() as t:
   root=P(t).resolve();src=root/'source';out=root/'release';leaf=out/'skills/chosen';leaf.mkdir(parents=True);(leaf/'SKILL.md').write_text('[support](../other/SKILL.md)');sibling=src/'skills/other';sibling.mkdir(parents=True);(sibling/'SKILL.md').write_text('upstream')
   def port(rel,target):self.assertEqual(rel,'skills/other/SKILL.md');target.mkdir(parents=True);(target/'SKILL.md').write_text('reviewed patch');return True
   closure.support(src,out,port);self.assertEqual((out/'skills/other/SKILL.md').read_text(),'reviewed patch')
