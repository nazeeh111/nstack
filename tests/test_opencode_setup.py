import importlib.util, json, pathlib, tempfile, unittest
import subprocess, sys
from unittest import mock
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

    def test_native_codex_addition_repeats_and_restores_existing_adapter(self):
        with tempfile.TemporaryDirectory() as tmp:
            home, state, cli = self.fixture(P(tmp).resolve()); m.apply(home, state, cli)
            config = home / '.config/opencode/opencode.json'; before = config.read_bytes()
            parent = (state / 'rollback.sh').resolve()
            codex = home.parent / 'codex'; codex.write_text('#!/bin/sh\necho "codex-cli 0.167.0"\n'); codex.chmod(0o755)
            result = m.apply(home, state, cli, codex)
            added = json.loads(config.read_text())
            self.assertNotIn('model', added); self.assertNotIn('providers', added)
            self.assertEqual(added['plugins'][0]['options'], {'codex': str(codex)})
            plugin = home / '.config/opencode/plugins/nstack-codex'
            self.assertTrue((plugin / 'gui-experimental.cjs').is_file())
            journal = P(result['run']) / 'journal.json'; saved = journal.read_bytes()
            self.assertFalse(m.apply(home, state, cli, codex)['changed']); self.assertEqual(journal.read_bytes(), saved)
            m.rollback(result['run'])
            self.assertEqual(config.read_bytes(), before); self.assertEqual((state / 'rollback.sh').resolve(), parent)
            self.assertFalse((plugin / 'package.json').exists()); self.assertFalse((plugin / 'gui-experimental.cjs').exists())

    def test_codex_upgrade_refuses_unowned_config_and_plugin_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            home, state, cli = self.fixture(P(tmp).resolve()); m.apply(home, state, cli)
            codex = home.parent / 'codex'; codex.write_text('#!/bin/sh\necho "codex-cli 0.167.0"\n'); codex.chmod(0o755)
            config = home / '.config/opencode/opencode.json'; before = config.read_bytes()
            config.write_text('{"model":"user-choice"}\n')
            with self.assertRaisesRegex(ValueError, 'preserved'): m.apply(home, state, cli, codex)
            self.assertEqual(config.read_text(), '{"model":"user-choice"}\n')
            config.write_bytes(before)
            plugin = home / '.config/opencode/plugins/nstack-codex/package.json'; plugin.parent.mkdir(parents=True)
            plugin.write_text('unowned plugin bytes\n')
            with self.assertRaisesRegex(ValueError, 'preserved'): m.apply(home, state, cli, codex)
            self.assertEqual(plugin.read_text(), 'unowned plugin bytes\n'); self.assertEqual(config.read_bytes(), before)

    def test_durable_adapter_repeat_retains_its_actual_launcher_dependency(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = P(tmp).resolve(); home, state, cli = self.fixture(base)
            codex = base / 'codex'; codex.write_text('#!/bin/sh\necho "codex-cli 0.167.0"\n'); codex.chmod(0o755)
            result = m.apply(home, state, cli, codex)
            code = m.profile_install.stage(state)
            self.assertEqual((code / 'integrations/opencode-codex/gui-experimental.cjs').read_bytes(),
                             (ROOT / 'integrations/opencode-codex/gui-experimental.cjs').read_bytes())
            journal = P(result['run']) / 'journal.json'; before = journal.read_bytes()
            run = subprocess.run([sys.executable, str(code / 'opencode_setup.py'), 'install',
                                  '--home', str(home), '--state', str(state), '--cli', str(cli),
                                  '--codex-harness', str(codex)], cwd=base, capture_output=True,
                                 text=True, check=True)
            self.assertFalse(json.loads(run.stdout)['changed'])
            self.assertEqual(journal.read_bytes(), before)

    def test_user_security_rules_survive_repeat_and_launcher_upgrade(self):
        with tempfile.TemporaryDirectory() as tmp:
            home, state, cli = self.fixture(P(tmp).resolve()); first = m.apply(home, state, cli)
            config = home / '.config/opencode/opencode.json'
            security = {'permissions': [{'action': 'shell', 'resource': '*', 'effect': 'ask'}],
                        'policies': [{'action': 'tool.use', 'resource': 'read:/private/fixture/*', 'effect': 'deny'}]}
            data = json.loads(config.read_text()); data.update(security)
            raw = json.dumps(data, separators=(',', ':')).encode() + b'\n\n'
            config.write_bytes(raw)
            journal = P(first['run']) / 'journal.json'; before = journal.read_bytes()
            self.assertFalse(m.apply(home, state, cli)['changed'])
            self.assertEqual(config.read_bytes(), raw); self.assertEqual(journal.read_bytes(), before)
            codex = home.parent / 'codex'; codex.write_text('#!/bin/sh\necho "codex-cli 0.167.0"\n'); codex.chmod(0o755)
            result = m.apply(home, state, cli, codex)
            added = json.loads(config.read_text())
            for key, value in security.items(): self.assertEqual(added[key], value)
            upgraded = config.read_bytes(); journal = P(result['run']) / 'journal.json'; before = journal.read_bytes()
            self.assertFalse(m.apply(home, state, cli, codex)['changed'])
            self.assertEqual(config.read_bytes(), upgraded); self.assertEqual(journal.read_bytes(), before)
            m.rollback(result['run']); self.assertEqual(config.read_bytes(), raw)

    def test_security_extras_do_not_allow_owned_conflicts_or_providers(self):
        with tempfile.TemporaryDirectory() as tmp:
            home, state, cli = self.fixture(P(tmp).resolve()); first = m.apply(home, state, cli)
            config = home / '.config/opencode/opencode.json'; original = json.loads(config.read_text())
            journal = P(first['run']) / 'journal.json'; before = journal.read_bytes()
            for conflict in [{'warming': True}, {'providers': {'fixture': {'settings': {'apiKey': 'synthetic-only'}}}},
                             {'unowned': True}]:
                data = {**original, 'permissions': [], **conflict}; raw = json.dumps(data).encode(); config.write_bytes(raw)
                with self.assertRaisesRegex(ValueError, 'preserved'): m.apply(home, state, cli)
                self.assertEqual(config.read_bytes(), raw); self.assertEqual(journal.read_bytes(), before)

    def test_concurrent_security_edit_refused_before_upgrade_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            home, state, cli = self.fixture(P(tmp).resolve()); first = m.apply(home, state, cli)
            config = home / '.config/opencode/opencode.json'
            data = json.loads(config.read_text()); data['permissions'] = []
            config.write_text(json.dumps(data)); parent = (state / 'rollback.sh').resolve()
            journal = P(first['run']) / 'journal.json'; before = journal.read_bytes()
            codex = home.parent / 'codex'; codex.write_text('#!/bin/sh\necho "codex-cli 0.167.0"\n'); codex.chmod(0o755)
            original_plan = m.plan; calls = 0
            changed = {**data, 'permissions': [{'action': 'shell', 'resource': '*', 'effect': 'ask'}]}
            concurrent = json.dumps(changed).encode() + b'\n'
            def competing_plan(*args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 2: config.write_bytes(concurrent)
                return original_plan(*args, **kwargs)
            with mock.patch.object(m, 'plan', side_effect=competing_plan):
                with self.assertRaisesRegex(ValueError, 'changed during preparation'):
                    m.apply(home, state, cli, codex)
            self.assertEqual(config.read_bytes(), concurrent)
            self.assertEqual((state / 'rollback.sh').resolve(), parent)
            self.assertEqual(journal.read_bytes(), before)
            self.assertFalse((home / '.config/opencode/plugins/nstack-codex').exists())

if __name__ == '__main__': unittest.main()
