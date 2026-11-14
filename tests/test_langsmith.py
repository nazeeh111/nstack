"""Portable registration derives commissioned runtime identity, preserving local state."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'lib')]
spec = importlib.util.spec_from_file_location('langsmith_recipe', ROOT / 'recipes/langsmith.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
from transaction import Transaction, fingerprint


class LangSmithRegistration(unittest.TestCase):
    def fixture(self, directory):
        state = Path(directory).resolve() / 'state'
        root = state / 'native-tools/ai-workflows/fixture-pin'
        root.mkdir(parents=True)
        runtime = Mock(root=root, fingerprint='fixture-pin')
        runtime.verify.return_value = {'fingerprint': 'fixture-pin'}
        code = state / 'code'
        self.enterContext(patch.object(m, 'Runtime', return_value=runtime))
        self.enterContext(patch.object(m.profile_install, 'stage', return_value=code))
        self.check = self.enterContext(patch.object(m, 'check', return_value={'passed': True}))
        return state, runtime, state / 'native-tools/index.json'

    def test_fresh_recipe_runtime_registers_both_discoverable_entries_repeat_and_rollback(self):
        with tempfile.TemporaryDirectory() as directory:
            state, runtime, index = self.fixture(directory)
            result = m.register(state)
            rows = json.loads(index.read_text())
            self.assertEqual([r['name'] for r in rows], ['LangChain / LangGraph', 'LangSmith'])
            self.assertTrue(all(r['runtime_root'] == str(runtime.root) for r in rows))
            self.assertFalse(rows[1]['hosted_tracing_enabled'])
            before = fingerprint(index)
            transactions = sorted((state / 'runs').glob('*/journal.json'))
            self.assertTrue(m.register(state)['unchanged'])
            self.assertEqual(fingerprint(index), before)
            self.assertEqual(sorted((state / 'runs').glob('*/journal.json')), transactions)
            self.assertEqual(self.check.call_count, 1)
            self.assertEqual(runtime.verify.call_count, 2)
            transaction = Transaction(result['transaction'])
            with transaction.lock():
                transaction.rollback()
            self.assertFalse(index.exists())

    def test_matching_rich_base_and_unrelated_records_survive_and_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            state, runtime, index = self.fixture(directory)
            original = [{'name': 'Other', 'local': 'preserve'},
                        {'name': 'LangChain / LangGraph', 'runtime_root': str(runtime.root),
                         'shared_runtime_id': 'nstack-ai-workflows-fixture-pin',
                         'checks': {'rich': 'deployment evidence'}}]
            index.write_text(json.dumps(original) + '\n')
            before = fingerprint(index)
            result = m.register(state)
            self.assertEqual(json.loads(index.read_text())[:-1], original)
            self.assertEqual(fingerprint(Path(result['transaction']) / 'restoration-rehearsal.json'), before)
            transaction = Transaction(result['transaction'])
            with transaction.lock():
                transaction.rollback()
            self.assertEqual(fingerprint(index), before)

    def test_uncommissioned_or_changed_runtime_does_not_publish_index(self):
        with tempfile.TemporaryDirectory() as directory:
            state, runtime, index = self.fixture(directory)
            runtime.verify.side_effect = ValueError('No owned commissioned runtime')
            with self.assertRaises(ValueError):
                m.register(state)
            self.assertFalse(index.exists())
            self.check.assert_not_called()

    def test_malformed_duplicate_or_stale_records_are_preserved(self):
        cases = [{}, [False], [{'name': 'LangChain / LangGraph'}],
                 [{'name': 'LangSmith'}], [{'name': 'LangChain / LangGraph'}, {'name': 'LangChain / LangGraph'}]]
        for rows in cases:
            with self.subTest(rows=rows), tempfile.TemporaryDirectory() as directory:
                state, runtime, index = self.fixture(directory)
                index.write_text(json.dumps(rows) + '\n')
                before = fingerprint(index)
                with self.assertRaises(ValueError):
                    m.register(state)
                self.assertEqual(fingerprint(index), before)
                self.check.assert_not_called()

    def test_concurrent_writer_wins_without_lost_update(self):
        with tempfile.TemporaryDirectory() as directory:
            state, runtime, index = self.fixture(directory)
            index.write_text('[]\n')
            def concurrent_write(_state):
                index.write_text('[{"name":"Concurrent owned record"}]\n')
                return {'passed': True}
            self.check.side_effect = concurrent_write
            with self.assertRaises(ValueError):
                m.register(state)
            self.assertEqual(json.loads(index.read_text()), [{'name': 'Concurrent owned record'}])

    def test_linked_index_is_not_followed(self):
        with tempfile.TemporaryDirectory() as directory:
            state, runtime, index = self.fixture(directory)
            other = state / 'unrelated.json'
            other.write_text('[]\n')
            before = fingerprint(other)
            index.symlink_to(other)
            with self.assertRaises(ValueError):
                m.register(state)
            self.assertTrue(index.is_symlink())
            self.assertEqual(fingerprint(other), before)
            runtime.verify.assert_not_called()


if __name__ == '__main__':
    unittest.main()
