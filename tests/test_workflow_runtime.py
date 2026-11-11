"""Workflow acceptance rejects semantic failures and preserves external ownership."""
import importlib.util
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('workflow_recipe', ROOT / 'recipes/workflows.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


class WorkflowRuntime(unittest.TestCase):
    def execution(self, output=None, error=None):
        result = {'runData': {'Result': [{'data': {'main': [[{'json': output or {'accepted': True, 'total': 42}}]]}}]}}
        if error:
            result['error'] = error
        return {'data': {'resultData': result}, 'status': 'success'}

    def test_no_exit_or_success_message_can_replace_output_assertion(self):
        with self.assertRaises(ValueError):
            w.assert_execution('Execution was successful:')
        with self.assertRaises(ValueError):
            w.assert_execution(json.dumps(self.execution({'accepted': True, 'total': 41})))
        with self.assertRaises(ValueError):
            w.assert_execution(json.dumps(self.execution(error={'message': 'fixture failed'})))
        self.assertEqual(w.assert_execution('startup\n' + json.dumps(self.execution())), {'accepted': True, 'total': 42})

    def test_wrong_valid_branch_and_activation_are_not_success(self):
        value = self.execution()
        value['data']['resultData']['runData']['Rejected'] = []
        with self.assertRaises(ValueError):
            w.assert_execution(json.dumps(value))
        with self.assertRaises(ValueError):
            w.extract_workflow('[{"id":"some-other-workflow","connections":{}}]')

    def test_internal_tokens_are_removed_before_evidence(self):
        text = '{"resumeToken":"sensitive-fixture","apiKey": "other", "total":42}'
        clean = json.loads(w.redact(text))
        self.assertEqual(clean, {'resumeToken': '[redacted]', 'apiKey': '[redacted]', 'total': 42})

    def test_preparation_preserves_changed_bytes_and_empty_docker_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = w.prepare(Path(tmp).resolve())
            original = (root / 'fixture.json').read_bytes()
            (root / 'fixture.json').write_bytes(b'user-owned edit')
            with self.assertRaises(ValueError):
                w.prepare(Path(tmp).resolve())
            self.assertEqual((root / 'fixture.json').read_bytes(), b'user-owned edit')
            (root / 'fixture.json').write_bytes(original)
            (root / 'docker-config/config.json').write_text('{}')
            with self.assertRaises(ValueError):
                w.verify(root)

    def test_docker_environment_does_not_inherit_provider_proxy_or_home(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = w.prepare(Path(tmp).resolve() / 'state')
            server = socket.socket(socket.AF_UNIX)
            try:
                sock = str(Path(tmp) / 'engine.sock')
                server.bind(sock)
                with patch.dict(w.os.environ, {'OPENAI_API_KEY': 'not-real', 'HTTPS_PROXY': 'not-real', 'DOCKER_AUTH_CONFIG': 'not-real'}):
                    env = w.docker_env(root, 'unix://' + sock)
                self.assertNotIn('OPENAI_API_KEY', env)
                self.assertNotIn('HTTPS_PROXY', env)
                self.assertNotIn('DOCKER_AUTH_CONFIG', env)
                self.assertEqual(env['HOME'], str(root / 'cli-home'))
                self.assertEqual(env['DOCKER_CONFIG'], str(root / 'docker-config'))
            finally:
                server.close()
        with self.assertRaises(ValueError):
            w.docker_env(Path('/unused'), 'tcp://remote:2375')

    def test_existing_foreign_resource_is_rejected_before_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = w.prepare(Path(tmp).resolve())
            def fake(root, args, **kwargs):
                if args[0] == 'ps':
                    return subprocess.CompletedProcess(args, 0, 'foreign-container\n', '')
                return subprocess.CompletedProcess(args, 0, '{}', '')
            with patch.object(w, 'docker', side_effect=fake) as run:
                with self.assertRaises(ValueError):
                    w.owned(root)
                self.assertEqual([call.args[1][0] for call in run.call_args_list], ['ps', 'inspect'])

    def test_compose_has_no_host_socket_home_bind_or_privilege(self):
        model = json.loads((w.ASSETS / 'compose.json').read_text())
        service = model['services']['n8n']
        self.assertEqual(service['image'], w.IMAGE)
        self.assertEqual(service['ports'][0]['host_ip'], '127.0.0.1')
        self.assertEqual(service['volumes'], ['data:/home/node/.n8n'])
        self.assertEqual(service['restart'], 'no')
        self.assertFalse(service.get('privileged', False))
        self.assertEqual(service['cap_drop'], ['ALL'])
        for flag in ('N8N_DIAGNOSTICS_ENABLED', 'N8N_VERSION_NOTIFICATIONS_ENABLED', 'N8N_TEMPLATES_ENABLED'):
            self.assertEqual(service['environment'][flag], 'false')
        for name in ('fixture', 'miswired', 'invalid'):
            workflow = json.loads((w.ASSETS / (name + '.json')).read_text())
            self.assertFalse(workflow['active'])
            self.assertTrue(all(n['type'].split('.')[-1] in {'manualTrigger', 'set', 'if', 'nstackDeliberatelyMissing'} for n in workflow['nodes']))

    def test_trigger_is_source_only_pinned_to_selected_sdk(self):
        source = json.loads((w.ASSETS.parent / 'trigger/SOURCE.json').read_text())
        self.assertEqual(source['version'], '4.8.3')
        self.assertEqual(source['skill_sdk_version'], '4.8.3')
        self.assertEqual(len(source['files']), 14)
        self.assertIn('Dedicated engine', source['isolation_gate'])
        self.assertTrue(all(source['revision'] in f['url'] for f in source['files']))

    def test_failed_post_start_boundary_stops_only_the_owned_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = w.prepare(Path(tmp).resolve())
            bad = {'restart': 'no', 'mounts': [], 'memory_limit': 2 * 1024 ** 3,
                   'nano_cpus': 2000000000, 'privileged': False, 'cap_drop': ['ALL'],
                   'security_options': ['no-new-privileges:true'], 'ports': {}}
            with patch.object(w, 'owned', return_value=[]), patch.object(w, 'status', side_effect=[{'containers': []}, {'containers': [bad]}]), patch.object(w, 'compose', return_value=subprocess.CompletedProcess([], 0, '', '')) as run, patch.object(w.socket, 'socket'), patch.object(w, 'stop') as stop:
                with self.assertRaisesRegex(ValueError, 'localhost UI port'):
                    w.start(root, 'unix:///owned-engine.sock')
                stop.assert_called_once_with(root, 'unix:///owned-engine.sock')
                self.assertEqual(run.call_args.args[1], ['up', '-d', '--pull', 'never'])

    def test_partial_start_preserves_original_error_if_cleanup_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = w.prepare(Path(tmp).resolve())
            with patch.object(w, 'owned', return_value=[]), patch.object(w, 'status', return_value={'containers': []}), patch.object(w, 'compose', return_value=subprocess.CompletedProcess([], 1, '', '')), patch.object(w.socket, 'socket'), patch.object(w, 'stop', side_effect=ValueError('cleanup failed')) as stop:
                with self.assertRaisesRegex(ValueError, 'Project startup failed'):
                    w.start(root)
                stop.assert_called_once_with(root, None)

    def test_real_sigterm_during_check_runs_finally_and_restores_handler(self):
        # Send SIGTERM to this private child only. Use the real CLI check/finally
        # path, replacing Docker operations so this regression needs no engine.
        script = '''import importlib.util,json,os,pathlib,signal,subprocess,sys
spec=importlib.util.spec_from_file_location('w',sys.argv[1]);w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
state=pathlib.Path(sys.argv[2]);out=pathlib.Path(sys.argv[3]);calls=[];previous=signal.getsignal(signal.SIGTERM)
w.owned=lambda *a,**k:[]
w.image_info=lambda *a,**k:{}
w.compose=lambda *a,**k:subprocess.CompletedProcess([],0,'','')
def stop(root,*a,**k):calls.append(str(root));return {'containers':[]}
w.stop=stop
def seed(*a,**k):os.kill(os.getpid(),signal.SIGTERM)
w.seed=seed
sys.argv=['workflows.py','--state',str(state),'check']
try:w.main()
except SystemExit as e:
 out.write_text(json.dumps({'exit':e.code,'stops':calls,'handler_restored':signal.getsignal(signal.SIGTERM)==previous}))
 raise
'''
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            record = base / 'cancel.json'
            proc = subprocess.run([sys.executable, '-c', script, str(ROOT / 'recipes/workflows.py'), str(base / 'state'), str(record)], capture_output=True, text=True, timeout=10)
            self.assertEqual(proc.returncode, 130, proc.stderr)
            result = json.loads(record.read_text())
            expected = str(base / 'state/native-tools/workflows/n8n' / w.VERSION)
            self.assertEqual(result['stops'], [expected, expected])
            self.assertTrue(result['handler_restored'])


if __name__ == '__main__':
    unittest.main()
