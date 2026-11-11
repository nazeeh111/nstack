"""Observable blinding, order sensitivity, incomplete evidence and safe local I/O."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'addons/llm-council/scripts/blind_review.py'
spec = importlib.util.spec_from_file_location('blind_review', SCRIPT)
review = importlib.util.module_from_spec(spec); spec.loader.exec_module(review)


class CouncilTests(unittest.TestCase):
    def data(self):
        return {'question': 'Which calculation matches the supplied facts?', 'rubric': ['Correct arithmetic'],
                'candidates': [{'id': 'correct', 'text': '17*23=391', 'origin': 'model-alpha'},
                               {'id': 'wrong', 'text': '17*23=400', 'origin': 'model-beta'}],
                'judges': [{'id': 'critic', 'origin': 'model-alpha'}]}

    def judgments(self, directory, choose_correct):
        rows = []
        for path in sorted((directory / 'packets').glob('*.json')):
            packet = review.read_json(path); responses = packet['responses']; labels = [v['label'] for v in responses]
            first = next(v['label'] for v in responses if '391' in v['text']) if choose_correct else labels[0]
            rows.append({'packet_id': packet['packet_id'], 'ranking': [[first], [v for v in labels if v != first]],
                         'reasons': {v['label']: 'Arithmetic checked against the rubric' for v in responses}, 'evidence_gaps': []})
        return rows

    def test_packets_withhold_declared_origins_and_reverse_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp).resolve() / 'review'; review.prepare(self.data(), out, seed=0)
            packets = [review.read_json(p) for p in sorted((out / 'packets').glob('*.json'))]
            self.assertEqual([r['text'] for r in packets[0]['responses']], list(reversed([r['text'] for r in packets[1]['responses']])))
            for p in (out / 'packets').glob('*.json'):
                text = p.read_text(); self.assertNotIn('model-alpha', text); self.assertNotIn('model-beta', text)
                self.assertNotIn('origin', text); self.assertEqual(p.stat().st_mode & 0o777, 0o600)
            self.assertEqual(out.stat().st_mode & 0o777, 0o700)
            before = (out / 'manifest.json').read_bytes()
            with self.assertRaises(FileExistsError): review.prepare(self.data(), out)
            self.assertEqual((out / 'manifest.json').read_bytes(), before)

    def test_always_first_judge_is_flagged_and_not_turned_into_truth(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp).resolve() / 'review'; review.prepare(self.data(), out, seed=1)
            result = review.summarize(out, self.judgments(out, False))
            self.assertEqual(result['state'], 'complete'); self.assertEqual(result['order_disagreements'], ['critic'])
            self.assertEqual(result['mean_ranks'], {'correct': 1.5, 'wrong': 1.5})
            self.assertNotIn('winner', result); self.assertIn('Requires independent evidence', result['final_decision'])

    def test_evidence_choice_is_stable_across_order_and_missing_is_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp).resolve() / 'review'; review.prepare(self.data(), out, seed=1)
            judgments = self.judgments(out, True); result = review.summarize(out, judgments)
            self.assertEqual(result['order_disagreements'], []); self.assertEqual(result['mean_ranks']['correct'], 1)
            self.assertEqual(review.summarize(out, judgments[:1])['state'], 'incomplete')
            with self.assertRaisesRegex(ValueError, 'Duplicate'): review.summarize(out, judgments + judgments[:1])

    def test_ties_supported_and_malformed_ranking_or_reason_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp).resolve() / 'review'; review.prepare(self.data(), out)
            rows = self.judgments(out, True)
            for r in rows: r['ranking'] = [['R1', 'R2']]
            result = review.summarize(out, rows); self.assertEqual(result['mean_ranks'], {'correct': 1.5, 'wrong': 1.5})
            broken = copy.deepcopy(rows); broken[0]['ranking'] = [['R1'], ['R1']]
            with self.assertRaises(ValueError): review.summarize(out, broken)
            broken = copy.deepcopy(rows); broken[0]['reasons']['R1'] = ''
            with self.assertRaises(ValueError): review.summarize(out, broken)

    def test_packet_mutation_and_invalid_input_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve(); out = base / 'review'; review.prepare(self.data(), out)
            rows = self.judgments(out, True); packet = out / 'packets/p001.json'; data = review.read_json(packet); data['question'] = 'Changed'; packet.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'changed'): review.summarize(out, rows)
            data = self.data(); data['candidates'][1]['id'] = 'correct'
            with self.assertRaises(ValueError): review.prepare(data, base / 'bad')
            self.assertFalse((base / 'bad').exists())

    def test_regular_bounded_inputs_only_and_exclusive_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve(); f = base / 'input.json'; f.write_text('{}')
            link = base / 'alias.json'; link.symlink_to(f)
            with self.assertRaises(OSError): review.read_json(link)
            private = base / '.ssh/input.json'; private.parent.mkdir(); private.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'Private'): review.read_json(private)
            fifo = base / 'pipe.json'; os.mkfifo(fifo)
            with self.assertRaisesRegex(ValueError, 'regular'): review.read_json(fifo)
            f.write_bytes(b'x' * (review.MAX_BYTES + 1))
            with self.assertRaisesRegex(ValueError, 'exceeds'): review.read_json(f)
            with self.assertRaises(FileExistsError): review.write_new(f, {})

    def test_worktrees_work_and_symlink_outputs_are_rejected_consistently(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve(); task = base / '.codex/worktrees/task'; task.mkdir(parents=True)
            source = task / 'input.json'; source.write_text(json.dumps(self.data()))
            self.assertEqual(review.read_json(source), self.data())
            review.prepare(review.read_json(source), task / 'review')
            self.assertEqual(review.summarize(task / 'review', [])['state'], 'incomplete')
            alias = base / 'alias'; alias.symlink_to(task, target_is_directory=True)
            with self.assertRaises(OSError): review.prepare(self.data(), alias / 'other')
            self.assertFalse((task / 'other').exists())
            with self.assertRaises(OSError): review.write_new(alias / 'report.json', {})
            self.assertFalse((task / 'report.json').exists())
            auth = base / '.codex/auth.json'; auth.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'Private'): review.read_json(auth)

    def test_evidence_reaches_critics_and_unknown_sources_are_not_discarded(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve(); data = self.data(); data['evidence'] = ['Fixture v1: multiply17 by23; source checked locally.']
            review.prepare(data, base / 'review')
            for p in (base / 'review/packets').glob('*.json'):
                self.assertEqual(review.read_json(p)['evidence'], data['evidence'])
            data['sources'] = ['Would have been silently lost']
            with self.assertRaisesRegex(ValueError, 'unknown'): review.prepare(data, base / 'bad')
            self.assertFalse((base / 'bad').exists())

    def test_corrupt_manifest_cannot_claim_complete_or_duplicate_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp).resolve() / 'review'; review.prepare(self.data(), out)
            path = out / 'manifest.json'; original = review.read_json(path)
            mutations = []
            empty = copy.deepcopy(original); empty['packets'] = {}; mutations.append(empty)
            duplicate = copy.deepcopy(original); duplicate['packets']['p001']['aliases'] = {'R1': 'correct', 'R2': 'correct'}; mutations.append(duplicate)
            wrong = copy.deepcopy(original); wrong['packets']['p001']['judge'] = 'missing'; mutations.append(wrong)
            repeated = copy.deepcopy(original); repeated['packets']['p002']['round'] = 'forward'; mutations.append(repeated)
            for broken in mutations:
                path.write_text(json.dumps(broken))
                with self.assertRaises(ValueError): review.summarize(out, [])

    def test_structured_evidence_reasons_survive_without_rejudging(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp).resolve() / 'review'; review.prepare(self.data(), out)
            rows = self.judgments(out, True)
            structured = {'supported': ['Checked arithmetic'], 'contradicted': [], 'unresolved': ['Scope remains synthetic']}
            rows[0]['reasons']['R1'] = structured; rows[1]['reasons']['R1'] = ['Independent source check', 'No factual confidence from votes']
            result = review.summarize(out, rows)
            self.assertIn(structured, result['judgments'][0]['reasons'].values())
            bad = copy.deepcopy(rows); bad[0]['reasons']['R1'] = {'empty': []}
            with self.assertRaises(ValueError): review.summarize(out, bad)
            bad = copy.deepcopy(rows); bad[0]['reasons']['R1'] = 42
            with self.assertRaises(ValueError): review.summarize(out, bad)


if __name__ == '__main__':
    unittest.main()
