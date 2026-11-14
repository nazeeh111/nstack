"""Fixed source/package identity and bounded static-route controls, without native side effects."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('craft_recipe', ROOT / 'recipes/craft_anything.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class CraftAnything(unittest.TestCase):
    def test_complete_original_method_and_support_match_exact_git_blobs(self):
        addon = ROOT / 'addons/craft-anything'
        source = json.loads((addon / 'SOURCE.json').read_text())
        self.assertEqual(source['revision'], m.REVISION)
        for name, row in source['upstream_files'].items():
            raw = (addon / name).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), row['sha256'], name)
            self.assertEqual(hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest(), row['git_blob'], name)
        raw = (addon / 'upstream/ORIGINAL-SKILL.md').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), '67af4e9bd3658d277eb057789bdff0d60fbae8df94995d18e444546f1ae1f529')
        self.assertEqual({p.name for p in addon.rglob('SKILL.md')}, {'SKILL.md'})

    def test_echoed_query_is_not_a_passing_observation(self):
        original = 'synthetic-hash'
        def evidence(number, result):
            return {'id': 'ev_' + str(number), 'subject': {'sha256': original}, 'result': result}
        docs = [evidence(1, {'format': 'mach-o', 'architecture': 'arm64'}),
                evidence(2, {'functions': [{'name': '_craft_answer'}]}),
                evidence(3, {'matches': [{'text': 'NSTACK_CRAFT_SENTINEL'}]})]
        negative = evidence(4, {'matches': [], 'total': 0})
        m.assert_fixture(docs, negative, original)
        docs[2] = evidence(3, {'matches': [], 'total': 0})
        docs[2]['params'] = {'pattern': 'NSTACK_CRAFT_SENTINEL'}
        with self.assertRaises(ValueError):
            m.assert_fixture(docs, negative, original)

    def test_wrong_download_never_mounted_or_executed(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory).resolve() / 'state'
            image = state.parent / 'wrong.dmg'; image.write_bytes(b'not an official image')
            with patch.object(m, 'host'), patch.object(m, 'checked') as native:
                with self.assertRaises(ValueError):
                    m.install(state, image)
                native.assert_not_called()
            self.assertFalse(m.runtime_root(state).exists())

    def test_native_assessment_rejection_has_no_execution_fallback(self):
        replies = [dict(exit_code=0, stdout='', stderr='valid on disk'),
                   dict(exit_code=0, stdout='', stderr='TeamIdentifier=' + m.TEAM + '\nNotarization Ticket=stapled'),
                   dict(exit_code=3, stdout='', stderr='rejected')]
        with patch.object(m, 'capture', side_effect=replies) as calls:
            with self.assertRaises(ValueError):
                m.assess_app(Path('/synthetic/Craft Anything.app'))
        self.assertEqual(calls.call_count, 3)
        self.assertEqual(calls.call_args.args[0][0], '/usr/sbin/spctl')

    def test_forging_receipt_cannot_accept_changed_package(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory).resolve()
            root = m.runtime_root(state); app = root / 'Craft Anything.app'
            cli = app / 'Contents/MacOS/craft-anything-cli'; cli.parent.mkdir(parents=True)
            cli.write_bytes(b'synthetic-original'); cli.chmod(0o755)
            original = m.manifest_hash(m.manifest(app))
            saved = {'revision': m.REVISION, 'dmg_sha256': m.DMG_SHA256,
                     'package_manifest_sha256': original}
            m.write(root / 'SOURCE.json', saved)
            with patch.object(m, 'host'), patch.object(m, 'assess_app'), \
                 patch.object(m, 'APP_MANIFEST_SHA256', original), patch.object(m, 'CLI_SHA256', m.digest(cli)):
                self.assertEqual(m.verify(state), cli)
                cli.write_bytes(b'altered')
                saved['package_manifest_sha256'] = m.manifest_hash(m.manifest(app))
                m.write(root / 'SOURCE.json', saved)
                with self.assertRaises(ValueError):
                    m.verify(state)
                self.assertEqual(cli.read_bytes(), b'altered')

    def test_no_provider_proxy_account_or_home_environment_inherited(self):
        with patch.dict(m.os.environ, {'OPENAI_API_KEY': 'synthetic', 'HTTPS_PROXY': 'synthetic',
                                      'HOME': '/synthetic/personal-home', 'CODEX_HOME': '/synthetic/host'}):
            env = m.environment('/private/owned/run')
        self.assertFalse({'OPENAI_API_KEY', 'HTTPS_PROXY', 'CODEX_HOME'} & env.keys())
        self.assertEqual(env['HOME'], '/private/owned/run/home')
        self.assertEqual(env['PATH'], '/private/owned/run/empty-bin')

    def test_static_route_rejects_execution_setup_and_foreign_output(self):
        with patch.object(m, 'verify') as verify:
            for tool in ('rebuild', 'setup', 'chat', 'mcp', 'ai', 'engines-install', 'native-objdump-run'):
                with self.assertRaises(ValueError):
                    m.execute('/unused', '/unused', '/unused', tool)
            verify.assert_not_called()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve(); source = base / 'artifact'; source.write_bytes(b'fixture')
            out = base / 'other-work'; out.mkdir(); original = out / 'keep'; original.write_text('unrelated dirty work')
            with patch.object(m, 'verify', return_value=base / 'cli'):
                with self.assertRaises(ValueError):
                    m.execute(base / 'state', source, out)
            self.assertEqual(original.read_text(), 'unrelated dirty work')
            self.assertEqual(sorted(p.name for p in out.iterdir()), ['keep'])

    def test_input_alias_secret_location_and_parameter_path_overrides_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve(); source = base / 'artifact'; source.write_bytes(b'fixture')
            alias = base / 'alias'; alias.symlink_to(source)
            with self.assertRaises(ValueError):
                m.approved_file(alias)
            secret = base / '.ssh/synthetic'; secret.parent.mkdir(); secret.write_text('synthetic')
            with self.assertRaises(ValueError):
                m.approved_file(secret)
            with patch.object(m, 'verify') as verify:
                for params in ({'path': '/other'}, {'allow_run': True}, {'project': '/other'}, []):
                    with self.assertRaises(ValueError):
                        m.execute(base / 'state', source, base / 'out', 'native-functions-list', params)
                verify.assert_not_called()


if __name__ == '__main__':
    unittest.main()
