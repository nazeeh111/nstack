import importlib.util,json,os,pathlib,sys,tempfile,unittest
from unittest.mock import patch
P=pathlib.Path
ROOT=P(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'lib'))
spec=importlib.util.spec_from_file_location('nstack_project_test',ROOT/'nstack.py');n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
import project_setup,project_publisher

class ProjectTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=P(self.tmp.name).resolve();self.project=self.root/'project';self.project.mkdir();self.home=self.root/'profile';self.home.mkdir();self.previous=n.STATE;n.STATE=self.root/'state';self.env=patch.dict(os.environ,{'CODEX_HOME':str(self.home)});self.env.start()
 def tearDown(self):self.env.stop();n.STATE=self.previous;self.tmp.cleanup()
 def test_owned_registration_repeat_and_inverse_preserves_later_config(self):
  config=self.project/'.codex/config.toml';config.parent.mkdir();config.write_text('project_doc_max_bytes=45000\n')
  project_setup.configure(n,self.project,trust=True);first=config.read_bytes();project_setup.configure(n,self.project,trust=True);self.assertEqual(first,config.read_bytes())
  config.write_text(config.read_text()+'\n[extra]\nkeep="later"\n')
  project_setup.configure(n,self.project,remove=True)
  self.assertEqual(project_setup.cm.tomllib.loads(config.read_text()),{'project_doc_max_bytes':45000,'extra':{'keep':'later'}})
  self.assertFalse((self.home/'config.toml').exists())
 def test_unowned_server_and_linked_user_config_fail_before_mutation(self):
  config=self.project/'.codex/config.toml';config.parent.mkdir();config.write_text('[mcp_servers.nstack_project]\ncommand="unrelated"\n');before=config.read_bytes()
  with self.assertRaisesRegex(ValueError,'not owned'):project_setup.configure(n,self.project)
  self.assertEqual(before,config.read_bytes());config.unlink();(self.home/'config.toml').symlink_to(self.root/'absent')
  with self.assertRaisesRegex(ValueError,'Linked user'):project_setup.configure(n,self.project,trust=True)
  self.assertFalse(config.exists())
 def test_bounded_rpc_rejects_foreign_paths_trials_and_replaced_root(self):
  publisher=project_publisher.Publisher(n,self.project)
  with self.assertRaisesRegex(ValueError,'bounded tool schema'):publisher.call('activate_leaf',{'candidate_id':'P011','source_path':'skills/obsidian-markdown/SKILL.md','project':'/'})
  with self.assertRaisesRegex(ValueError,'on-demand leaves only'):publisher.call('activate_leaf',{'candidate_id':'L036','source_path':'SKILL.md'})
  with self.assertRaisesRegex(ValueError,'Invalid shelf'):publisher.call('deactivate_leaf',{'name':'../../victim'})
  old=self.root/'old';self.project.rename(old);self.project.mkdir()
  with self.assertRaisesRegex(ValueError,'identity changed'):publisher.call('verify_shelf',{})
 def test_malformed_or_parent_linked_trust_config_does_not_change_project(self):
  user=self.home/'config.toml';user.write_text('not valid toml [')
  project=self.project/'.codex/config.toml'
  with self.assertRaises(Exception):project_setup.configure(n,self.project,trust=True)
  self.assertFalse(project.exists());self.assertEqual(user.read_text(),'not valid toml [')
  alias=self.root/'home-alias';alias.symlink_to(self.home)
  with patch.dict(os.environ,{'CODEX_HOME':str(alias)}):
   with self.assertRaisesRegex(ValueError,'Linked user config parent'):project_setup.configure(n,self.project,trust=True)
  self.assertFalse(project.exists())

if __name__=='__main__':unittest.main()
