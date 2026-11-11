"""Full pinned ECC methods survive native bindings; no runner is executed."""
import hashlib
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'lib'))
import ecc_addon

SOURCE = Path(os.environ.get('NSTACK_TEST_ECC_SOURCE', str(
    Path.home() / 'Library/Application Support/nstack/sources/affaan-m--ECC' / ecc_addon.REVISION)))


@unittest.skipUnless(SOURCE.is_dir(), 'Acquire the exact pinned ECC source for offline fidelity checks')
class EccFidelity(unittest.TestCase):
    def definition(self, name):
        class SourceOnly:
            def acquire(self, repository, revision):
                assert repository == ecc_addon.REPOSITORY and revision == ecc_addon.REVISION
                return SOURCE
        return ecc_addon.definition(SourceOnly(), name)

    def test_complete_methods_frontmatter_and_exact_originals(self):
        for name in ecc_addon.DESCRIPTIONS:
            definition = self.definition(name)
            entry = f'skills/{name}/SKILL.md'
            original = (SOURCE / entry).read_bytes()
            self.assertEqual(definition['overrides'][f'skills/{name}/UPSTREAM_SKILL.md'], original)
            active = definition['overrides'][entry].decode()
            native_link = '\n> Native tools/paths and execution limits: read [NATIVE-BINDINGS.md](NATIVE-BINDINGS.md). The original method follows.\n'
            self.assertEqual(active.replace(native_link, '', 1),
                             original.decode().replace('Claude Code', 'active host').replace('CLAUDE.md', 'AGENTS.md').replace('Claude', 'active host'))
            for rel, (raw, _) in definition['frozen_files'].items():
                self.assertEqual(raw, (SOURCE / rel).read_bytes())
                self.assertEqual(hashlib.sha256(raw).hexdigest(), definition['provenance']['source_files'][rel])

    def test_original_edd_controls_and_both_onboarding_outputs(self):
        evaluation = self.definition('eval-harness')
        active = evaluation['overrides']['skills/eval-harness/SKILL.md'].decode()
        for original_rule in ('Run evals continuously during development', 'Typical target: pass@3 > 90%',
                              'Human review for security', 'Never fully automate security checks', 'Recommended thresholds:'):
            self.assertIn(original_rule, active)
        binding = evaluation['overrides']['skills/eval-harness/NATIVE-BINDINGS.md'].decode()
        self.assertIn('gate.isolation_required', binding)
        self.assertIn('keep it closed', binding)
        onboard = self.definition('codebase-onboarding')
        active = onboard['overrides']['skills/codebase-onboarding/SKILL.md'].decode()
        self.assertIn('Produce two outputs:', active)
        self.assertIn('Starter AGENTS.md', active)
        binding = onboard['overrides']['skills/codebase-onboarding/NATIVE-BINDINGS.md'].decode()
        self.assertIn('AGENTS.starter.md', binding)
        self.assertIn('preserve its bytes', binding)


if __name__ == '__main__':
    unittest.main()
