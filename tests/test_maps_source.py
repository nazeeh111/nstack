"""Exact original Maps workflow/support stays active; no scraper is executed."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT / 'addons/google-maps-scraper'
# Independent immutable-primary Git-blob acquisition, not the package manifest.
SOURCE_MAP_SHA256 = 'beaffc24bf9ca1d239e3b36e1709bd253c1dd1a4c988817cb7c3e88534be333c'
ORIGINAL_SKILL_SHA256 = '0b733b979b083683c2af36e52a7bd113ae2a4b1845fee66479d40f7aa20c5eec'


class MapsSource(unittest.TestCase):
    def test_complete_original_skill_and_all_selected_source_bytes(self):
        meta = json.loads((ADDON / 'SOURCE.json').read_text())
        self.assertEqual(meta['source_path'], 'skills/google-maps-scraper/SKILL.md')
        self.assertEqual(meta['revision'], '146aefe83844960bb534f335261a4435783a58cc')
        mapping = {k: v['sha256'] for k, v in meta['source_files'].items()}
        self.assertEqual(hashlib.sha256(json.dumps(mapping, sort_keys=True).encode()).hexdigest(), SOURCE_MAP_SHA256)
        self.assertEqual(len(mapping), 17)
        original = (ADDON / 'UPSTREAM_SKILL.md').read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(), ORIGINAL_SKILL_SHA256)
        marker = '\n> Native execution and access: read [NATIVE-BINDINGS.md](NATIVE-BINDINGS.md) before source commands. Full original workflow follows.\n'
        self.assertEqual((ADDON / 'SKILL.md').read_text().replace(marker, '', 1), original.decode())
        for source, row in meta['source_files'].items():
            data = original if row['path'] == 'SKILL.md' else (ADDON / row['path']).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), row['sha256'], source)
            self.assertEqual(hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest(), row['git_blob'])
            if row['path'] != 'SKILL.md':
                self.assertEqual(bool((ADDON / row['path']).stat().st_mode & 0o111), row['git_mode'] == '100755')
        self.assertEqual(sum(k.endswith('.md') and '/references/' in k for k in mapping), 6)
        self.assertEqual(sum('/scripts/' in k for k in mapping), 8)
        self.assertIn('Permission is hereby granted', (ADDON / 'LICENSE').read_text())

    def test_fast_sample_is_separate_and_real_client_access_stays_conditional(self):
        bindings = (ADDON / 'NATIVE-BINDINGS.md').read_text()
        self.assertIn('automatic self-refresh', bindings)
        self.assertIn('is not admitted', bindings)
        self.assertIn('not authorized setup', bindings)
        self.assertIn('never replacement', json.loads((ADDON / 'SOURCE.json').read_text())['adaptation'])
        self.assertIn('separate', (ADDON / 'references/native-fast-mode.md').read_text())
        self.assertEqual(list(ADDON.rglob('SKILL.md')), [ADDON / 'SKILL.md'])


if __name__ == '__main__':
    unittest.main()
