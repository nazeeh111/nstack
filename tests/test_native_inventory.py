import json,pathlib,sys,unittest,subprocess
from unittest.mock import patch
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'lib'))
from native_inventory import plugin_metadata,installed_plugins,effective_metadata
class NativePlugins(unittest.TestCase):
 def test_missing_status_or_effective_payload_never_becomes_clean_empty_inventory(self):
  valid={'data':[{'skills':[],'errors':[]}]};self.assertEqual(effective_metadata(valid,{'config':{}})['loader_error_count'],0)
  for skills,config in [({'data':[{'skills':[]}]},{'config':{}}),(valid,{}),({'data':[{'skills':[{'name':'fixture','path':'/fixture','scope':{'private':'fixture'}}],'errors':[]}]},{'config':{}}),(valid,{'config':{'plugins':{'fixture':{'enabled':{'private':'fixture'}}}}})]:
   with self.assertRaises(ValueError):effective_metadata(skills,config)
 def fixture(self):return {'marketplaces':[{'name':'fixture','plugins':[{'id':'plugin@fixture','name':'plugin','installed':True,'enabled':False,'version':'1','source':{'type':'remote','account':'private-fixture'},'shareContext':{'creatorAccountUserId':'private-fixture'},'env':{'fixture':'private-fixture'}}]}],'marketplaceLoadErrors':[{'message':'private-fixture','marketplacePath':'private-fixture'}]}
 def test_only_safe_state_is_retained_and_partial_catalog_error_is_visible(self):
  result=plugin_metadata(self.fixture());self.assertNotIn('private-fixture',json.dumps(result));self.assertEqual(result['plugin_marketplace_error_count'],1);self.assertFalse(result['plugins'][0]['enabled']);self.assertTrue(result['plugins'][0]['installed'])
 def test_ambiguous_or_invalid_state_does_not_become_clean_inventory(self):
  data=self.fixture();data['marketplaces'][0]['plugins']*=2
  with self.assertRaisesRegex(ValueError,'duplicate'):plugin_metadata(data)
  data=self.fixture();data['marketplaces'][0]['plugins'][0]['enabled']='false'
  with self.assertRaisesRegex(ValueError,'identity/state'):plugin_metadata(data)
  data=self.fixture();data['marketplaces'][0]['plugins'][0]['version']={'private-fixture':'not a version'}
  with self.assertRaisesRegex(ValueError,'version/source'):plugin_metadata(data)
 def test_native_warning_cannot_be_reported_as_clean_remote_catalog(self):
  data={'installed':[{'pluginId':'fixture@market','name':'fixture','marketplaceName':'market','installed':True,'enabled':True,'source':{'source':'remote','account':'private-fixture'}}],'available':[]}
  completed=subprocess.CompletedProcess([],0,json.dumps(data),'private-fixture catalog failure')
  with patch('native_inventory.subprocess.run',return_value=completed):result=installed_plugins(pathlib.Path('.'),'codex')
  self.assertTrue(result['plugin_native_warning_present']);self.assertIsNone(result['plugin_marketplace_error_count']);self.assertNotIn('private-fixture',json.dumps(result))
  data['marketplaceLoadErrors']=[{'message':'private-fixture'}]
  with patch('native_inventory.subprocess.run',return_value=subprocess.CompletedProcess([],0,json.dumps(data),'')):
   with self.assertRaisesRegex(ValueError,'completeness/error'):installed_plugins(pathlib.Path('.'),'codex')
if __name__=='__main__':unittest.main()
