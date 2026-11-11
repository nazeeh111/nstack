"""Pinned private-source acquisition and source-derived addon integrity, offline."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ADDONS = ROOT / 'addons'
spec = importlib.util.spec_from_file_location('private_source_fetch', ADDONS / 'llm-council/scripts/fetch_source.py')
fetcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetcher)


class PrivateSourceTests(unittest.TestCase):
    def fixture(self, base):
        source = base / 'source'
        source.mkdir()
        files = {'SKILL.md': b'fixture complete method\n', 'references/nested.md': b'fixture support\n'}
        for name, data in files.items():
            target = source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        manifest = base / 'manifest.json'
        data = {'repository': 'fixture/source', 'revision': '1' * 40,
                'files': {name: hashlib.sha256(content).hexdigest() for name, content in files.items()}}
        manifest.write_text(json.dumps(data))
        return source, manifest, files

    def test_complete_source_bytes_private_modes_and_existing_target_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source, manifest, files = self.fixture(base)
            target = base / 'private'
            result = fetcher.fetch(target, manifest, source)
            self.assertFalse(result['upstream_code_executed'])
            self.assertEqual(result['files'], json.loads(manifest.read_text())['files'])
            self.assertEqual(target.stat().st_mode & 0o777, 0o700)
            for name, content in files.items():
                self.assertEqual((target / name).read_bytes(), content)
                self.assertEqual((target / name).stat().st_mode & 0o777, 0o600)
            sentinel = target / 'user-owned'
            sentinel.write_bytes(b'preserve unrelated bytes')
            with self.assertRaises(FileExistsError):
                fetcher.fetch(target, manifest, source)
            self.assertEqual(sentinel.read_bytes(), b'preserve unrelated bytes')

    def test_wrong_source_hash_rolls_back_only_this_new_pack(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source, manifest, files = self.fixture(base)
            (source / 'references/nested.md').write_bytes(b'changed revision')
            target = base / 'bad'
            sibling = base / 'keep'
            sibling.write_bytes(b'original')
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                fetcher.fetch(target, manifest, source)
            self.assertFalse(target.exists())
            self.assertEqual(sibling.read_bytes(), b'original')
            self.assertEqual((source / 'SKILL.md').read_bytes(), files['SKILL.md'])

    def test_traversal_and_source_symlink_are_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source, manifest, files = self.fixture(base)
            data = json.loads(manifest.read_text())
            original = manifest.read_bytes()
            data['files']['../escape'] = 'a' * 64
            manifest.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                fetcher.fetch(base / 'private', manifest, source)
            self.assertFalse((base / 'private').exists())
            manifest.write_bytes(original)
            outside = base / 'outside'
            outside.write_bytes(files['SKILL.md'])
            (source / 'SKILL.md').unlink()
            (source / 'SKILL.md').symlink_to(outside)
            with self.assertRaisesRegex(ValueError, 'cache'):
                fetcher.fetch(base / 'private', manifest, source)
            self.assertFalse((base / 'private').exists())
            self.assertEqual(outside.read_bytes(), files['SKILL.md'])


class SourceClosureTests(unittest.TestCase):
    def test_bundled_originals_and_native_derivatives_match_recorded_hashes(self):
        for name, count in [('roast-room', 12), ('council-of-high-intelligence', 18)]:
            folder = ADDONS / name
            meta = json.loads((folder / 'SOURCE.json').read_text())
            self.assertEqual(len(list((folder / 'personas').glob('council-*.md'))), count)
            for row in meta['files']:
                self.assertEqual(hashlib.sha256((folder / row['path']).read_bytes()).hexdigest(), row['sha256'], row['path'])
            self.assertEqual(hashlib.sha256((folder / 'patches/native.patch').read_bytes()).hexdigest(), meta['patch_sha256'])
            # Archival source must not become a second discoverable skill entrypoint.
            self.assertEqual(list(folder.rglob('SKILL.md')), [folder / 'SKILL.md'])

    def test_private_manifests_retain_actual_full_source_closures(self):
        remy = json.loads((ADDONS / 'llm-council/private-source.json').read_text())
        roast = json.loads((ADDONS / 'roast-room/private-source.json').read_text())
        self.assertEqual(set(remy['files']), {'README.md', 'SKILL.md'})
        brains = [name for name in roast['files'] if '/brains/' in name]
        self.assertEqual(len(brains), 96)
        self.assertEqual(len({Path(name).parent.name for name in brains}), 12)
        self.assertFalse((ADDONS / 'roast-room/brains').exists())
        for row in json.loads((ADDONS / 'roast-room/SOURCE.json').read_text())['files']:
            self.assertNotIn('/brains/', row['path'])
        self.assertEqual((ADDONS / 'llm-council/scripts/fetch_source.py').read_bytes(),
                         (ADDONS / 'roast-room/scripts/fetch_source.py').read_bytes())

    def test_quote_lint_requires_explicit_existing_corpus_and_flags_unmatched_excerpt(self):
        script = ADDONS / 'roast-room/scripts/check_quotes.py'
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            session = base / 'session'
            session.mkdir()
            brains = base / 'brains'
            (brains / 'seat').mkdir(parents=True)
            quote = 'A measured fixture statement contains seven distinct words here'
            (brains / 'seat/principles.md').write_text(quote)
            (session / 'round-1.md').write_text(f'"{quote}" (S001)')
            args = [sys.executable, str(script), str(session), '--brains', str(brains)]
            matched = subprocess.run(args, capture_output=True, text=True)
            self.assertEqual(matched.returncode, 0, matched.stderr)
            self.assertIn('not source authentication', matched.stdout)
            (session / 'round-1.md').write_text('"This unsupported fixture statement never appeared in selected source materials" (S001)')
            self.assertEqual(subprocess.run(args, capture_output=True).returncode, 1)
            self.assertNotEqual(subprocess.run(args[:-1] + [str(base / 'missing')], capture_output=True).returncode, 0)


if __name__ == '__main__':
    unittest.main()
