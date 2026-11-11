"""Replay the exact offline DevTools leaf; never start a server or read config."""
import hashlib
import json
import os
import pathlib
import re
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'lib'))
from patch_devtools import OLD, NEW, REVISION
from skill_build import materialize


class DevToolsNative(unittest.TestCase):
    def test_prerequisite_only_change_preserves_methods_support_and_original(self):
        default = pathlib.Path.home() / 'Library/Application Support/nstack/sources/ChromeDevTools--chrome-devtools-mcp' / REVISION
        source = pathlib.Path(os.environ.get('NSTACK_DEVTOOLS_SOURCE', default))
        receipt_path = source / '.nstack-source.json'
        if not receipt_path.is_file():
            self.skipTest('Exact offline DevTools source unavailable; no network acquisition')
        receipt = json.loads(receipt_path.read_text())
        self.assertEqual(receipt['revision'], REVISION)
        self.assertEqual(receipt['repository'], 'ChromeDevTools/chrome-devtools-mcp')
        manifest = json.loads((ROOT / 'registry/manifest.json').read_text())
        component = next(c for c in manifest['components'] if c['id'] == 'P065')
        specs = [s for s in manifest['skills'] if s['candidate_id'] == 'P065']
        self.assertEqual(len(specs), 2)
        with tempfile.TemporaryDirectory(prefix='nstack-devtools-') as temp:
            for spec in specs:
                folder = source / pathlib.Path(spec['source_path']).parent
                for file in folder.rglob('*'):
                    if file.is_file():
                        self.assertEqual(hashlib.sha256(file.read_bytes()).hexdigest(), receipt['files'][str(file.relative_to(source))])
                out = pathlib.Path(temp) / folder.name
                out.mkdir()
                materialize(source, out, spec, component, manifest)
                # Match native_setup's natural entry-name normalization.
                entry = out / 'SKILL.md'
                entry.write_text(re.sub(r'(?m)^name:.*$', 'name: ' + folder.name, entry.read_text(), count=1))
                original = (folder / 'SKILL.md').read_bytes()
                if folder.name == 'memory-leak-debugging':
                    final = (out / 'SKILL.md').read_bytes()
                    self.assertEqual(final, original.decode().replace(OLD, NEW).encode())
                    self.assertEqual((out / 'upstream-original/SKILL.md.txt').read_bytes(), original)
                    record = json.loads((out / 'NATIVE-ADAPTATION.json').read_text())
                    self.assertEqual(record['source_sha256'], hashlib.sha256(original).hexdigest())
                    self.assertEqual(record['native_sha256'], hashlib.sha256(final).hexdigest())
                    self.assertEqual(len((out / 'ADAPTATION.patch').read_text().split('@@')) - 1, 2)
                else:
                    self.assertEqual(spec['delivery'], 'intact upstream leaf')
                    self.assertEqual((out / 'SKILL.md').read_bytes(), original)
                for file in folder.rglob('*'):
                    if file.is_file() and file.name != 'SKILL.md':
                        self.assertEqual((out / file.relative_to(folder)).read_bytes(), file.read_bytes())


if __name__ == '__main__':
    unittest.main()
