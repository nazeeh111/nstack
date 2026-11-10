"""The behavioral graders must reject false-success controls without model calls."""
import json
from pathlib import Path
import subprocess
import sys
import unittest


class AdaptiveRoutingControls(unittest.TestCase):
    def test_independent_graders_accept_correct_and_reject_wrong_artifacts(self):
        script = Path(__file__).resolve().parents[1] / 'evals/01/selftest.py'
        run = subprocess.run([sys.executable, str(script)], check=True,
                             capture_output=True, text=True, timeout=30)
        result = json.loads(run.stdout)
        self.assertEqual(result['positive_controls'], 6)
        self.assertEqual(result['negative_controls'], 6)
        self.assertTrue(all(r['valid_artifact_accepted'] and r['plausible_wrong_artifact_rejected']
                            for r in result['results']))
