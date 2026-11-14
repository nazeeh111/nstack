"""Controller prose ports preserve source metadata as a complete YAML unit."""
import json
import pathlib
import re
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'lib')]
from patch_native34 import front, materialize, native_text
from patch_pstack import entry_policy


class NativeFrontmatter(unittest.TestCase):
    def test_pstack_methods_are_available_to_automatic_selection_without_changing_the_body(self):
        original = ('---\nname: pstack-method\ndescription: Scoped concurrency design\n'
                    'disable-model-invocation: true\nmetadata:\n  retained: yes\n---\n'
                    '\nApply when several writers can update the same state.\n')
        active = entry_policy(original)
        self.assertEqual(active.split('\n---\n', 1)[1], original.split('\n---\n', 1)[1])
        self.assertIn('metadata:\n  retained: yes\n', active)
        self.assertNotIn('disable-model-invocation:', active)
        import claude_setup
        derived, removed, manual = claude_setup.adapt_entry(active.encode(), 'pstack-shared-state')
        self.assertFalse(manual)
        self.assertEqual(derived.decode().split('\n---\n', 1)[1], active.split('\n---\n', 1)[1])
        with self.assertRaisesRegex(ValueError, 'policy changed'):
            entry_policy(original.replace('disable-model-invocation: true', 'disable-model-invocation: false'))

    def test_prose_bindings_do_not_rewrite_metadata_values(self):
        header = ('---\nname: source-name\ndescription: Source description\n'
                  'model: opus\nmetadata:\n  invocation: claude -p task\n'
                  'allowed-tools: [AskUserQuestion, Read]\n---\n')
        body = '\nClaude Code uses AskUserQuestion.\n'
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            active = native_text(header + body, 'P021', root / 'SKILL.md', root)
        self.assertTrue(active.startswith(header))
        self.assertNotIn('Claude Code', active[len(header):])
        self.assertNotIn('AskUserQuestion', active[len(header):])
        self.assertEqual(front(active, 'native-name').split('\n---\n', 1)[0],
                         header.rstrip('\n').rsplit('\n---', 1)[0].replace('name: source-name', 'name: native-name'))

    def test_pinned_office_hours_retains_complete_gbrain_mapping(self):
        registry = json.loads((ROOT / 'registry/manifest.json').read_text())
        spec = next(s for s in registry['skills']
                    if s['candidate_id'] == 'P006' and s['source_path'] == 'office-hours/SKILL.md')
        source = (pathlib.Path.home() / 'Library/Application Support/nstack/sources'
                  / spec['source_repository'].replace('/', '--') / spec['revision'])
        if not (source / '.nstack-source.json').is_file():
            self.skipTest('Pinned offline source absent; no acquisition')
        original = (source / spec['source_path']).read_text()
        header = original.split('\n---\n', 1)[0]
        self.assertIn('\ngbrain:\n  schema: 1\n', header)
        component = next(c for c in registry['components'] if c['id'] == 'P006')
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp)
            entry = materialize(source, out, spec, component)
            active = (out / entry / 'SKILL.md').read_text()
        native_name = spec.get('native_name') or pathlib.Path(spec['source_path']).parent.name
        expected = re.sub(r'(?m)^name:.*$', 'name: p006-' + native_name, header, count=1)
        self.assertEqual(active.split('\n---\n', 1)[0], expected)


if __name__ == '__main__':
    unittest.main()
