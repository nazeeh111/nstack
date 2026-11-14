"""Claude host adapter: isolated payloads, real transactions and denied controls."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'lib')]
import claude_setup as claude
import native_setup as native
from transaction import fingerprint


class ClaudeSetup(unittest.TestCase):
    def setUp(self):
        saved = native.nstack.STATE
        self.addCleanup(setattr, native.nstack, 'STATE', saved)

    def args(self, home, state, **extra):
        return argparse.Namespace(home=str(home), state=str(state), only=['obsidian-markdown'], vault=None, **extra)

    def fixture(self, base, body=None):
        source = base / 'source'
        entry = source / 'skills/entry'
        entry.mkdir(parents=True)
        text = body or ('---\nname: fixture\ndescription:\n  Plain multiline description\n  with useful methods\n'
                        'allowed-tools:\n  - Bash(*)\nmodel: force-other-model\nhooks:\n  PreToolUse: []\n'
                        'context: fork\nagent: privileged\nlicense: MIT\n---\n'
                        'Read [complete support](../../support.md).\n')
        (entry / 'SKILL.md').write_text(text)
        (entry / 'references').mkdir()
        (entry / 'references/details.md').write_text('Complete retained reference.\n')
        (source / 'support.md').write_text('Support outside exposed entry remains relative.\n')
        (source / 'LICENSE').write_text('MIT fixture\n')
        leaf = next(spec for name, spec in native.selection() if name == 'obsidian-markdown')
        receipt = {'content_sha256': 'fixture', 'builder_sha256': 'fixture', 'entry_dir': 'skills/entry',
                   'files': {str(path.relative_to(source)): native.sha(path.read_bytes())
                             for path in source.rglob('*') if path.is_file()}}
        (source / '.nstack-release.json').write_text(json.dumps(receipt, sort_keys=True, indent=2, ensure_ascii=False) + '\n')
        return source, leaf, receipt

    def source_patches(self, source, leaf, receipt):
        return (patch.object(native.nstack, 'build', return_value=source),
                patch.object(native.nstack, 'registered_release', return_value=(receipt, {}, leaf)))

    def test_complete_payload_is_derived_without_native_mutation_and_self_seal_cannot_hide_tamper(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            source, leaf, receipt = self.fixture(base)
            p1, p2 = self.source_patches(source, leaf, receipt)
            with p1, p2:
                baseline, _ = native.prepare(base / 'state', [('obsidian-markdown', leaf)], [])
                before = fingerprint(baseline)
                release, rows = claude.prepare(base / 'state', [('obsidian-markdown', leaf)], [])
                self.assertEqual(fingerprint(baseline), before)
                entry = Path(rows[0]['skill_path'])
                content = entry.read_text()
                self.assertIn('name: "obsidian-markdown"', content)
                self.assertIn('license: MIT', content)
                for field in ('allowed-tools:', 'model:', 'hooks:', 'context:', 'agent:'):
                    self.assertNotIn(field, content)
                self.assertEqual((entry.parent / '../../support.md').resolve().read_bytes(), (source / 'support.md').read_bytes())
                self.assertEqual((entry.parent / 'references/details.md').read_text(), 'Complete retained reference.\n')
                self.assertEqual((release / 'originals/obsidian-markdown/SKILL.md').read_bytes(),
                                 (baseline / 'bundles/obsidian-markdown/skills/entry/SKILL.md').read_bytes())
                self.assertEqual(claude.prepare(base / 'state', [('obsidian-markdown', leaf)], [])[0], release)
                entry.chmod(0o644)
                entry.write_text(content + 'unreviewed change\n')
                entry.chmod(0o444)
                seal = release / 'NATIVE-MANIFEST.json'
                saved = json.loads(seal.read_text())
                saved['files'] = native.tree(release)
                seal.chmod(0o600)
                seal.write_text(json.dumps(saved))
                seal.chmod(0o444)
                with self.assertRaisesRegex(ValueError, 'Claude release changed'):
                    claude.prepare(base / 'state', [('obsidian-markdown', leaf)], [])

    def test_manual_policy_and_shell_injection_are_host_native(self):
        for name in ('01', 'pstack-blast-radius', 'untangle-codebase'):
            raw = ('---\nname: original\ndescription: useful methods\n' +
                   ('' if name == '01' else 'disable-model-invocation: true\n') + '---\nMethod body.\n').encode()
            adapted, _, manual = claude.adapt_entry(raw, name)
            self.assertTrue(manual)
            self.assertIn(b'disable-model-invocation: true\n', adapted)
            self.assertTrue(adapted.endswith(b'Method body.\n'))
        for body in ('!`touch something`', '```!\ntouch something\n```'):
            with self.assertRaisesRegex(ValueError, 'shell injection'):
                claude.adapt_entry(('---\nname: test\ndescription: test\n---\n' + body).encode(), 'test')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            claude.adapt_entry(b'---\nname: x\ndescription: x\nmodel: x\nmodel: y\n---\n', 'test')

    def test_actual_dirty_bytes_repeat_noop_and_saved_terminal_rollback(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            home, state = base / 'home', base / 'state'
            home.mkdir()
            own = home / '.claude/skills/my-own'
            own.mkdir(parents=True)
            (own / 'SKILL.md').write_text('Unrelated dirty user skill.\n')
            agents = home / '.claude/CLAUDE.md'
            agents.write_text('Personal instructions and exact dirty bytes.\n')
            agents.chmod(0o640)
            original, own_before = fingerprint(agents), fingerprint(own)
            source, leaf, receipt = self.fixture(base)
            p1, p2 = self.source_patches(source, leaf, receipt)
            with p1, p2:
                result = claude.apply(self.args(home, state, adaptive_routing=True))
                self.assertEqual(result['skills'], 2)
                self.assertEqual(fingerprint(own), own_before)
                self.assertIn(b'disable-model-invocation: true', (home / '.claude/skills/01/SKILL.md').read_bytes())
                journal = Path(result['run']) / 'journal.json'
                before = journal.read_bytes()
                self.assertFalse(claude.apply(self.args(home, state, adaptive_routing=True))['changed'])
                self.assertEqual(journal.read_bytes(), before)
            (home / 'new-note.md').write_text('Useful new work.\n')
            subprocess.run([str(state / 'rollback.sh')], check=True, capture_output=True)
            self.assertEqual(fingerprint(agents), original)
            self.assertEqual(fingerprint(own), own_before)
            self.assertFalse((home / '.claude/skills/obsidian-markdown').exists())
            self.assertFalse((state / 'claude-profile.json').exists())
            self.assertEqual((home / 'new-note.md').read_text(), 'Useful new work.\n')

    def test_collision_linked_parent_and_managed_edit_are_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            home, state = base / 'home', base / 'state'
            home.mkdir()
            source, leaf, receipt = self.fixture(base)
            p1, p2 = self.source_patches(source, leaf, receipt)
            with p1, p2:
                collision = home / '.claude/skills/obsidian-markdown'
                collision.mkdir(parents=True)
                (collision / 'SKILL.md').write_text('Original unowned bytes.\n')
                before = fingerprint(collision)
                with self.assertRaisesRegex(ValueError, 'collision'):
                    claude.apply(self.args(home, state))
                self.assertEqual(fingerprint(collision), before)
                # Remove only this disposable test fixture to continue controls.
                (collision / 'SKILL.md').unlink()
                collision.rmdir()
                result = claude.apply(self.args(home, state))
                agents = home / '.claude/CLAUDE.md'
                agents.write_text(agents.read_text().replace('## nstack for Claude Code', '## User-changed block'))
                changed = fingerprint(agents)
                profile_before = fingerprint(state / 'claude-profile.json')
                with self.assertRaisesRegex(ValueError, 'changed nstack'):
                    claude.apply(self.args(home, state))
                with self.assertRaisesRegex(ValueError, 'rollback conflict'):
                    claude.rollback(result['run'])
                self.assertEqual(fingerprint(agents), changed)
                self.assertEqual(fingerprint(state / 'claude-profile.json'), profile_before)
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            home, state, elsewhere = base / 'home', base / 'state', base / 'elsewhere'
            home.mkdir()
            elsewhere.mkdir()
            (home / '.claude').symlink_to(elsewhere)
            source, leaf, receipt = self.fixture(base)
            p1, p2 = self.source_patches(source, leaf, receipt)
            with p1, p2, self.assertRaisesRegex(ValueError, 'Linked profile target parent'):
                claude.apply(self.args(home, state))
            self.assertEqual(list(elsewhere.iterdir()), [])

    def test_update_retires_only_owned_links_and_chain_restores_previous_generation(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            home, state = base / 'home', base / 'state'
            home.mkdir()
            source, leaf, receipt = self.fixture(base)
            p1, p2 = self.source_patches(source, leaf, receipt)
            with p1, p2:
                first = claude.apply(self.args(home, state, adaptive_routing=True))
                first_profile = fingerprint(state / 'claude-profile.json')
                second = claude.apply(self.args(home, state))
                self.assertFalse((home / '.claude/skills/01').exists())
                claude.rollback(second['run'])
                self.assertTrue((home / '.claude/skills/01').is_symlink())
                self.assertEqual(fingerprint(state / 'claude-profile.json'), first_profile)
                claude.rollback(first['run'])
                self.assertFalse((home / '.claude/CLAUDE.md').exists())

    def test_interruption_has_recovery_before_first_mutation_and_concurrent_edit_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            home, state = base / 'home', base / 'state'
            home.mkdir()
            source, leaf, receipt = self.fixture(base)
            p1, p2 = self.source_patches(source, leaf, receipt)
            with p1, p2, patch.object(claude.Transaction, 'replace_file', side_effect=RuntimeError('interrupted')):
                with self.assertRaisesRegex(RuntimeError, 'interrupted'):
                    claude.apply(self.args(home, state))
            self.assertTrue((state / 'rollback.sh').is_symlink())
            subprocess.run([str(state / 'rollback.sh')], check=True, capture_output=True)
            self.assertFalse((home / '.claude/skills/obsidian-markdown').exists())
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            home, state = base / 'home', base / 'state'
            home.mkdir()
            source, leaf, receipt = self.fixture(base)
            p1, p2 = self.source_patches(source, leaf, receipt)
            original_plan = claude.plan
            calls = []
            def concurrent(*args):
                if calls:
                    agents = home / '.claude/CLAUDE.md'
                    agents.parent.mkdir(exist_ok=True)
                    agents.write_text('Concurrent human edit.\n')
                calls.append(True)
                return original_plan(*args)
            with p1, p2, patch.object(claude, 'plan', side_effect=concurrent):
                with self.assertRaisesRegex(ValueError, 'Concurrent'):
                    claude.apply(self.args(home, state))
            self.assertEqual((home / '.claude/CLAUDE.md').read_text(), 'Concurrent human edit.\n')
            self.assertFalse((home / '.claude/skills/obsidian-markdown').exists())
            self.assertFalse((state / 'rollback.sh').exists())

    def test_custom_config_env_dirty_restore_repeat_and_no_silent_move(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            home, state, custom = base / 'home', base / 'state', base / 'custom-claude'
            home.mkdir(); custom.mkdir()
            default = home / '.claude/CLAUDE.md'
            default.parent.mkdir()
            default.write_text('Untouched default configuration.\n')
            default_before = fingerprint(default)
            agents = custom / 'CLAUDE.md'
            agents.write_text('Dirty custom user instructions.\n')
            agents.chmod(0o640)
            old = fingerprint(agents)
            source, leaf, receipt = self.fixture(base)
            p1, p2 = self.source_patches(source, leaf, receipt)
            with p1, p2, patch.object(Path, 'home', return_value=home), patch.dict(os.environ, {'CLAUDE_CONFIG_DIR': str(custom)}):
                result = claude.apply(self.args(home, state))
                self.assertTrue((custom / 'skills/obsidian-markdown').is_symlink())
                self.assertEqual(result['claude_home'], str(custom))
                self.assertEqual(json.loads((state / 'claude-profile.json').read_text())['claude_home'], str(custom))
                self.assertFalse(claude.apply(self.args(home, state))['changed'])
                self.assertEqual(fingerprint(default), default_before)
                self.assertFalse((home / '.claude/skills').exists())
                other = base / 'other-config'
                with self.assertRaisesRegex(ValueError, 'another configuration directory'):
                    claude.apply(self.args(home, state, claude_home=str(other)))
                self.assertFalse(other.exists())
            subprocess.run([str(state / 'rollback.sh')], check=True, capture_output=True)
            self.assertEqual(fingerprint(agents), old)
            self.assertEqual(fingerprint(default), default_before)
            self.assertFalse((custom / 'skills/obsidian-markdown').exists())

    def test_config_override_precedence_and_foreign_home_ignores_process_env(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            home, current = base / 'other-home', base / 'current-home'
            explicit, environment = base / 'explicit', base / 'environment'
            with patch.object(Path, 'home', return_value=current), patch.dict(os.environ, {'CLAUDE_CONFIG_DIR': str(environment)}):
                self.assertEqual(claude.claude_directory(home), home / '.claude')
                self.assertEqual(claude.claude_directory(current), environment)
                self.assertEqual(claude.claude_directory(current, str(explicit)), explicit)


if __name__ == '__main__':
    unittest.main()
