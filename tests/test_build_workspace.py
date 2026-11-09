import importlib.util,json,pathlib,sys,tempfile,unittest
from unittest.mock import patch
P=pathlib.Path;ROOT=P(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'lib'));import build_workspace
spec=importlib.util.spec_from_file_location('workspace_nstack',ROOT/'nstack.py');n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
class Workspaces(unittest.TestCase):
 def fixture(self,root):
  n.STATE=root/'state';project=root/'project';project.mkdir();st=project.stat();scope=n.sha(json.dumps([str(project),st.st_dev,st.st_ino]).encode());prefix=n.STATE/'workspaces'/scope/'P198/123';source=prefix/'build-source';(source/'.git').mkdir(parents=True);(source/'.git/HEAD').write_text('pinned fixture');(source/'module.py').write_text('value=1');(prefix/'nstack-retirement.json').write_text('precious note');c=n.component('P198');saved={'id':'P198','project':str(project),'prefix':str(prefix),'source':str(source),'source_repository':c['repository'],'revision':c['revision'],'phase':'active','pristine_files':build_workspace.source_snapshot(n,source)};record=n.STATE/'workspace-owners'/scope/'P198/current.json';n.dump(record,saved);return project,prefix,source,record
 def test_actual_snapshot_rejects_hidden_edits_without_running_git(self):
  previous=n.STATE
  try:
   with tempfile.TemporaryDirectory() as t:
    project,prefix,source,record=self.fixture(P(t).resolve());before=build_workspace.prepare(n,'P198',project)
    self.assertEqual(before,build_workspace.prepare(n,'P198',project));(source/'module.py').write_text('value=2')
    with patch.object(build_workspace.subprocess,'check_output',side_effect=AssertionError('Git must not adjudicate the mutable index')):
     with self.assertRaisesRegex(ValueError,'edited/generated'):build_workspace.prepare(n,'P198',project)
    self.assertTrue(prefix.exists());self.assertEqual(n.load(record)['phase'],'active')
  finally:n.STATE=previous
 def test_linked_source_and_git_metadata_are_refused(self):
  previous=n.STATE
  try:
   with tempfile.TemporaryDirectory() as t:
    project,prefix,source,record=self.fixture(P(t).resolve());kept=prefix/'kept';source.rename(kept);source.symlink_to(kept,target_is_directory=True)
    with self.assertRaisesRegex(ValueError,'Linked'):build_workspace.prepare(n,'P198',project)
    source.unlink();kept.rename(source);git=source/'.git';git.rename(source/'git-original');git.symlink_to(source/'git-original',target_is_directory=True)
    with self.assertRaisesRegex(ValueError,'metadata escaped'):build_workspace.prepare(n,'P198',project)
  finally:n.STATE=previous
 def test_removed_component_can_retire_and_preserve_unexpected_note(self):
  previous=n.STATE
  try:
   with tempfile.TemporaryDirectory() as t:
    project,prefix,source,record=self.fixture(P(t).resolve())
    with patch.object(n,'component',side_effect=ValueError('No longer admitted')):result=build_workspace.prepare(n,'P198',project,retire=True)
    retained=P(result['retained']);self.assertFalse(prefix.exists());self.assertEqual((retained/'nstack-retirement.json').read_text(),'precious note');self.assertEqual(n.load(record)['phase'],'retired')
  finally:n.STATE=previous
if __name__=='__main__':unittest.main()
