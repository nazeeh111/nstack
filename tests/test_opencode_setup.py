import importlib.util, pathlib, tempfile, unittest
P = pathlib.Path
ROOT = P(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('opencode_setup', ROOT / 'opencode_setup.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class OpenCodeSetupTests(unittest.TestCase):
    def fixture(self, base):
        home, state = base / 'home', base / 'state'
        (home / '.codex').mkdir(parents=True)
        (home / '.codex/AGENTS.md').write_text('User policy\n')
        (home / '.agents/skills').mkdir(parents=True)
        cli = base / 'opencode'; cli.write_text('#!/bin/sh\necho "opencode v2.2.6"\n'); cli.chmod(0o755)
        return home, state, cli

    def test_shared_files_repeat_and_rollback_preserve_later_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            home, state, cli = self.fixture(P(tmp).resolve())
            result = m.apply(home, state, cli)
            journal = P(result['run']) / 'journal.json'; before = journal.read_bytes()
            self.assertFalse(m.apply(home, state, cli)['changed']); self.assertEqual(before, journal.read_bytes())
            self.assertEqual((home / '.config/opencode/AGENTS.md').resolve(), home / '.codex/AGENTS.md')
            (home / 'artifact.md').write_text('Keep me\n')
            m.rollback(result['run'])
            self.assertFalse((home / '.local/bin/opencode').exists())
            self.assertFalse((home / '.config/opencode/opencode.json').exists())
            self.assertEqual((home / 'artifact.md').read_text(), 'Keep me\n')
            self.assertEqual((home / '.codex/AGENTS.md').read_text(), 'User policy\n')

    def test_existing_config_refused_before_any_profile_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            home, state, cli = self.fixture(P(tmp).resolve())
            config = home / '.config/opencode/opencode.jsonc'; config.parent.mkdir(parents=True)
            config.write_text('{"unrelated":"preserve"}')
            with self.assertRaisesRegex(ValueError, 'JSONC'): m.apply(home, state, cli)
            self.assertEqual(config.read_text(), '{"unrelated":"preserve"}')
            self.assertFalse(state.exists()); self.assertFalse((config.parent / 'AGENTS.md').exists())

    def test_later_config_edit_blocks_rollback_without_data_loss(self):
        with tempfile.TemporaryDirectory() as tmp:
            home, state, cli = self.fixture(P(tmp).resolve()); result = m.apply(home, state, cli)
            config = home / '.config/opencode/opencode.json'; config.write_text('later user bytes\n')
            with self.assertRaises(ValueError): m.rollback(result['run'])
            self.assertEqual(config.read_text(), 'later user bytes\n')

if __name__ == '__main__': unittest.main()
