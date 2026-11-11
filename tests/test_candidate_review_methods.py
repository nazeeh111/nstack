"""Compare domain methods with exact offline upstream sources, without runtimes."""
import json
import pathlib
import runpy
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'lib'))
import patch_gstack_ranges
import patch_prospecting

CACHE = pathlib.Path.home() / 'Library/Application Support/nstack/sources'


class CandidateReviewMethodConservation(unittest.TestCase):
    def source(self, repository, revision):
        root = CACHE / repository.replace('/', '--') / revision
        if not (root / '.nstack-source.json').is_file():
            self.skipTest('Exact offline source unavailable; no network acquisition')
        receipt = json.loads((root / '.nstack-source.json').read_text())
        self.assertEqual((receipt['repository'], receipt['revision']), (repository, revision))
        return root

    def marketing(self):
        return self.source('coreyhaines31/marketingskills', '88c79f6528a9347420e57ceb1fff9a60de651768')

    def test_controller_removal_keeps_complete_search_reuse_and_root_cause_method(self):
        source = self.source('garrytan/gstack', '622e8b1f76d293b647eca7b33d9dd060ab618b21')
        for name in ('office-hours', 'plan-eng-review'):
            file = source / name / 'SKILL.md'
            raw = file.read_text()
            method = raw[raw.index('## Search Before Building\n'):raw.index('**Eureka:**')]
            active = patch_gstack_ranges.patch(raw, file)
            self.assertEqual(active.count(method), 1)
            self.assertNotIn('## Telemetry', active)

    def test_demand_scoring_preserves_exact_formula_weights_bands_and_date_caution(self):
        rel = patch_prospecting.FILES[2]
        raw = (self.marketing() / rel).read_text()
        active = patch_prospecting.port(rel, raw)
        method = raw[raw.index('## Step 4'):raw.index('### Prospect stages')]
        self.assertIn(method, active)
        self.assertIn('**Seven-day manual outreach plan**', active)
        self.assertIn('target three conversations and one design-partner commitment', active)
        self.assertIn('separately authorized actions', active)
        self.assertNotIn('project-calibrated criteria', active)

    def test_draft_sequences_and_benchmark_navigation_survive_without_provider_effects(self):
        rel = patch_prospecting.FILES[1]
        raw = (self.marketing() / rel).read_text()
        active = patch_prospecting.port(rel, raw)
        for line in raw[raw.index('## Follow-Up Sequences'):raw.index('## Before You Send')].splitlines():
            if '](' not in line:
                self.assertIn(line, active)
        self.assertIn('## Data & Benchmarks', active)
        self.assertIn('/88c79f6528a9347420e57ceb1fff9a60de651768/skills/cold-email/references/benchmarks.md)', active)
        self.assertNotIn('## Before You Send', active)
        self.assertNotIn('## Tool Integrations', active)
        self.assertIn('prepares only explicitly requested drafts', active)
        self.assertIn('No provider setup, enrichment, sending', active)

    def test_win_loss_and_personalization_keep_source_heuristics(self):
        source = self.marketing()
        rel = patch_prospecting.FILES[7]
        raw = (source / rel).read_text()
        active = patch_prospecting.port(rel, raw)
        for prefix in ('Ask within 2-4 weeks', '- **Under ~5 deals'):
            self.assertIn(next(line for line in raw.splitlines() if line.startswith(prefix)), active)
        rel = patch_prospecting.FILES[4]
        active = patch_prospecting.port(rel, (source / rel).read_text())
        self.assertIn('## The 3-Minute Personalization System', active)
        self.assertIn('~5% lift.', active)
        self.assertIn('not independently validated predictions or guarantees', active)

    def test_benchmark_source_navigation_rejects_mutable_wrong_repo_and_other_dependencies(self):
        checker = runpy.run_path(str(ROOT / 'tests/check_p343_closure.py'))
        allowed = checker['source_locator_allowed']
        leaf = 'skills/cold-email/SKILL.md'
        exact = checker['SOURCE_PREFIX'] + 'benchmarks.md'
        self.assertTrue(allowed(leaf, exact))
        for target in (exact.replace('88c79f6528a9347420e57ceb1fff9a60de651768', 'main'),
                       exact.replace('coreyhaines31/marketingskills', 'other/marketingskills'),
                       exact + '?raw=true',
                       checker['SOURCE_PREFIX'] + 'sourcing-and-enrichment.md',
                       'https://example.com/benchmarks.md'):
            with self.subTest(target=target):
                self.assertFalse(allowed(leaf, target))
        self.assertFalse(allowed('skills/prospecting/SKILL.md', exact))


if __name__ == '__main__':
    unittest.main()
