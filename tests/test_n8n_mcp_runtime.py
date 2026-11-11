"""Docs-only transport boundaries and failure interpretation, without Docker."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('n8n_mcp_recipe', ROOT / 'recipes/n8n_mcp.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class N8nMcpRuntime(unittest.TestCase):
    def test_container_is_offline_readonly_and_has_no_mount_or_api_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = m.prepare(Path(tmp).resolve())
            args = m.launch_args(root, 'nstack-test')
        self.assertEqual(args[args.index('--network') + 1], 'none')
        self.assertEqual(args[args.index('--memory') + 1], '768m')
        self.assertIn('--read-only', args)
        self.assertIn('N8N_MCP_TELEMETRY_DISABLED=true', args)
        self.assertIn('MCP_MODE=stdio', args)
        self.assertEqual(args[-1], m.IMAGE)
        self.assertNotIn('--volume', args)
        self.assertNotIn('--mount', args)
        self.assertNotIn('--privileged', args)
        self.assertFalse(any('N8N_API_' in a for a in args))

    def test_host_provider_proxy_and_docker_auth_environment_is_not_forwarded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = m.prepare(Path(tmp).resolve())
            with patch.object(Path, 'is_socket', return_value=True), patch.dict(os.environ, {'N8N_API_KEY': 'not-real', 'OPENAI_API_KEY': 'not-real', 'HTTPS_PROXY': 'not-real', 'DOCKER_AUTH_CONFIG': 'not-real'}):
                env = m.environment(root)
            self.assertTrue(env['DOCKER_HOST'].startswith('unix:///'))
            for key in ('N8N_API_KEY', 'OPENAI_API_KEY', 'HTTPS_PROXY', 'DOCKER_AUTH_CONFIG'):
                self.assertNotIn(key, env)
            self.assertEqual(env['DOCKER_CONFIG'], str(root / 'docker-config'))

    def test_foreign_container_cleanup_never_reaches_remove(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = m.prepare(Path(tmp).resolve())
            with patch.object(m, 'docker', return_value=subprocess.CompletedProcess([], 0, '{}', '')) as runner:
                with self.assertRaises(ValueError):
                    m.cleanup(root, 'foreign')
                self.assertEqual(runner.call_count, 1)
                self.assertEqual(runner.call_args.args[1][0], 'inspect')

    def test_changed_bytes_and_linked_assets_are_preserved_and_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp).resolve()
            root = m.prepare(state)
            fixture = root / 'fixture.json'
            fixture.write_bytes(b'user edit')
            with self.assertRaises(ValueError):
                m.prepare(state)
            self.assertEqual(fixture.read_bytes(), b'user edit')
            fixture.unlink()
            fixture.symlink_to(ROOT / 'README.md')
            with self.assertRaises(ValueError):
                m.verify(root)

    def test_upstream_errors_cannot_be_misreported_as_valid_data(self):
        for response in ({'error': {'message': 'bad'}}, {'result': {'isError': True, 'content': [{'type': 'text', 'text': '{"valid":true}'}]}}):
            with self.assertRaises(ValueError):
                m.tool_document(response)
        raw = {'result': {'content': [{'type': 'text', 'text': '{"valid":false,"errors":["invalid node"]}'}]}}
        self.assertEqual(m.tool_document(raw), {'valid': False, 'errors': ['invalid node']})
        self.assertIn('invalid node', raw['result']['content'][0]['text'])

    def test_transport_matches_id_and_preserves_upstream_response(self):
        script = '''import sys,json
q=json.loads(sys.stdin.readline())
print(json.dumps({"jsonrpc":"2.0","method":"notifications/progress","params":{}}),flush=True)
print(json.dumps({"jsonrpc":"2.0","id":q["id"],"result":{"content":[{"type":"text","text":"unchanged source"}]}}),flush=True)
'''
        client = m.Client.__new__(m.Client)
        client.proc = subprocess.Popen([sys.executable, '-c', script], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        client.buffer = b''
        client.errors = bytearray()
        client.sequence = 0
        client.messages = []
        client.closed_streams = set()
        try:
            response = client.request('tools/list', timeout=5)
            self.assertEqual(response, {'jsonrpc': '2.0', 'id': 1, 'result': {'content': [{'type': 'text', 'text': 'unchanged source'}]}})
            self.assertEqual(client.messages[0]['method'], 'notifications/progress')
        finally:
            client.proc.communicate(timeout=5)

    def test_fixture_bytes_match_the_actually_executed_core_fixtures(self):
        for name in ('fixture', 'miswired', 'invalid'):
            self.assertEqual((m.ASSETS / (name + '.json')).read_bytes(), (m.ASSETS.parent / 'n8n' / (name + '.json')).read_bytes())
        good = json.loads((m.ASSETS / 'fixture.json').read_text())
        bad = json.loads((m.ASSETS / 'miswired.json').read_text())
        self.assertEqual(good['nodes'], bad['nodes'])
        self.assertNotEqual(good['connections']['IF'], bad['connections']['IF'])

    def test_image_revision_is_disclosed_separately_from_catalog_pin(self):
        source = json.loads((m.ASSETS / 'SOURCE.json').read_text())
        self.assertEqual(source['version'], '2.101.0')
        self.assertEqual(source['image_revision'], m.IMAGE_REVISION)
        self.assertNotEqual(source['selected_revision'], source['image_revision'])
        self.assertFalse(source['image_source_difference']['runtime_files_changed'])
        self.assertTrue(all(p.startswith('.github/') for p in source['image_source_difference']['only_changed_files']))


if __name__ == '__main__':
    unittest.main()
