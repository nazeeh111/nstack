"""Offline recipe contracts. Fake scanner reports are fixtures, not NVIDIA scan evidence."""
import errno
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('skillspector_recipe', ROOT / 'recipes/skillspector.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def report(**changes):
    value = {'execution_successful': True, 'issues': [{'rule_id': 'AST1'}],
             'components': [{'path': 'SKILL.md', 'lines': 3}],
             'risk_assessment': {'score': 55, 'severity': 'HIGH', 'recommendation': 'DO_NOT_INSTALL'},
             'metadata': {'skillspector_version': m.VERSION, 'llm_requested': False, 'inference_usage': []},
             'analysis_completeness': {'is_complete': False, 'limitations': ['offline OSV']}}
    value.update(changes)
    return value


class SkillSpector(unittest.TestCase):
    def test_clean_environment_has_no_host_credentials_or_tracing(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'fake-private', 'LANGSMITH_API_KEY': 'fake-private',
                                     'SKILLSPECTOR_PROVIDER': 'openai', 'HTTPS_PROXY': 'fake-private',
                                     'SKILLSPECTOR_MODEL_REGISTRY': '/private/secret'}, clear=False):
            env = m.isolated_env('/empty-home', '/owned-temp')
        self.assertEqual(env['SKILLSPECTOR_OSV_TIMEOUT'], '0')
        self.assertEqual(env['LANGSMITH_TRACING'], 'false')
        self.assertEqual(env['HOME'], '/empty-home')
        self.assertFalse({'OPENAI_API_KEY', 'LANGSMITH_API_KEY', 'SKILLSPECTOR_PROVIDER',
                          'HTTPS_PROXY', 'SKILLSPECTOR_MODEL_REGISTRY'} & env.keys())
        self.assertNotIn('fake-private', json.dumps(env))

    def test_snapshot_resolves_root_preserves_bytes_modes_and_avoids_secrets(self):
        with tempfile.TemporaryDirectory(dir='/private/tmp') as directory:
            base = Path(directory); source = base / 'source'; source.mkdir()
            (source / 'SKILL.md').write_text('data only')
            (source / 'script').write_text('#!/bin/sh\nexit 1'); (source / 'script').chmod(0o755)
            (source / '.env').write_text('fixture-secret-never-copy')
            (source / '.env.example').write_text('KEY=example')
            (source / '.git').mkdir(); (source / '.git/config').write_text('ignored')
            linked = base / 'linked'; linked.symlink_to(source)
            inv = m.snapshot(linked, base / 'snapshot')
            self.assertEqual(inv['resolved'], str(source))
            self.assertEqual(set(inv['files']), {'SKILL.md', 'script', '.env.example'})
            self.assertEqual((base / 'snapshot/script').read_bytes(), (source / 'script').read_bytes())
            self.assertTrue((base / 'snapshot/script').stat().st_mode & 0o111)
            self.assertIn('.env', inv['skipped']); self.assertIn('.git/', inv['skipped'])
            self.assertFalse((base / 'snapshot/.env').exists())

    def test_snapshot_rejects_nested_link_escape_and_nonregular_input(self):
        with tempfile.TemporaryDirectory(dir='/private/tmp') as directory:
            base = Path(directory); source = base / 'source'; source.mkdir()
            (base / 'outside').write_text('outside')
            (source / 'linked').symlink_to(base / 'outside')
            with self.assertRaisesRegex(ValueError, 'escapes'):
                m.snapshot(source, base / 'snapshot1')
            (source / 'linked').unlink(); os.mkfifo(source / 'pipe')
            with self.assertRaisesRegex(ValueError, 'non-regular'):
                m.snapshot(source, base / 'snapshot2')

    def test_snapshot_limits_reject_instead_of_claiming_complete(self):
        with tempfile.TemporaryDirectory(dir='/private/tmp') as directory:
            base = Path(directory); source = base / 'source'; source.mkdir(); (source / 'data').write_bytes(b'abc')
            with patch.object(m, 'MAX_BYTES', 2), self.assertRaisesRegex(ValueError, 'bound'):
                m.snapshot(source, base / 'snapshot')

    def test_scan_keeps_findings_and_actual_partial_coverage(self):
        summary = m.report_summary(report(), 1)
        self.assertEqual(summary['status'], 'scanned_requires_source_adjudication')
        self.assertEqual(summary['issues'], 1)
        self.assertFalse(summary['analysis_completeness']['is_complete'])
        self.assertEqual(summary['live_osv'], 'unavailable_offline')
        for broken, code in [(report(execution_successful=False), 0), (report(), 2),
                             (report(metadata={'skillspector_version': m.VERSION, 'llm_requested': True}), 0),
                             (report(metadata={'skillspector_version': m.VERSION, 'llm_requested': False, 'inference_usage': [{'tokens': 1}]}), 0),
                             (report(analysis_completeness={}), 0), (report(components=None), 0)]:
            with self.subTest(broken=broken, code=code), self.assertRaises(ValueError):
                m.report_summary(broken, code)

    def test_network_guard_is_required_and_never_silently_removed(self):
        with patch.object(m.platform, 'system', return_value='Linux'), patch.object(m, 'capture') as capture:
            with self.assertRaisesRegex(ValueError, 'no fallback'):
                m.network_guard(Path('/runtime'), Path('/work'), {})
            capture.assert_not_called()
        with patch.object(m.platform, 'system', return_value='Darwin'), \
             patch.object(m, 'capture', return_value=subprocess.CompletedProcess([], 0, '{"network_denied":false,"errno":61}', '')):
            with self.assertRaisesRegex(ValueError, 'probe failed'):
                m.network_guard(Path('/runtime'), Path('/work'), {})

    @unittest.skipUnless(platform.system() == 'Darwin' and Path('/usr/bin/sandbox-exec').is_file(), 'native macOS probe')
    def test_actual_mac_profile_denies_network_using_inert_python_only(self):
        with tempfile.TemporaryDirectory(dir='/private/tmp') as directory:
            work = Path(directory); root = work / 'runtime'; (root / '.venv/bin').mkdir(parents=True)
            (root / '.venv/bin/python').symlink_to(Path(sys.executable).resolve())
            home = work / 'home'; home.mkdir()
            prefix, proof = m.network_guard(root, work, m.isolated_env(home, work))
            self.assertEqual(prefix[0], '/usr/bin/sandbox-exec')
            self.assertTrue(proof['network_denied']); self.assertIn(proof['errno'], (errno.EPERM, errno.EACCES))

    def test_source_pin_hashes_and_original_skill_closure(self):
        addon = ROOT / 'addons/skillspector'; source = json.loads((addon / 'SOURCE.json').read_text())
        self.assertEqual(source['revision'], m.REVISION)
        for name, info in source['upstream_files'].items():
            self.assertEqual(m.digest(addon / name), info['sha256'])
        original = (addon / 'upstream/ORIGINAL-SKILL.md').read_text()
        active = (addon / 'SKILL.md').read_text()
        # All upstream sections and workflow steps remain, beyond metadata and a scoped insertion.
        marker_start = active.index('> Native adaptation,')
        marker_end = active.index('\n\n', marker_start)
        native_body = active[active.index('# Skill Inspector'):marker_start] + active[marker_end + 2:]
        self.assertEqual(native_body.rstrip(), original[original.index('# Skill Inspector'):].rstrip())
        self.assertEqual(hashlib.sha256((addon / 'upstream/ORIGINAL-SKILL.md').read_bytes()).hexdigest(),
                         '1acc220016936ba68f7b9083c19575a8866c9cf74c251d689285a0d9fbe2a067')

    def test_run_passes_only_real_static_cli_and_retains_raw_reports(self):
        with tempfile.TemporaryDirectory(dir='/private/tmp') as directory:
            base = Path(directory); target = base / 'target'; target.mkdir(); (target / 'SKILL.md').write_text('fixture')
            calls = []
            def backend(argv, cwd, env, stdout, stderr, timeout):
                calls.append((argv, env)); Path(stdout).write_text(json.dumps(report())); Path(stderr).write_text('fixture backend\n')
                return 1
            with patch.object(m, 'verify', return_value=Path('/trusted/skillspector')), \
                 patch.object(m, 'network_guard', return_value=(['/usr/bin/sandbox-exec', '-p', 'DENY'], {'network_denied': True, 'errno': errno.EPERM})), \
                 patch.object(m, 'execute', side_effect=backend):
                receipt = m.run(base / 'runtime', [target], base / 'output')
            argv, env = calls[0]
            self.assertEqual(argv[:4], ['/usr/bin/sandbox-exec', '-p', 'DENY', Path('/trusted/skillspector')])
            self.assertEqual(argv[-3:], ['--no-llm', '--format', 'json'])
            self.assertNotIn('--inspect-dependencies', argv); self.assertNotIn('--transitive', argv)
            self.assertEqual(receipt['status'], 'scanned_requires_source_adjudication')
            self.assertEqual(json.loads((base / 'output/component-0000/report.json').read_text())['issues'][0]['rule_id'], 'AST1')

    def test_denied_network_does_not_start_scanner_and_saves_failure(self):
        with tempfile.TemporaryDirectory(dir='/private/tmp') as directory:
            base = Path(directory); target = base / 'target'; target.mkdir()
            with patch.object(m, 'verify', return_value=Path('/trusted/skillspector')), \
                 patch.object(m, 'network_guard', side_effect=ValueError('denied by host')), \
                 patch.object(m, 'execute') as execute:
                with self.assertRaisesRegex(ValueError, 'denied by host'):
                    m.run(base / 'runtime', [target], base / 'output')
                execute.assert_not_called()
            self.assertEqual(json.loads((base / 'output/run.json').read_text())['status'], 'incomplete')

    def test_source_verification_rejects_wrong_pin_before_runtime_install(self):
        result = subprocess.CompletedProcess([], 0, 'wrong-pin\n', '')
        with patch.object(m, 'capture', return_value=result), self.assertRaisesRegex(ValueError, 'pin/tree'):
            m.source_inventory(Path('/unused'), '/usr/bin/git', {})


    def test_runtime_drift_is_detected_without_overwriting_bytes(self):
        with tempfile.TemporaryDirectory(dir='/private/tmp') as directory:
            root = Path(directory); (root / '.venv/bin').mkdir(parents=True)
            (root / '.venv/bin/python').symlink_to(Path(sys.executable).resolve())
            binary = root / '.venv/bin/skillspector'; binary.write_text('original fixture')
            receipt = {'revision': m.REVISION, 'tree': m.TREE, 'lock_sha256': m.LOCK_HASH,
                       'source_files': {}, 'runtime_files': m.runtime_inventory(root),
                       'interpreter_sha256': m.digest(Path(sys.executable).resolve())}
            m.write_json(root / 'SOURCE.json', receipt)
            with patch.object(m, 'source_inventory', return_value={}):
                self.assertEqual(m.verify(root), binary)
                binary.write_text('unexpected drift')
                with self.assertRaisesRegex(ValueError, 'bytes changed'):
                    m.verify(root)
            self.assertEqual(binary.read_text(), 'unexpected drift')

    def test_fake_install_exercises_frozen_explicit_command_and_receipt(self):
        # Fake acquisition/build only, never a dependency installation or NVIDIA scan.
        with tempfile.TemporaryDirectory(dir='/private/tmp') as directory:
            state = Path(directory); calls = []
            def backend(argv, cwd, env, timeout=120):
                args = [str(x) for x in argv]; calls.append((args, dict(env)))
                stdout = ''
                if 'sync' in args:
                    (cwd / '.venv/bin').mkdir(parents=True)
                    (cwd / '.venv/bin/python').symlink_to(Path(sys.executable).resolve())
                    (cwd / '.venv/bin/skillspector').write_text('fixture scanner, not executable')
                elif 'sys.version_info' in ' '.join(args):
                    stdout = json.dumps({'version': [3, 14, 0], 'prefix': '/fixture-python'})
                elif 'list' in args:
                    stdout = '[{"name":"skillspector","version":"2.12.0"}]'
                elif '--version' in args:
                    stdout = 'SkillSpector v2.12.0'
                return subprocess.CompletedProcess(args, 0, stdout, '')
            with patch.object(m.platform, 'system', return_value='Darwin'), \
                 patch.object(m, 'capture', side_effect=backend), \
                 patch.object(m, 'source_inventory', return_value={}), \
                 patch.object(m, 'network_guard', return_value=([], {'network_denied': True, 'errno': errno.EPERM})):
                binary = m.install(state, sys.executable, '/usr/bin/true')
            command, env = next((a, e) for a, e in calls if 'sync' in a)
            for flag in ('--frozen', '--no-config', '--no-dev', '--no-editable', '--python'):
                self.assertIn(flag, command)
            self.assertNotIn('--all-extras', command)
            self.assertEqual(env['UV_PYTHON_DOWNLOADS'], 'never')
            saved = json.loads((binary.parents[2] / 'SOURCE.json').read_text())
            self.assertEqual(saved['revision'], m.REVISION)
            self.assertIn('.venv/bin/skillspector', saved['runtime_files'])
            self.assertFalse(saved['provider_calls'])


if __name__ == '__main__':
    unittest.main()
