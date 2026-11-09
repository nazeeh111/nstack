import pathlib,tempfile,unittest,sys,os,stat
P=pathlib.Path;sys.path.insert(0,str(P(__file__).resolve().parents[1]/'lib'));from transaction import Transaction,fingerprint
class TransactionTests(unittest.TestCase):
 def test_apply_restart_idempotence_restore(self):
  with tempfile.TemporaryDirectory() as t:
   root=P(t).resolve();run=root/'run';file=root/'config';file.write_text('before');collection=root/'skills';collection.mkdir();(collection/'private.txt').write_text('useful bytes');link=root/'entry';link.symlink_to('old');before={str(p):fingerprint(p) for p in [file,collection,link]}
   tx=Transaction(run)
   with tx.lock():tx.replace_file(file,b'after');tx.retire(collection);tx.link(link,'new')
   journal=(run/'journal.json').read_bytes();tx=Transaction(run)
   with tx.lock():tx.replace_file(file,b'after');tx.retire(collection);tx.link(link,'new')
   self.assertEqual(journal,(run/'journal.json').read_bytes())
   with tx.lock():tx.rollback()
   self.assertEqual(before,{str(p):fingerprint(p) for p in [file,collection,link]})
 def test_later_edit_conflict_preserved(self):
  with tempfile.TemporaryDirectory() as t:
   root=P(t).resolve();p=root/'file';p.write_text('before');tx=Transaction(root/'run')
   with tx.lock():tx.replace_file(p,b'after')
   p.write_text('later work')
   with self.assertRaisesRegex(ValueError,'conflict'):
    with tx.lock():tx.rollback()
   self.assertEqual(p.read_text(),'later work')
if __name__=='__main__':unittest.main()

class RecoveryTests(unittest.TestCase):
 def test_expected_source_baseline_rejects_concurrent_edit(self):
  with tempfile.TemporaryDirectory() as t:
   root=P(t).resolve();p=root/'config';p.write_text('before');before=fingerprint(p);p.write_text('client edit');tx=Transaction(root/'run')
   with tx.lock():
    with self.assertRaisesRegex(ValueError,'Concurrent'):tx.replace_file(p,b'stale derived result',expected=before)
   self.assertEqual(p.read_text(),'client edit')
 def test_two_precreated_instances_reload_journal_under_lock(self):
  with tempfile.TemporaryDirectory() as t:
   root=P(t).resolve();a=Transaction(root/'runs/same');b=Transaction(root/'runs/same');one=root/'one';two=root/'two'
   with a.lock():a.replace_file(one,b'one')
   with b.lock():b.replace_file(two,b'two')
   with a.lock():self.assertEqual(len(a.rows),2);a.rollback()
   self.assertFalse(one.exists());self.assertFalse(two.exists())
 def test_reconcile_crash_after_merged_config_restore(self):
  import config_merge as cm
  with tempfile.TemporaryDirectory() as t:
   root=P(t).resolve();p=root/'config';before='owned=1\nother=1\n';updates=[(['owned'],2)];after=cm.apply(before,updates,[]);p.write_text(before);tx=Transaction(root/'run');(tx.run/'config-after.toml').write_text(after)
   with tx.lock():tx.replace_file(p,after.encode(),config={'updates':updates,'retire':[]})
   p.write_text(after.replace('other=1','other=3'))
   # Inject loss of journal acknowledgement after the actual replacement.
   original=tx.save;calls=[0]
   def lost_ack():
    if tx.rows[0]['phase']=='rolled-back':raise RuntimeError('synthetic process death after restore')
    original()
   with tx.lock():
    tx.save=lost_ack
    with self.assertRaisesRegex(RuntimeError,'synthetic'):tx.rollback()
   retry=Transaction(root/'run')
   with retry.lock():retry.rollback();self.assertEqual(retry.rows[0]['phase'],'rolled-back')
   self.assertEqual(cm.tomllib.loads(p.read_text()),{'owned':1,'other':3});self.assertEqual(p.stat().st_mode&0o777,0o644)
 @unittest.skipUnless(sys.platform=='darwin','macOS metadata contract')
 def test_mac_xattr_acl_and_directory_mode_roundtrip(self):
  import subprocess
  from transaction import metadata
  with tempfile.TemporaryDirectory() as t:
   root=P(t).resolve();p=root/'config';p.write_text('before');os.chflags(p,stat.UF_TRACKED);subprocess.run(['/usr/bin/xattr','-w','com.nstack.fixture','retained',str(p)],check=True);subprocess.run(['/bin/chmod','+a','everyone allow readattr',str(p)],check=True);before=fingerprint(p);tx=Transaction(root/'run')
   with tx.lock():tx.replace_file(p,b'after',0o600)
   self.assertEqual(metadata(p)['xattrs'],before['metadata']['xattrs']);self.assertEqual(metadata(p)['acl_sha256'],before['metadata']['acl_sha256'])
   with tx.lock():tx.rollback()
   self.assertEqual(fingerprint(p),before)

class PreparationCrashTests(unittest.TestCase):
 def test_interrupted_backup_copy_resumes(self):
  import transaction as module
  with tempfile.TemporaryDirectory() as t:
   root=P(t).resolve();p=root/'file';p.write_text('original complete bytes');tx=Transaction(root/'run');original_copy=module.copy
   def partial(src,dest):
    if str(dest).endswith('/before/0'):
     P(dest).parent.mkdir(parents=True,exist_ok=True);P(dest).write_text('partial');raise RuntimeError('synthetic death during backup')
    return original_copy(src,dest)
   try:
    module.copy=partial
    with tx.lock():
     with self.assertRaisesRegex(RuntimeError,'during backup'):tx.replace_file(p,b'new bytes')
   finally:module.copy=original_copy
   self.assertEqual(p.read_text(),'original complete bytes')
   retry=Transaction(root/'run')
   with retry.lock():retry.replace_file(p,b'new bytes');retry.rollback()
   self.assertEqual(p.read_text(),'original complete bytes')
 def test_interrupted_restore_copy_resumes(self):
  import transaction as module
  with tempfile.TemporaryDirectory() as t:
   root=P(t).resolve();p=root/'file';p.write_text('original complete bytes');tx=Transaction(root/'run')
   with tx.lock():tx.replace_file(p,b'new bytes')
   original_copy=module.copy
   def partial(src,dest):
    if '/rollback-stage/' in str(dest):P(dest).write_text('partial');raise RuntimeError('synthetic death during restore copy')
    return original_copy(src,dest)
   try:
    module.copy=partial
    with tx.lock():
     with self.assertRaisesRegex(RuntimeError,'during restore copy'):tx.rollback()
   finally:module.copy=original_copy
   self.assertEqual(p.read_text(),'new bytes')
   retry=Transaction(root/'run')
   with retry.lock():retry.rollback()
   self.assertEqual(p.read_text(),'original complete bytes')
