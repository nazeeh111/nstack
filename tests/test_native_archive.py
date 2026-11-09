import io,pathlib,sys,tarfile,tempfile,unittest
P=pathlib.Path;sys.path.insert(0,str(P(__file__).resolve().parents[1]/'lib'));import native_archive
class Archive(unittest.TestCase):
 def make(self,path,entries):
  with tarfile.open(path,'w:gz') as tar:
   for name,kind,body in entries:
    item=tarfile.TarInfo(name);item.mode=0o755
    if kind=='link':item.type=tarfile.SYMTYPE;item.linkname=body;tar.addfile(item)
    else:item.size=len(body);tar.addfile(item,io.BytesIO(body))
 def test_exact_prefix_regular_file_and_executable(self):
  with tempfile.TemporaryDirectory() as t:
   root=P(t);archive=root/'input.tar.gz';out=root/'out';out.mkdir();self.make(archive,[('go/bin/compiler','file',b'synthetic executable')]);native_archive.unpack(archive,out,'go');self.assertEqual((out/'bin/compiler').read_bytes(),b'synthetic executable');self.assertTrue((out/'bin/compiler').stat().st_mode&0o100)
 def test_escape_link_duplicate_and_wrong_prefix_rejected(self):
  fixtures=[[('go/../../outside','file',b'x')],[('/absolute','file',b'x')],[('go/link','link','../../outside')],[('other/bin/compiler','file',b'x')],[('go/file','file',b'first'),('go/file','file',b'second')]]
  for entries in fixtures:
   with self.subTest(entries=entries),tempfile.TemporaryDirectory() as t:
    root=P(t);archive=root/'input.tar.gz';out=root/'out';out.mkdir();self.make(archive,entries)
    with self.assertRaises(ValueError):native_archive.unpack(archive,out,'go')
    self.assertFalse((root/'outside').exists())
 def test_nested_receipt_name_remains_in_integrity_manifest(self):
  with tempfile.TemporaryDirectory() as t:
   root=P(t);(root/'TOOLCHAIN.json').write_text('root receipt');(root/'nested').mkdir();(root/'nested/TOOLCHAIN.json').write_text('must be hashed');self.assertEqual(set(native_archive.tree(root)),{'nested/TOOLCHAIN.json'})
if __name__=='__main__':unittest.main()
