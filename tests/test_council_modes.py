"""Actual balanced review rounds, mode separation and saved paired compatibility."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'addons/llm-council/scripts/blind_review.py'
spec = importlib.util.spec_from_file_location('council_modes', SCRIPT)
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class CouncilModeTests(unittest.TestCase):
    def data(self, candidates=5, judges=5):
        return {'question': 'Which plan meets the checked baseline?',
                'rubric': ['Match evidence v7; distinguish uncertainty from vote strength'],
                'evidence': ['baseline@fixture-v7: observed checks=5; not model truth'],
                'review_order': 'balanced',
                'candidates': [{'id': f'plan-{i}', 'text': f'Plan {i}: observed checks={i}',
                                'origin': 'declared-model'} for i in range(1, candidates + 1)],
                # Deliberately not alphabetic: serialized JSON sorts keys.
                'judges': [{'id': f'fresh-{i}', 'origin': 'declared-model'} for i in reversed(range(judges))]}

    def judgments(self, directory):
        rows = []
        for path in sorted((directory / 'packets').glob('*.json')):
            packet = review.read_json(path)
            responses = sorted(packet['responses'], key=lambda row: int(row['text'].split('checks=')[1]), reverse=True)
            rows.append({'packet_id': packet['packet_id'], 'ranking': [[row['label']] for row in responses],
                         'reasons': {row['label']: {'supported': [row['text']],
                             'unresolved': ['Fixture only, not real model evidence']} for row in responses},
                         'evidence_gaps': ['No live outcome measurement']})
        return rows

    def test_five_by_five_balances_positions_and_preserves_all_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp).resolve() / 'review'; data = self.data()
            prepared = review.prepare(data, out, seed=19)
            self.assertEqual(prepared['packets'], 5)
            manifest = review.validated_manifest(out)
            self.assertEqual(manifest['version'], 2)
            self.assertEqual(manifest['source_sha256'], review.digest(data))
            for path in (out / 'packets').glob('*.json'):
                packet = review.read_json(path)
                for key in ('question', 'rubric', 'evidence'):
                    self.assertEqual(packet[key], data[key])
                self.assertEqual({r['text'] for r in packet['responses']}, {r['text'] for r in data['candidates']})
                self.assertNotIn('declared-model', path.read_text())
                self.assertNotIn('fresh-', path.read_text())
                self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(out.stat().st_mode & 0o777, 0o700)
            result = review.summarize(out, self.judgments(out))
            self.assertEqual(result['state'], 'complete')
            self.assertEqual(result['review_order'], 'balanced')
            self.assertEqual(result['mean_ranks']['plan-5'], 1)
            self.assertEqual(result['mean_ranks']['plan-1'], 5)
            coverage = result['order_coverage']
            self.assertTrue(coverage['planned_positions_balanced'])
            self.assertTrue(coverage['received_positions_balanced'])
            for counts in coverage['received_candidate_position_counts'].values():
                self.assertEqual(counts, [1] * 5)
            self.assertEqual(coverage['within_reviewer_reversal'], 'not_performed')
            self.assertEqual(coverage['reversal_comparisons_completed'], 0)
            self.assertEqual(result['order_disagreements'], [])
            self.assertNotIn('winner', result)
            self.assertEqual(len(result['judgments']), 5)
            self.assertTrue(all(row['evidence_gaps'] == ['No live outcome measurement'] for row in result['judgments']))

    def test_missing_review_reduces_actual_coverage_and_duplicates_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp).resolve() / 'review'; review.prepare(self.data(), out, seed=2)
            rows = self.judgments(out)
            result = review.summarize(out, rows[:-1])
            self.assertEqual(result['state'], 'incomplete')
            self.assertEqual(result['missing_packets'], [rows[-1]['packet_id']])
            self.assertTrue(result['order_coverage']['planned_positions_balanced'])
            self.assertFalse(result['order_coverage']['received_positions_balanced'])
            self.assertTrue(all(sum(v) == 4 for v in result['order_coverage']['received_candidate_position_counts'].values()))
            self.assertEqual(result['order_coverage']['within_reviewer_reversal'], 'not_performed')
            with self.assertRaisesRegex(ValueError, 'Duplicate'):
                review.summarize(out, rows + rows[:1])
            wrong = copy.deepcopy(rows); wrong[0]['packet_id'] = 'p999'
            with self.assertRaisesRegex(ValueError, 'unknown'):
                review.summarize(out, wrong)

    def test_partial_position_design_does_not_claim_balance(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp).resolve() / 'review'; review.prepare(self.data(judges=3), out)
            result = review.summarize(out, self.judgments(out))
            self.assertEqual(result['state'], 'complete')
            self.assertFalse(result['order_coverage']['planned_positions_balanced'])
            self.assertFalse(result['order_coverage']['received_positions_balanced'])

    def test_role_limits_duplicates_and_unknown_modes_fail_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            bad = []
            paired = self.data(); paired['review_order'] = 'paired'; bad.append(paired)
            too_many = self.data(judges=6); bad.append(too_many)
            duplicate = self.data(); duplicate['judges'][1]['id'] = duplicate['judges'][0]['id']; bad.append(duplicate)
            duplicate = self.data(); duplicate['candidates'][1]['id'] = duplicate['candidates'][0]['id']; bad.append(duplicate)
            unknown = self.data(); unknown['review_order'] = 'random'; bad.append(unknown)
            unknown = self.data(); unknown['sources'] = ['must not disappear']; bad.append(unknown)
            for i, data in enumerate(bad):
                target = base / str(i)
                with self.assertRaises(ValueError): review.prepare(data, target)
                self.assertFalse(target.exists())

    def test_manifest_mode_roster_and_round_tampering_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp).resolve() / 'review'; review.prepare(self.data(), out)
            path = out / 'manifest.json'; original = review.read_json(path)
            mutations = []
            for key, value in [('version', 1), ('version', True), ('review_order', 'paired')]:
                bad = copy.deepcopy(original); bad[key] = value; mutations.append(bad)
            bad = copy.deepcopy(original); del bad['review_order']; mutations.append(bad)
            bad = copy.deepcopy(original); del bad['judges']['fresh-0']; mutations.append(bad)
            bad = copy.deepcopy(original); bad['packets']['p001']['judge'] = 'unregistered'; mutations.append(bad)
            bad = copy.deepcopy(original); bad['packets']['p002']['judge'] = bad['packets']['p001']['judge']; mutations.append(bad)
            bad = copy.deepcopy(original); bad['packets']['p001']['round'] = 'forward'; mutations.append(bad)
            bad = copy.deepcopy(original); bad['packets']['p006'] = bad['packets'].pop('p005'); mutations.append(bad)
            for bad in mutations:
                path.write_text(json.dumps(bad))
                with self.assertRaises(ValueError): review.summarize(out, [])

    def test_balanced_rotation_and_packet_mode_are_verified_even_after_rehash(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp).resolve() / 'review'; review.prepare(self.data(), out)
            manifest_path = out / 'manifest.json'; original = review.read_json(manifest_path)
            packet_path = out / 'packets/p002.json'; packet = review.read_json(packet_path)
            first = review.read_json(out / 'packets/p001.json')
            # Coherent candidate/text rehash still cannot silently remove position rotation.
            changed = copy.deepcopy(packet); changed['responses'] = first['responses']
            bad = copy.deepcopy(original); bad['packets']['p002']['aliases'] = bad['packets']['p001']['aliases']
            bad['packets']['p002']['sha256'] = review.digest(changed)
            packet_path.write_text(json.dumps(changed)); manifest_path.write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError, 'rotate'): review.summarize(out, [])
            for value in (None, 'paired'):
                changed = copy.deepcopy(packet)
                if value is None: del changed['review_order']
                else: changed['review_order'] = value
                bad = copy.deepcopy(original); bad['packets']['p002']['sha256'] = review.digest(changed)
                packet_path.write_text(json.dumps(changed)); manifest_path.write_text(json.dumps(bad))
                with self.assertRaises(ValueError): review.summarize(out, [])

    def test_changed_context_missing_packet_and_duplicate_json_keys_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp).resolve() / 'review'; review.prepare(self.data(), out)
            packet_path = out / 'packets/p001.json'; original = packet_path.read_bytes()
            data = review.read_json(packet_path); data['evidence'] = ['replaced source']
            packet_path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, 'changed'): review.summarize(out, [])
            packet_path.unlink()
            with self.assertRaises(FileNotFoundError): review.summarize(out, [])
            packet_path.write_bytes(original)
            duplicate = Path(tmp).resolve() / 'duplicate.json'
            duplicate.write_text('{"judges":{"same":"one","same":"two"}}')
            with self.assertRaisesRegex(ValueError, 'Duplicate JSON'): review.read_json(duplicate)

    def test_default_paired_shape_and_explicit_paired_stay_version_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve(); data = self.data(candidates=3, judges=4)
            del data['review_order']
            for i in range(2):
                out = base / str(i); review.prepare(data, out, seed=2)
                manifest = review.validated_manifest(out)
                self.assertEqual(manifest['version'], 1); self.assertNotIn('review_order', manifest)
                self.assertEqual(len(manifest['packets']), 8)
                result = review.summarize(out, self.judgments(out))
                self.assertEqual(result['review_order'], 'paired')
                self.assertEqual(result['order_disagreements'], [])
                self.assertEqual(result['order_coverage']['within_reviewer_reversal'], 'complete')
                self.assertEqual(result['order_coverage']['reversal_comparisons_completed'], 4)
                bad = dict(manifest, review_order='balanced')
                (out / 'manifest.json').write_text(json.dumps(bad))
                with self.assertRaises(ValueError): review.summarize(out, [])
                data['review_order'] = 'paired'

    def test_preexisting_version_one_packet_fixture_is_still_accepted(self):
        # Hand-built historical schema, independent of the new prepare path.
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp).resolve() / 'saved'; (out / 'packets').mkdir(parents=True)
            context = {'question': 'Saved question', 'rubric': ['Saved rubric'], 'evidence': []}
            candidates = {'old-a': 'Plan 1: observed checks=1', 'old-b': 'Plan 2: observed checks=2'}
            manifest = {'version': 1, 'source_sha256': 'a' * 64, 'context_sha256': review.digest(context),
                        'candidates': {k: {'origin_declared': 'unknown', 'text_sha256': hashlib.sha256(v.encode()).hexdigest()} for k, v in candidates.items()},
                        'judges': {'old-critic': 'unknown'}, 'packets': {}}
            for i, (round_name, ids) in enumerate([('forward', ['old-a', 'old-b']), ('reverse', ['old-b', 'old-a'])], 1):
                packet_id = f'p{i:03}'; aliases = dict(zip(['R1', 'R2'], ids))
                packet = {'packet_id': packet_id, **context, 'instructions': 'Saved critic instructions',
                          'responses': [{'label': label, 'text': candidates[key]} for label, key in aliases.items()]}
                manifest['packets'][packet_id] = {'aliases': aliases, 'judge': 'old-critic', 'round': round_name, 'sha256': review.digest(packet)}
                (out / 'packets' / (packet_id + '.json')).write_bytes(review.encoded(packet))
            (out / 'manifest.json').write_bytes(review.encoded(manifest))
            result = review.summarize(out, self.judgments(out))
            self.assertEqual(result['state'], 'complete')
            self.assertEqual(result['mean_ranks'], {'old-a': 2, 'old-b': 1})
            self.assertEqual(result['order_coverage']['within_reviewer_reversal'], 'complete')

    def test_balanced_cli_round_and_exclusive_report_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve(); source = base / 'input.json'; source.write_text(json.dumps(self.data()))
            out = base / 'review'; reviews = base / 'reviews.json'; report = base / 'report.json'
            subprocess.run([sys.executable, str(SCRIPT), 'prepare', str(source), str(out)], check=True, capture_output=True)
            reviews.write_text(json.dumps(self.judgments(out)))
            args = [sys.executable, str(SCRIPT), 'summarize', str(out), str(reviews), str(report)]
            subprocess.run(args, check=True, capture_output=True)
            saved = report.read_bytes(); result = json.loads(saved)
            self.assertEqual(result['state'], 'complete')
            self.assertTrue(result['order_coverage']['received_positions_balanced'])
            duplicate = subprocess.run(args, capture_output=True)
            self.assertEqual(duplicate.returncode, 2); self.assertEqual(report.read_bytes(), saved)


if __name__ == '__main__':
    unittest.main()
