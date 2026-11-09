import io,json,pathlib,sys,tarfile,tempfile,unittest
from unittest.mock import patch
P=pathlib.Path;sys.path.insert(0,str(P(__file__).resolve().parents[1]/'lib'));import node_artifact
class NodeArtifact(unittest.TestCase):
 def archive(self,path,data,extra=None):
  with tarfile.open(path,'w:gz') as archive:
   for name,raw in [('package/package.json',json.dumps(data).encode()),*(extra or [])]:
    item=tarfile.TarInfo(name);item.size=len(raw);archive.addfile(item,io.BytesIO(raw))
 def test_resolved_identity_and_unresolved_runtime_specs(self):
  with tempfile.TemporaryDirectory() as t:
   file=P(t)/'input.tgz';base={'name':'fixture','version':'1.0.0','dependencies':{'local':'1.2.3'}};self.archive(file,base);self.assertTrue(node_artifact.inspect(file,'fixture','1.0.0')['runtime_dependency_protocols_resolved'])
   with self.assertRaisesRegex(ValueError,'name differs'):node_artifact.inspect(file,'wrong')
   for spec in ('workspace:*','catalog:','link:../local','file:../local'):
    base['dependencies']['local']=spec;self.archive(file,base)
    with self.assertRaisesRegex(ValueError,'Unresolved'):node_artifact.inspect(file)
 def test_escape_or_private_material_is_never_extracted(self):
  with tempfile.TemporaryDirectory() as t:
   file=P(t)/'input.tgz'
   for name in ('package/../escape','package/.env','package/.aws/credentials','package/.npmrc'):
    self.archive(file,{'name':'fixture','version':'1.0.0'},[(name,b'inert fixture')])
    with self.assertRaises(ValueError):node_artifact.inspect(file)
   self.assertFalse((P(t)/'escape').exists())
 def test_bundle_requires_local_closure_and_checks_every_archive(self):
  with tempfile.TemporaryDirectory() as t:
   root=P(t);source=root/'source';source.mkdir();packs=root/'packs';packs.mkdir()
   main={'name':'main','version':'1.0.0','workspaces':['packages/*'],'dependencies':{'local':'workspace:*'}}
   (source/'package.json').write_text(json.dumps(main));local=source/'packages/local';local.mkdir(parents=True);(local/'package.json').write_text(json.dumps({'name':'local','version':'2.0.0'}))
   packed=main|{'dependencies':{'local':'2.0.0'}};self.archive(packs/'main.tgz',packed)
   with self.assertRaisesRegex(ValueError,'incomplete'):node_artifact.inspect_bundle(packs,source,'main')
   self.archive(packs/'local.tgz',{'name':'local','version':'2.0.0'});r=node_artifact.inspect_bundle(packs,source,'main','1.0.0');self.assertEqual(len(r['required_packages']),2);self.assertEqual({x['archive'] for x in r['required_packages']},{'main.tgz','local.tgz'})
   with self.assertRaisesRegex(ValueError,'source version'):node_artifact.inspect_bundle(packs,source,'main','9.0.0')
   self.archive(packs/'bad-extra.tgz',{'name':'unused','version':'1','dependencies':{'x':'workspace:*'}})
   with self.assertRaisesRegex(ValueError,'Unresolved'):node_artifact.inspect_bundle(packs,source,'main')
   (packs/'bad-extra.tgz').unlink();self.archive(packs/'main.tgz',main|{'dependencies':{}})
   with self.assertRaisesRegex(ValueError,'dropped'):node_artifact.inspect_bundle(packs,source,'main')
   self.archive(packs/'main.tgz',main|{'dependencies':{'local':'999.0.0'}})
   with self.assertRaisesRegex(ValueError,'cannot be satisfied'):node_artifact.inspect_bundle(packs,source,'main')
   for spec in ('^2.0.0','~2.0.0','>=2.0.0 <3.0.0'):
    self.archive(packs/'main.tgz',main|{'dependencies':{'local':spec}});self.assertTrue(node_artifact.inspect_bundle(packs,source,'main')['complete_native_source_closure'])
 def test_optional_platform_and_libc_are_native_only(self):
  with tempfile.TemporaryDirectory() as t:
   root=P(t);source=root/'source';source.mkdir();packs=root/'packs';packs.mkdir()
   main={'name':'main','version':'1','workspaces':['packages/*'],'optionalDependencies':{'gnu':'workspace:*','musl':'workspace:*','foreign':'workspace:*'}}
   (source/'package.json').write_text(json.dumps(main))
   for name,meta in [('gnu',{'os':['linux'],'libc':['glibc']}),('musl',{'os':['linux'],'libc':['musl']}),('foreign',{'os':['win32']})]:
    folder=source/'packages'/name;folder.mkdir(parents=True);(folder/'package.json').write_text(json.dumps({'name':name,'version':'1',**meta}))
   self.archive(packs/'main.tgz',main|{'optionalDependencies':dict.fromkeys(main['optionalDependencies'],'1')});self.archive(packs/'gnu.tgz',{'name':'gnu','version':'1'})
   with patch.object(node_artifact.sys,'platform','linux'),patch.object(node_artifact.platform,'libc_ver',return_value=('glibc','2.40')):
    r=node_artifact.inspect_bundle(packs,source,'main');self.assertEqual({x['name'] for x in r['required_packages']},{'main','gnu'})
if __name__=='__main__':unittest.main()
