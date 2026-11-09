import json,pathlib,tempfile,sys,unittest
from unittest.mock import patch
P=pathlib.Path;ROOT=P(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'lib'));import bootstrap
class BootstrapTests(unittest.TestCase):
 def test_incomplete_cached_receipt_cannot_skip_binary_checks(self):
  with tempfile.TemporaryDirectory() as t:
   root=P(t);dest=root/'bin/0.167.0';dest.mkdir(parents=True);(dest/'LOCK.json').write_text(json.dumps({'files':[]}))
   with patch.object(bootstrap.platform,'system',return_value='Darwin'),patch.object(bootstrap.platform,'machine',return_value='arm64'):
    with self.assertRaisesRegex(ValueError,'required artifact set'):bootstrap.binary_pair(ROOT,root)
 def test_foreign_target_needs_own_artifacts(self):
  with patch.object(bootstrap.platform,'system',return_value='Linux'),patch.object(bootstrap.platform,'machine',return_value='x86_64'):
   with self.assertRaisesRegex(ValueError,'native macOS ARM64'):bootstrap.binary_pair(ROOT,P('/nonexistent'))
