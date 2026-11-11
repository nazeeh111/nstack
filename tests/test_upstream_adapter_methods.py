"""Replay pinned original methods without acquiring or executing their tools."""
import hashlib,json,pathlib,re,sys,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'lib')]
from patch_native34 import materialize,front
from closure import validate
P=pathlib.Path
MARKER='\n> Native host binding: read [NATIVE-BINDINGS.md](NATIVE-BINDINGS.md) before source commands. The complete upstream method follows.\n'
METHOD_SHA256={
 'skill-seekers-import':'869cb60789394aa6bf94559579adecd4e36cf7979e7089ea0b8aa9e7fb73e025',
 'slidev-production':'3b1b7fd100b3bbc93fbadfeac13092cbf81410a81d16b3ffd5d1716f4a2a3c82',
 'impeccable-audit':'5ba9e3a090fc4c4d212c8cbfa5a48f7454ceb10fa81a284b4a7b4e8351ece2f1',
 'impeccable-harden':'4167eb7fc456cdfe09ff0ac2dbcb5e59cee57e590137aab6cc8ec08aafb6d775',
}

class OriginalAdapters(unittest.TestCase):
 def test_source_frontmatter_survives_with_only_explicit_changes(self):
  raw='---\nname: source-name\ndescription: >-\n  First source line\n  second source line.\nlicense: Apache-2.0\nmetadata:\n  version: 4.8.0\n  custom: [one, two]\ndisable-model-invocation: true\n---\n\nExact source body.\n'
  self.assertEqual(front(raw,'natural-name'),raw.replace('name: source-name','name: natural-name',1))
  expected=raw.replace('name: source-name','name: natural-name',1).replace('description: >-\n  First source line\n  second source line.','description: "Scoped explicit description"',1)
  self.assertEqual(front(raw,'natural-name','Scoped explicit description'),expected)

 def test_original_distributed_methods_and_complete_support(self):
  registry=json.loads((ROOT/'registry/manifest.json').read_text());components={c['id']:c for c in registry['components']}
  selected=[s for s in registry['skills']if s['candidate_id']in('P029','P410','P202')and s.get('native_name')]
  self.assertEqual(len(selected),4)
  for s in selected:
   source=P.home()/'Library/Application Support/nstack/sources'/s['source_repository'].replace('/','--')/s['revision']
   if not source.is_dir():self.skipTest('Pinned offline sources unavailable')
   with self.subTest(name=s['native_name']),tempfile.TemporaryDirectory()as temp:
    out=P(temp);entry=out/materialize(source,out,s,components[s['candidate_id']]);meta=json.loads((out/'SOURCE-PORT.json').read_text())
    raw=source/meta['method_source_path'];original=raw.read_text();active=(entry/'SKILL.md').read_text().replace(MARKER,'',1)
    self.assertEqual(hashlib.sha256(raw.read_bytes()).hexdigest(),METHOD_SHA256[s['native_name']])
    if s['candidate_id']=='P202':self.assertEqual(active.split('\n---\n',1)[1],original)
    else:self.assertEqual(re.sub(r'(?m)^name:.*$',re.search(r'(?m)^name:.*$',original)[0],active,count=1),original)
    self.assertEqual(meta['source_path'],s['source_path'])
    self.assertEqual(meta['method_revision'],s['revision'])
    self.assertEqual(meta['method_sha256'],hashlib.sha256(raw.read_bytes()).hexdigest())
    for f in raw.parent.rglob('*'):
     if f.is_file()and f.name!='SKILL.md':self.assertEqual((entry/f.relative_to(raw.parent)).read_bytes(),f.read_bytes())
    self.assertEqual((out/'upstream'/s['source_path']).read_bytes(),(source/s['source_path']).read_bytes())
    self.assertTrue((entry/'NATIVE-BINDINGS.md').is_file());validate(out,provenance_roots=('upstream',))
    if s['candidate_id']=='P410':self.assertEqual(len(list((entry/'references').glob('*.md'))),53)

 def test_raea_original_main_and_primary_source_closure(self):
  addon=ROOT/'addons/raea';meta=json.loads((addon/'SOURCE.json').read_text());original=(addon/'UPSTREAM_SKILL.md').read_bytes()
  self.assertEqual(meta['method_source_path'],'skills/raea/SKILL.md')
  self.assertEqual(meta['method_revision'],'c507860150995eb7c22ef9db23dee636c832428a')
  self.assertEqual(hashlib.sha256(original).hexdigest(),meta['method_sha256'])
  self.assertEqual(meta['method_sha256'],'e215226af5cbf44ad5bbe57a41908700eeffe2748a29a56a7aceba743ce0da2d')
  marker='\n> Native offline execution: read [NATIVE-BINDINGS.md](NATIVE-BINDINGS.md) before source commands. The complete upstream method follows.\n'
  self.assertEqual((addon/'SKILL.md').read_text().replace(marker,'',1),original.decode())
  self.assertIn('raea-tested-against: 0.1.0-rc1',original.decode());self.assertEqual(meta['version'],'0.1.0')
  self.assertEqual(len(meta['source_files']),84)
  self.assertEqual(hashlib.sha256(json.dumps(meta['source_files'],sort_keys=True).encode()).hexdigest(),'608ae91b444724c30b67e78153b083a81232e0287bd474993010751ad11a0bb1')
  for source,row in meta['source_files'].items():
   data=original if row['path']=='SKILL.md'else(addon/row['path']).read_bytes()
   self.assertEqual(hashlib.sha256(data).hexdigest(),row['sha256'],source)
   self.assertEqual(hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(),row['git_blob'],source)
  validate(addon)
  self.assertEqual(len(list(addon.rglob('SKILL.md'))),1)
  self.assertIn('Apache License',(addon/'LICENSE').read_text())
  binding=(addon/'NATIVE-BINDINGS.md').read_text();self.assertIn('run --offline',binding);self.assertIn('capability gaps',binding)

if __name__=='__main__':unittest.main()
