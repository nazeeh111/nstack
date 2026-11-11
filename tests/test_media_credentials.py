"""Offline admission checks. All target I/O/providers are synthetic tripwires."""
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'lib'))
from patch_media import finalize_credentials, PRIVACY_BOUNDARY


PIN = '3d78ac0fa6671c31ba69186d084951aeb8dc8e18'
SOURCE = pathlib.Path(os.environ.get('NSTACK_TEST_P215_SOURCE', str(
    pathlib.Path.home() / 'Library/Application Support/nstack/sources/heygen-com--hyperframes' / PIN)))


@unittest.skipUnless(SOURCE.is_dir(), 'Acquire the exact pinned P215 source for offline client-admission checks')
class MediaCredentials(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = pathlib.Path(self.temp.name)
        self.source = self.base / 'source'
        self.out = self.base / 'out'
        self.source.mkdir()
        # Exact selected source is data; these tests never import its real dependencies.
        for name in ('hyperframes', 'hyperframes-cli', 'hyperframes-registry', 'media-use'):
            shutil.copytree(SOURCE / 'skills' / name, self.source / 'skills' / name)
        shutil.copytree(self.source, self.out)
        self.spec = {'candidate_id': 'P215', 'source_repository': 'heygen-com/hyperframes', 'revision': PIN}

    def patch(self):
        finalize_credentials(self.source, self.out, self.spec)

    def node(self, code, data):
        node = shutil.which('node')
        self.assertIsNotNone(node, 'Node is required for synthetic VM boundary checks')
        # No inherited keys, user HOME, NODE_OPTIONS or provider environment.
        env = {'PATH': os.path.dirname(node), 'HOME': str(self.base), 'DO_NOT_TRACK': '1', 'HYPERFRAMES_NO_TELEMETRY': '1'}
        result = subprocess.run([node, '--experimental-vm-modules', '--input-type=module', '-e', code],
                                input=json.dumps(data), text=True, capture_output=True,
                                cwd=self.base, env=env, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_exact_originals_diff_and_full_methods_survive(self):
        self.patch()
        record = self.out / 'NATIVE-PRIVACY'
        meta = json.loads((record / 'SOURCE-ADAPTATION.json').read_text())
        self.assertEqual(meta['revision'], PIN)
        for item in meta['files']:
            original = (self.source / item['path']).read_bytes()
            self.assertEqual((self.out / item['original']).read_bytes(), original)
            self.assertEqual(hashlib.sha256(original).hexdigest(), item['upstream_sha256'])
            self.assertEqual(hashlib.sha256((self.out / item['path']).read_bytes()).hexdigest(), item['active_sha256'])
            if item['path'].endswith('.md'):
                active = (self.out / item['path']).read_text()
                self.assertEqual(active.replace('\n\n' + PRIVACY_BOUNDARY + '\n', '\n\n', 1).lstrip('\n'),
                                 original.decode().lstrip('\n'))
        self.assertIn('function storedCredential()', (record / 'ADAPTATION.patch').read_text())
        for name in ('audio.mjs', 'heygen-tts.mjs', 'heygen-voice.mjs'):
            rel = pathlib.Path('skills/media-use/audio/scripts') / name
            active = (self.out / rel).read_text()
            self.assertIn((self.source / rel).read_text().split('\n', 1)[1], active)
        for name in ('sfx.mjs', 'bgm.mjs', 'tts.mjs', 'gemini-auth.mjs'):
            rel = pathlib.Path('skills/media-use/audio/scripts/lib') / name
            self.assertEqual((self.source / rel).read_bytes(), (self.out / rel).read_bytes())

    def test_shared_helper_no_discovery_and_no_rest_with_tripwire_control(self):
        original = (self.source / 'skills/media-use/audio/scripts/lib/heygen.mjs').read_text()
        self.patch()
        patched = (self.out / 'skills/media-use/audio/scripts/lib/heygen.mjs').read_text()
        result = self.node(r'''
import vm from 'node:vm'; import path from 'node:path';
let input=''; for await (const x of process.stdin) input+=x;
const sources=JSON.parse(input), rows=[];
for (const source of sources) {
  let reads=0, calls=0, homes=0;
  const context=vm.createContext({process:{env:{HEYGEN_API_KEY:'synthetic',GEMINI_API_KEY:'synthetic'}},
    URL,URLSearchParams,Buffer,fetch:()=>{calls++;throw Error('network tripwire');}});
  const mod=new vm.SourceTextModule(source,{context});
  await mod.link(async (name)=>{
    const exports=name==='node:fs'?{readFileSync(){reads++;throw Error('file tripwire');},mkdirSync(){},writeFileSync(){}}:
      name==='node:os'?{homedir(){homes++;return '/synthetic-home';}}:
      name==='node:path'?{dirname:path.dirname,join:path.join,resolve:path.resolve}:
      {fetchMedia(){calls++;throw Error('download tripwire');}};
    return new vm.SyntheticModule(Object.keys(exports),function(){for(const [k,v]of Object.entries(exports))this.setExport(k,v);},{context});
  });
  await mod.evaluate();
  try{mod.namespace.loadEnvFromDir('/synthetic-project/child');}catch{}
  const credential=mod.namespace.heygenCredential();
  let authBlocked=false,restBlocked=false;
  try{mod.namespace.heygenAuthHeaders();}catch(e){authBlocked=/UNADMITTED/.test(e.message);}
  if(rows.length){try{await mod.namespace.heygenJSON('/voices',{headers:{Authorization:'synthetic'}});}catch(e){restBlocked=/UNADMITTED/.test(e.message);}}
  rows.push({reads,calls,homes,absent:credential===null,authBlocked,restBlocked});
}
console.log(JSON.stringify(rows));
''', [original, patched])
        self.assertGreater(result[0]['reads'], 0, 'Original control must hit synthetic discovery tripwire')
        self.assertEqual(result[1], {'reads': 0, 'calls': 0, 'homes': 0, 'absent': True, 'authBlocked': True, 'restBlocked': True})

    def test_all_three_command_startups_refuse_before_io_for_every_mode(self):
        self.patch()
        scripts = {name: (self.out / 'skills/media-use/audio/scripts' / name).read_text()
                   for name in ('audio.mjs', 'heygen-tts.mjs', 'heygen-voice.mjs')}
        result = self.node(r'''
import vm from 'node:vm'; let input='';for await(const x of process.stdin)input+=x;
const sources=JSON.parse(input),rows=[];
for(const [name,source]of Object.entries(sources))for(const argv of [[],['--provider','kokoro','--no-bgm'],['--only','sfx'],['--list'],['delete','synthetic']]){
  let effects=0;
  const tripwire=()=>{effects++;throw Error('side-effect tripwire');};
  const context=vm.createContext({process:{argv:['node',name,...argv],env:{},cwd:tripwire,exit:tripwire},console:{error:tripwire,log:tripwire}});
  const names={};for(const m of source.matchAll(/import\s*\{([^}]+)\}\s*from\s*['"]([^'"]+)['"]/gs)){
    names[m[2]]=m[1].split(',').map(x=>x.trim()).filter(Boolean);
  }
  const mod=new vm.SourceTextModule(source,{context,initializeImportMeta(meta){meta.url='file:///synthetic/'+name;}});
  await mod.link(async id=>new vm.SyntheticModule(names[id]||[],function(){for(const x of names[id]||[])this.setExport(x,tripwire);},{context}));
  let blocked=false;try{await mod.evaluate();}catch(e){blocked=/UNADMITTED/.test(e.message);}
  rows.push({name,blocked,effects});
}
console.log(JSON.stringify(rows));
''', scripts)
        self.assertEqual(len(result), 15)
        self.assertTrue(all(r['blocked'] and r['effects'] == 0 for r in result), result)

    def test_every_selected_entry_and_provider_reference_states_blocked_boundary(self):
        self.patch()
        for name in ('hyperframes', 'hyperframes-cli', 'hyperframes-registry', 'media-use'):
            text = (self.out / 'skills' / name / 'SKILL.md').read_text()
            self.assertTrue(text.startswith('---\n'))
            self.assertIn(PRIVACY_BOUNDARY, text)
        for rel in ('audio/references/tts.md', 'references/setup-providers.md', 'references/heygen.md', 'references/operations.md'):
            text = (self.out / 'skills/media-use' / rel).read_text()
            self.assertIn('UNADMITTED', text)
            self.assertIn('media-use --local-only', text)
            self.assertIn('empty task-owned temporary working directory', text)
            self.assertIn('separate fresh empty process home', text)
            self.assertIn('no literal script text or project paths in argv', text)
            self.assertIn('no provider keys, config-directory overrides or NODE_OPTIONS', text)
            for setting in ('HYPERFRAMES_NO_UPDATE_CHECK=1', 'HYPERFRAMES_NO_AUTO_INSTALL=1', 'HYPERFRAMES_SKIP_SKILLS=1'):
                self.assertIn(setting, text)
        with self.assertRaises(ValueError):
            self.patch()


if __name__ == '__main__':
    unittest.main()
