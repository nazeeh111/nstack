import sys,pathlib,unittest,tomllib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'lib'));import config_merge as c
class ConfigTests(unittest.TestCase):
 def test_owned_merge_and_rollback_preserve_later_unrelated_edit(self):
  original='# note\nmodel="chosen"\nnotify = [\n "old-tool"\n]\n[agents]\nmax_concurrent_threads_per_session=4\n[mcp_servers.legacy]\ncommand="old"\n[mcp_servers.legacy.env]\nPLACEHOLDER="synthetic"\n[other]\nvalue=1\n'
  updates=[(['notify'],c.MISSING),(['agents','enabled'],True),(['plugins','old@market','enabled'],False)];retire=[['mcp_servers','legacy']]
  after=c.apply(original,updates,retire);data=tomllib.loads(after);self.assertEqual(data['model'],'chosen');self.assertEqual(data['agents']['max_concurrent_threads_per_session'],4);self.assertNotIn('notify',data)
  later=after.replace('value=1','value=2');restored=c.inverse(later,original,after,updates,retire);self.assertEqual(tomllib.loads(restored)['other']['value'],2);self.assertEqual(tomllib.loads(restored)['notify'],['old-tool']);self.assertEqual(tomllib.loads(restored)['mcp_servers']['legacy']['command'],'old')
 def test_same_key_conflict_stops(self):
  before='x=1\n';updates=[(['x'],2)];after=c.apply(before,updates,[])
  with self.assertRaisesRegex(ValueError,'Rollback conflict'):c.inverse('x=3\n',before,after,updates,[])
if __name__=='__main__':unittest.main()

class AdversarialTomlTests(unittest.TestCase):
 def test_array_table_after_retired_registration_survives(self):
  before='[mcp_servers.legacy]\ncommand="old"\n[[skills.config]]\npath="keep"\nenabled=false\n'
  after=c.apply(before,[],[['mcp_servers','legacy']]);self.assertEqual(tomllib.loads(after)['skills']['config'],[{'path':'keep','enabled':False}])
 def test_key_example_in_multiline_string_is_data(self):
  before="note='''\nnotify=[\"example\"]\n'''\nnotify=[\"actual\"]\n"
  after=c.apply(before,[(['notify'],c.MISSING)],[]);self.assertEqual(tomllib.loads(after)['note'],tomllib.loads(before)['note']);self.assertNotIn('notify',tomllib.loads(after))

class SemanticTypeTests(unittest.TestCase):
 def test_boolean_integer_types_are_distinct(self):
  after=c.apply('flag=1\n',[(['flag'],True)],[]);self.assertIs(tomllib.loads(after)['flag'],True)
  with self.assertRaisesRegex(ValueError,'conflict'):c.inverse('flag=1\n','flag=false\n','flag=true\n',[(['flag'],True)],[])
