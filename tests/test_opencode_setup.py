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

    def test_opted_in_vault_writes_preserve_denials_readonly_roles_and_repeat(self):
        with tempfile.TemporaryDirectory() as tmp:
            home, state, cli = self.fixture(P(tmp).resolve())
            vault = home / 'Knowledge'; vault.mkdir()
            note = vault / 'Home.md'; note.write_text('Preserve this note\n')
            denied = {'action': 'edit', 'resource': str(vault / 'private') + '/*', 'effect': 'deny'}
            plan = {'permissions': [{'action': 'edit', 'resource': '*', 'effect': 'deny'}]}
            data = {'permissions': [denied], 'agents': {'plan': plan, 'explore': {'permissions': [{'action': 'edit', 'resource': '*', 'effect': 'deny'}]}}}
            actual = m.knowledge_permissions(data, home, vault, 'allow')
            guards = [{'action': 'edit', 'resource': str(vault / folder) + suffix, 'effect': 'deny'}
                      for folder in ('.git', '.obsidian') for suffix in ('', '/*')]
            self.assertEqual(actual['agents']['plan'], plan)
            self.assertEqual(actual['agents']['explore'], data['agents']['explore'])
            for role in ('build', 'general'):
                rules = actual['agents'][role]['permissions']
                self.assertEqual(rules, [{'action': 'edit', 'resource': str(vault) + '/*', 'effect': 'allow'}, denied, *guards])
            self.assertEqual(m.knowledge_permissions(actual, home, vault), actual)
            prompted = m.knowledge_permissions(actual, home, vault, 'ask')
            for role in ('build', 'general'):
                self.assertEqual(prompted['agents'][role]['permissions'],
                                 [{'action': 'edit', 'resource': str(vault) + '/*', 'effect': 'ask'}, denied, *guards])
            self.assertEqual(m.knowledge_permissions(prompted, home, vault), prompted)
            self.assertEqual(m.knowledge_permissions(prompted, home, vault, 'allow'), actual)
            # A pre-existing scoped metadata allow cannot override the guards.
            scoped = {'action': 'edit', 'resource': str(vault / '.git/config'), 'effect': 'allow'}
            custom = {**data, 'agents': {**data['agents'], 'build': {'permissions': [guards[0], scoped, guards[0]]}}}
            protected = m.knowledge_permissions(custom, home, vault, 'allow')
            rules = protected['agents']['build']['permissions']
            self.assertEqual(rules[-4:], guards)
            self.assertEqual(rules.count(guards[0]), 1)
            self.assertLess(rules.index(scoped), rules.index(guards[0]))
            self.assertEqual(m.knowledge_permissions(protected, home, vault), protected)
            with self.assertRaisesRegex(ValueError, 'denial'):
                m.knowledge_permissions({'permissions': [{'action': 'edit', 'resource': str(vault) + '/*', 'effect': 'deny'}]}, home, vault, 'allow')
            agent_denial = {'agents': {'build': {'permissions': [
                {'action': 'edit', 'resource': str(vault) + '/*', 'effect': 'deny'}]}}}
            before_denial = json.dumps(agent_denial)
            with self.assertRaisesRegex(ValueError, 'denial'):
                m.knowledge_permissions(agent_denial, home, vault, 'allow')
            self.assertEqual(json.dumps(agent_denial), before_denial)
            with self.assertRaisesRegex(ValueError, 'explicit vault'):
                m.plan(home, state, cli, vault_write='allow')
            m.apply(home, state, cli)
            path = home / '.config/opencode/opencode.json'
            installed = json.loads(path.read_text()); installed.update(data)
            original = json.dumps(installed, indent=2) + '\n'; path.write_text(original)
            result = m.apply(home, state, cli, vault=vault, vault_write='allow')
            actual = json.loads(path.read_text())
            self.assertEqual(actual['agents']['build']['permissions'][0]['effect'], 'allow')
            self.assertEqual(actual['agents']['plan'], plan)
            self.assertEqual(actual['agents']['explore'], data['agents']['explore'])
            self.assertEqual(actual['permissions'], m.knowledge_permissions(data, home, vault, 'allow')['permissions'])
            for role in ('build', 'general'):
                self.assertEqual(actual['agents'][role]['permissions'][-4:], guards)
            raw = path.read_bytes(); journal = P(result['run']) / 'journal.json'; receipt = journal.read_bytes()
            self.assertFalse(m.apply(home, state, cli, vault=vault)['changed'])
            self.assertEqual(path.read_bytes(), raw); self.assertEqual(journal.read_bytes(), receipt)
            m.rollback(result['run']); self.assertEqual(path.read_text(), original)
            self.assertEqual(note.read_text(), 'Preserve this note\n')

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


    def test_explicit_knowledge_scope_preserves_other_policy_and_undo(self):
        with tempfile.TemporaryDirectory() as tmp:
            home,state,cli=self.fixture(P(tmp).resolve()); m.apply(home,state,cli)
            vault=home/'Knowledge';vault.mkdir();(vault/'Home.md').write_text('canonical')
            config=home/'.config/opencode/opencode.json';data=json.loads(config.read_text())
            data['permissions']=[{'action':'shell','resource':'*','effect':'ask'},{'action':'external_directory','resource':'*','effect':'ask'}]
            data['policies']=[{'action':'tool.use','resource':'read:'+str(home/'.ssh/*'),'effect':'deny'}]
            before=json.dumps(data,indent=2)+'\n';config.write_text(before)
            result=m.apply(home,state,cli,vault=vault);actual=json.loads(config.read_text())
            self.assertEqual(actual['policies'],data['policies']);self.assertEqual(actual['permissions'][:2],data['permissions'])
            self.assertEqual(actual['permissions'][2:], [{'action':'external_directory','resource':str(vault)+'/*','effect':'allow'}])
            for role in ['build','general']:self.assertEqual(actual['agents'][role]['permissions'],[{'action':'edit','resource':str(vault)+'/*','effect':'ask'}])
            self.assertNotIn('explore',actual['agents']);self.assertNotIn('plan',actual['agents'])
            self.assertNotIn('model',actual);self.assertNotIn('providers',actual)
            journal=(P(result['run'])/'journal.json').read_bytes();raw=config.read_bytes()
            self.assertFalse(m.apply(home,state,cli,vault=vault)['changed']);self.assertEqual(raw,config.read_bytes());self.assertEqual(journal,(P(result['run'])/'journal.json').read_bytes())
            m.rollback(result['run']);self.assertEqual(config.read_text(),before);self.assertEqual((vault/'Home.md').read_text(),'canonical')
            denied={**data,'permissions':[{'action':'external_directory','resource':str(vault)+'/*','effect':'deny'}]}
            with self.assertRaisesRegex(ValueError,'denial'):m.knowledge_permissions(denied,home,vault)
            with self.assertRaises(ValueError):m.knowledge_permissions(data,home,home)
            private={'action':'external_directory','resource':str(vault/'private')+'/*','effect':'deny'}
            narrowed=m.knowledge_permissions({**data,'permissions':data['permissions']+[private]},home,vault)
            self.assertEqual(narrowed['permissions'][-1],private)
            for action,resource in [('edit','*'),('*','*'),('external_directory','~/Knowledge/*'),('external_directory','$HOME/Knowledge/*'),('e*',str(vault)+'/*')]:
                with self.assertRaisesRegex(ValueError,'denial'):m.knowledge_permissions({**data,'permissions':[{'action':action,'resource':resource,'effect':'deny'}]},home,vault)
            for private_name in ['.kube','.gnupg','.azure','.docker']:
                folder=home/private_name;folder.mkdir()
                with self.assertRaises(ValueError):m.knowledge_permissions(data,home,folder)

    def test_vault_edit_prompts_preserve_global_narrow_denials_and_agent_precedence(self):
        with tempfile.TemporaryDirectory() as tmp:
            home, state, cli = self.fixture(P(tmp).resolve())
            vault = home / 'Knowledge'; vault.mkdir()
            # Neither narrow denial covers Home.md. The second uses native
            # action/resource wildcards and home expansion.
            denials = [
                {'action': 'edit', 'resource': str(vault / 'private') + '/*', 'effect': 'deny'},
                {'action': 'e*', 'resource': '$HOME/Knowledge/*/sealed/*', 'effect': 'deny'},
            ]
            config = {'permissions': [
                {'action': 'external_directory', 'resource': '*', 'effect': 'ask'}, *denials,
            ]}
            actual = m.knowledge_permissions(config, home, vault)
            ask = {'action': 'edit', 'resource': str(vault) + '/*', 'effect': 'ask'}
            for role in ('build', 'general'):
                self.assertEqual(actual['agents'][role]['permissions'], [ask, *denials])
            grant = {'action': 'external_directory', 'resource': str(vault) + '/*', 'effect': 'allow'}
            self.assertEqual([rule for rule in actual['permissions'] if rule != grant], config['permissions'])
            self.assertEqual(m.knowledge_permissions(actual, home, vault), actual)
            # Existing agent rules keep their original ordering and precedence.
            existing = {'action': 'edit', 'resource': str(vault / 'private/reviewed') + '/*', 'effect': 'allow'}
            custom = {**config, 'agents': {'build': {'permissions': [denials[0], existing]}}}
            merged = m.knowledge_permissions(custom, home, vault)
            rules = merged['agents']['build']['permissions']
            self.assertEqual(rules[-2:], [denials[0], existing])
            self.assertEqual(rules.count(denials[0]), 1)
            self.assertEqual(m.knowledge_permissions(merged, home, vault), merged)
            m.apply(home, state, cli)
            path = home / '.config/opencode/opencode.json'
            data = json.loads(path.read_text()); data.update(config)
            path.write_text(json.dumps(data))
            installed = m.apply(home, state, cli, vault=vault)
            raw = path.read_bytes(); journal = P(installed['run']) / 'journal.json'
            receipt = journal.read_bytes()
            self.assertFalse(m.apply(home, state, cli, vault=vault)['changed'])
            self.assertEqual(path.read_bytes(), raw)
            self.assertEqual(journal.read_bytes(), receipt)

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
