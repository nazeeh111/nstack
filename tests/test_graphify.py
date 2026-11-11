"""Graphify bounded-route checks; live acceptance uses only owned synthetic code."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import platform
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('graphify_recipe', ROOT / 'recipes/graphify.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

FIXTURE = {
    'base.py': 'class Base:\n    def store(self, value):\n        return value\n',
    'service.py': 'from base import Base\n\nclass Service(Base):\n    def run(self, value):\n        return self.store(value)\n',
    'helper.py': 'def normalize(value):\n    return value.strip()\n',
    'app.py': 'from helper import normalize\n\ndef run(value):\n    return normalize(value)\n',
    'notes.md': '# Semantic omission sentinel\nThis documentation must not create semantic nodes.\n',
}


def load_graph(out):
    return json.loads((out / 'graphify-out/graph.json').read_text())


def validate_known_graph(test, source, graph, helper='helper.py', service=True):
    """Ground truth comes from stdlib Python AST, not Graphify's own evaluator."""
    nodes = graph['nodes']; edges = graph.get('edges', graph.get('links', [])); by_id = {n['id']: n for n in nodes}
    test.assertEqual(len(nodes), len(by_id)); test.assertGreater(len(edges), 0)
    test.assertTrue(all(e['source'] in by_id and e['target'] in by_id for e in edges))
    test.assertTrue(all(n.get('_origin') == 'ast' and n['source_file'].endswith('.py') for n in nodes))
    test.assertEqual(graph.get('input_tokens'), 0); test.assertEqual(graph.get('output_tokens'), 0)
    call = next(x for x in ast.walk(ast.parse((source / 'app.py').read_text())) if isinstance(x, ast.Call))
    caller = next(n['id'] for n in nodes if n['source_file'] == 'app.py' and n['label'] == 'run()')
    callee = next(n['id'] for n in nodes if n['source_file'] == helper and n['label'] == 'normalize()')
    test.assertTrue(any(e['source'] == caller and e['target'] == callee and e['relation'] == 'calls'
                        and e['source_location'] == 'L' + str(call.lineno) for e in edges))
    if service:
        cls = next(x for x in ast.walk(ast.parse((source / 'service.py').read_text())) if isinstance(x, ast.ClassDef))
        child = next(n['id'] for n in nodes if n['source_file'] == 'service.py' and n['label'] == cls.name)
        parent = next(n['id'] for n in nodes if n['source_file'] == 'base.py' and n['label'] == cls.bases[0].id)
        test.assertTrue(any(e['source'] == child and e['target'] == parent and e['relation'] == 'inherits'
                            and e['source_location'] == 'L' + str(cls.lineno) for e in edges))
    return {'nodes': len(nodes), 'edges': len(edges), 'known_call_lineno': call.lineno}


class GraphifyStatic(unittest.TestCase):
    def test_locked_assets_and_reference_closure(self):
        wheels = m.assets()['wheels']; self.assertEqual(len(wheels), 31)
        self.assertEqual(sum(x['scope'] == 'core' for x in wheels), 30)
        self.assertFalse(any(x['name'] in ('openai', 'anthropic', 'boto3', 'mcp', 'watchdog', 'graspologic') for x in wheels))
        for host in ('codex', 'opencode'):
            self.assertEqual(len(list((m.ASSETS / 'upstream' / host / 'references').glob('*.md'))), 8)
        self.assertFalse((m.ASSETS / 'SKILL.md').exists())

    def test_environment_is_constructed_without_accounts(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'synthetic-fixture', 'HTTPS_PROXY': 'synthetic-fixture'}):
            env = m.clean_env('/owned/home', '/owned/tmp')
        self.assertNotIn('OPENAI_API_KEY', env); self.assertNotIn('HTTPS_PROXY', env)
        self.assertEqual(env['GRAPHIFY_BACKEND'], 'none'); self.assertNotIn('/usr/bin', env['PATH'])

    def test_rejects_symlink_and_sensitive_input_before_read(self):
        with tempfile.TemporaryDirectory(prefix='nstack-graphify-input-', dir='/private/tmp') as name:
            source = Path(name) / 'source'; source.mkdir(); key = source / '.env'; key.write_text('synthetic fixture')
            with self.assertRaisesRegex(ValueError, 'Sensitive'): m.approved_source(source)
            key.unlink(); (source / 'link.py').symlink_to('/nonexistent')
            with self.assertRaisesRegex(ValueError, 'symlink'): m.approved_source(source)

    def test_preserves_unowned_runtime(self):
        with tempfile.TemporaryDirectory(prefix='nstack-graphify-unowned-', dir='/private/tmp') as name:
            root = Path(name); sentinel = root / 'keep'; sentinel.write_text('preserve')
            with self.assertRaisesRegex(ValueError, 'Unowned'): m.verify(root)
            self.assertEqual(sentinel.read_text(), 'preserve')


@unittest.skipUnless(platform.system() == 'Darwin' and (m.runtime_root() / 'READY.json').is_file(), 'explicitly prepared macOS runtime needed')
class GraphifyRuntime(unittest.TestCase):
    def test_actual_code_only_repeat_rename_delete_and_queries(self):
        with tempfile.TemporaryDirectory(prefix='nstack-graphify-test-', dir='/private/tmp') as name:
            work = Path(name); source = work / 'fixture'; source.mkdir(); out = work / 'output'
            for filename, body in FIXTURE.items(): (source / filename).write_text(body)
            before = {p.name: m.digest(p) for p in source.iterdir()}
            first = m.run(m.runtime_root(), source, out)
            self.assertTrue(first['guard']['network_denied']); self.assertTrue(first['guard']['outside_read_denied'])
            graph = load_graph(out); validate_known_graph(self, source, graph)
            self.assertEqual(before, {p.name: m.digest(p) for p in source.iterdir()})
            m.run(m.runtime_root(), source, out); self.assertEqual(graph, load_graph(out))
            for command, terms in [('query', ['normalize']), ('path', ['app.py::run()', 'normalize()']), ('explain', ['normalize()'])]:
                receipt = m.run(m.runtime_root(), source, out, command, terms)
                command_log = json.loads((Path(receipt['logs']) / 'command.json').read_text())
                self.assertIn('normalize', command_log['stdout'])
            (source / 'helper.py').rename(source / 'processing.py')
            (source / 'app.py').write_text(FIXTURE['app.py'].replace('helper', 'processing'))
            m.run(m.runtime_root(), source, out); renamed = load_graph(out)
            validate_known_graph(self, source, renamed, helper='processing.py')
            self.assertFalse(any(n['source_file'] == 'helper.py' or n['id'].startswith('helper') for n in renamed['nodes']))
            (source / 'service.py').unlink()
            m.run(m.runtime_root(), source, out); deleted = load_graph(out)
            validate_known_graph(self, source, deleted, helper='processing.py', service=False)
            self.assertFalse(any(n['source_file'] == 'service.py' or n['id'].startswith('service') for n in deleted['nodes']))
            self.assertFalse(any(p.name == 'graph.html' for p in out.rglob('*')))


if __name__ == '__main__': unittest.main()
