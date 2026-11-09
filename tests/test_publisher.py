import importlib.util,json,pathlib,tempfile,unittest,os,sys
P=pathlib.Path
spec=importlib.util.spec_from_file_location('nstack',P(__file__).resolve().parents[1]/'nstack.py');n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
class PublisherTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.root=P(self.t.name).resolve();self.project=self.root/'project';self.project.mkdir();self.old_state=n.STATE;n.STATE=self.root/'state';self.release=n.STATE/'build/skills/P011/fixture';self.release.mkdir(parents=True)
  (self.release/'SKILL.md').write_text('---\nname: fixture\ndescription: Synthetic publisher acceptance fixture\n---\n')
  files=n.tree(self.release);n.dump(self.release/'.nstack-release.json',{'builder_sha256':n.builder_identity(),'candidate_id':'P011','name':'p011-obsidian-markdown','source_repository':'kepano/obsidian-skills','revision':'3ccff5338ea700537839b21900aa5358a0402c98','source_path':'skills/obsidian-markdown/SKILL.md','delivery':'intact upstream leaf','deployment':'on demand','files':files,'content_sha256':n.sha(json.dumps(files,sort_keys=True).encode()),'manifest_sha256':n.sha((n.ROOT/'registry/manifest.json').read_bytes())})
  n.dump(n.STATE/'publisher-index'/self.release.name,{'receipt_sha256':n.sha((self.release/'.nstack-release.json').read_bytes()),'release':str(self.release)})
 def tearDown(self):n.STATE=self.old_state;self.t.cleanup()
 def test_publish_repeat_deactivate_and_unrelated(self):
  dest=n.publish(self.project,self.release);record=n.journal_paths(self.project)[0]/'activations.json';before=record.read_bytes();self.assertEqual(n.publish(self.project,self.release),dest);self.assertEqual(before,record.read_bytes());self.assertEqual(n.verify(self.project)['active'],['p011-obsidian-markdown']);other=self.root/'other';other.mkdir();self.assertEqual(n.verify(other)['active'],[]);n.deactivate(self.project,'p011-obsidian-markdown');self.assertFalse(P(dest).exists());self.assertTrue((self.release/'SKILL.md').exists())
 def test_tamper_rejected(self):
  (self.release/'SKILL.md').write_text('tampered')
  with self.assertRaisesRegex(ValueError,'tampered'):n.publish(self.project,self.release)
 def test_no_clobber(self):
  shelf=self.project/'.agents/skills';shelf.mkdir(parents=True);(shelf/'p011-obsidian-markdown').write_text('unrelated bytes')
  with self.assertRaisesRegex(ValueError,'already exists'):n.publish(self.project,self.release)
  self.assertEqual((shelf/'p011-obsidian-markdown').read_text(),'unrelated bytes')
 def test_changed_owned_link_not_removed(self):
  dest=P(n.publish(self.project,self.release));dest.unlink();elsewhere=self.root/'elsewhere';elsewhere.mkdir();dest.symlink_to(elsewhere)
  with self.assertRaisesRegex(ValueError,'changed or unowned'):n.deactivate(self.project,'p011-obsidian-markdown')
  self.assertTrue(dest.is_symlink())
 def test_forged_receipt_rejected(self):
  r=n.load(self.release/'.nstack-release.json');r['revision']='0'*40;n.dump(self.release/'.nstack-release.json',r)
  with self.assertRaisesRegex(ValueError,'differs from registry'):n.publish(self.project,self.release)
 def test_missing_publisher_seal_rejected(self):
  (n.STATE/'publisher-index'/self.release.name).unlink()
  with self.assertRaisesRegex(ValueError,'lacks publisher'):n.publish(self.project,self.release)
 def test_interrupted_link_is_reconciled(self):
  n.publish(self.project,self.release);rows=n.activation_rows(self.project);rows['p011-obsidian-markdown']['phase']='prepared';n.save_activations(self.project,rows)
  with self.assertRaisesRegex(ValueError,'Unreconciled'):n.verify(self.project)
  n.publish(self.project,self.release);self.assertTrue(n.verify(self.project)['verified'])
 def test_worker_forged_journal_cannot_remove_unowned_link(self):
  shelf=self.project/'.agents/skills';shelf.mkdir(parents=True);dest=shelf/'victim';dest.symlink_to(self.release)
  n.dump(self.project/'.nstack/activations.json',{'victim':{'release':str(self.release),'target':str(self.release),'phase':'active'}})
  with self.assertRaisesRegex(ValueError,'No nstack ownership'):n.deactivate(self.project,'victim')
  self.assertTrue(dest.is_symlink())
 def test_linked_journal_rejected(self):
  elsewhere=self.root/'elsewhere';elsewhere.mkdir();(self.project/'.nstack').symlink_to(elsewhere)
  with self.assertRaisesRegex(ValueError,'Linked project'):n.publish(self.project,self.release)
 def test_traversal_deactivation_rejected(self):
  with self.assertRaisesRegex(ValueError,'Invalid shelf name'):n.deactivate(self.project,'../../victim')
if __name__=='__main__':unittest.main()
