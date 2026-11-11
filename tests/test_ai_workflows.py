"""Meaningful offline checks for container and project scope boundaries."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ai_recipe', ROOT / 'recipes/ai_workflows.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def inspection():
    return {'Image': 'sha256:fixture', 'Config': {'Labels': {'org.nstack.owner': 'ai-workflows', 'org.nstack.fingerprint': 'fixture'},
            'Env': ['LANGSMITH_TRACING=false', 'LANGCHAIN_TRACING_V2=false']},
            'HostConfig': {'NetworkMode': 'none', 'ReadonlyRootfs': True, 'Privileged': False,
                'PortBindings': {}, 'RestartPolicy': {'Name': 'no'}, 'Memory': 1073741824,
                'NanoCpus': 1000000000, 'PidsLimit': 128, 'CapAdd': [], 'CapDrop': ['ALL'],
                'SecurityOpt': ['no-new-privileges=true']},
            'Mounts': [{'Type': 'bind', 'Source': '/fixture/work', 'Destination': '/work', 'RW': True}]}


class AiWorkflows(unittest.TestCase):
    def test_scope_validator_rejects_network_privilege_restart_and_mount_expansion(self):
        original = inspection()
        m.validate_container(original, Path('/fixture/work'), None, 'fixture', 'sha256:fixture')
        mutations = []
        for key, value in [('NetworkMode', 'bridge'), ('ReadonlyRootfs', False), ('Privileged', True),
                           ('PortBindings', {'8000/tcp': [{'HostPort': '8000'}]}),
                           ('RestartPolicy', {'Name': 'always'}), ('Memory', 0), ('NanoCpus', 0),
                           ('PidsLimit', 0), ('CapAdd', ['SYS_ADMIN']), ('CapDrop', []), ('SecurityOpt', [])]:
            bad = copy.deepcopy(original)
            bad['HostConfig'][key] = value
            mutations.append(bad)
        bad = copy.deepcopy(original)
        bad['Mounts'].append({'Type': 'bind', 'Source': '/private/account', 'Destination': '/account', 'RW': False})
        mutations.append(bad)
        bad = copy.deepcopy(original)
        bad['Mounts'][0]['Type'] = 'volume'
        mutations.append(bad)
        for bad in mutations:
            with self.assertRaises(ValueError):
                m.validate_container(bad, Path('/fixture/work'), None, 'fixture', 'sha256:fixture')

    def test_readonly_project_mount_and_tracing_credentials_image_controls(self):
        good = inspection()
        good['Mounts'].append({'Type': 'bind', 'Source': '/fixture/project', 'Destination': '/project', 'RW': False})
        m.validate_container(good, Path('/fixture/work'), Path('/fixture/project'), 'fixture', 'sha256:fixture')
        bads = []
        bad = copy.deepcopy(good); bad['Mounts'][1]['RW'] = True; bads.append(bad)
        bad = copy.deepcopy(good); bad['Config']['Env'][0] = 'LANGSMITH_TRACING=true'; bads.append(bad)
        bad = copy.deepcopy(good); bad['Config']['Env'].append('OPENAI_API_KEY=synthetic-fixture'); bads.append(bad)
        bad = copy.deepcopy(good); bad['Image'] = 'sha256:wrong'; bads.append(bad)
        bad = copy.deepcopy(good); bad['Config']['Labels']['org.nstack.owner'] = 'other'; bads.append(bad)
        for bad in bads:
            with self.assertRaises(ValueError):
                m.validate_container(bad, Path('/fixture/work'), Path('/fixture/project'), 'fixture', 'sha256:fixture')

    def test_project_rejects_host_roots_vault_settings_and_link_alias(self):
        runtime = object.__new__(m.Runtime)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            runtime.state = root / 'private-state'
            runtime.state.mkdir()
            project = root / 'project'; project.mkdir()
            self.assertEqual(runtime.bounded_project(project), project)
            alias = root / 'alias'; alias.symlink_to(project)
            for bad in [Path('/'), Path.home(), Path.home() / 'Knowledge', Path.home() / '.docker', runtime.state, root, alias]:
                if bad.exists():
                    with self.assertRaises(ValueError):
                        runtime.bounded_project(bad)

    def test_lock_contains_exact_hashes_and_matches_official_wheel_manifest(self):
        source = json.loads((m.TEMPLATE / 'SOURCE.json').read_text())
        lock = (m.TEMPLATE / 'requirements.lock').read_text()
        self.assertEqual(hashlib.sha256(lock.encode()).hexdigest(), source['lock_sha256'])
        rows = [line for line in lock.splitlines() if not line.startswith('#') and line.strip()]
        self.assertEqual(len(rows), len(source['wheels']))
        self.assertEqual(len(rows), 42)
        for row in source['wheels']:
            self.assertIn(row['name'] + '==' + row['version'] + ' --hash=sha256:' + row['sha256'], rows)
            self.assertTrue(row['url'].startswith('https://files.pythonhosted.org/'))
        self.assertFalse(any(x['name'].startswith(('langchain-openai', 'langchain-anthropic')) for x in source['wheels']))
        self.assertEqual(len(m.identity()[0]), 64)

    def test_langfuse_profile_six_services_no_gateway_no_egress_only_loopback(self):
        compose = json.loads((m.TEMPLATE / 'langfuse/compose.json').read_text())
        self.assertEqual(set(compose['services']), {'langfuse-web', 'langfuse-worker', 'postgres', 'redis', 'clickhouse', 'minio'})
        self.assertEqual(compose['networks'], {'private': {'internal': True}})
        for name, service in compose['services'].items():
            self.assertEqual(service['restart'], 'no')
            self.assertEqual(service['networks'], ['private'])
            self.assertRegex(service['image'], r'@sha256:[0-9a-f]{64}$')
            self.assertFalse(service.get('privileged', False))
            for port in service.get('ports', []):
                self.assertTrue(port.startswith('127.0.0.1:'))
                self.assertIn(name, {'langfuse-web', 'minio'})
            if name.startswith('langfuse-'):
                self.assertEqual(service['environment']['TELEMETRY_ENABLED'], 'false')
                self.assertEqual(service['environment']['LANGFUSE_IN_APP_AGENT_ENABLED'], 'false')
                self.assertEqual(service['environment']['LANGFUSE_AI_GATEWAY_ENABLED'], 'false')
        source = json.loads((m.TEMPLATE / 'langfuse/SOURCE.json').read_text())
        self.assertEqual(hashlib.sha256((m.TEMPLATE / 'langfuse/docker-compose.upstream.yml').read_bytes()).hexdigest(), source['upstream_compose_sha256'])
        self.assertEqual(hashlib.sha256((m.TEMPLATE / 'langfuse/compose.json').read_bytes()).hexdigest(), source['derived_compose_sha256'])


if __name__ == '__main__':
    unittest.main()
