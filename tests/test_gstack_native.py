"""Replay the real pinned Gstack source; never acquire or execute upstream code.

Set NSTACK_GSTACK_SOURCE to an existing exact-pin cache for offline clone checks.
The source-dependent checks skip explicitly when that source is unavailable.
"""
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'lib')]
from skill_build import materialize
from closure import validate

PIN = '622e8b1f76d293b647eca7b33d9dd060ab618b21'
DEFAULT_SOURCE = pathlib.Path.home() / 'Library/Application Support/nstack/sources/garrytan--gstack' / PIN


class NativeGstackPinnedReplay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = pathlib.Path(os.environ.get('NSTACK_GSTACK_SOURCE', DEFAULT_SOURCE))
        try:
            receipt = json.loads((cls.source / '.nstack-source.json').read_text())
        except (OSError, ValueError) as exc:
            raise unittest.SkipTest('Exact pinned offline Gstack source unavailable; no network fetch: ' + type(exc).__name__)
        if receipt.get('repository') != 'garrytan/gstack' or receipt.get('revision') != PIN:
            raise AssertionError('Wrong Gstack source identity')
        files = {str(p.relative_to(cls.source)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in cls.source.rglob('*') if p.is_file() and p.name != '.nstack-source.json'}
        if files != receipt['files']:
            raise AssertionError('Pinned source cache differs from its receipt')
        cls.temp = tempfile.TemporaryDirectory(prefix='nstack-gstack-test-')
        cls.addClassCleanup(cls.temp.cleanup)
        registry = json.loads((ROOT / 'registry/manifest.json').read_text())
        component = next(c for c in registry['components'] if c['id'] == 'P006')
        cls.outputs = {}
        for spec in registry['skills']:
            if spec['candidate_id'] != 'P006' or spec['delivery'] != 'narrow-patched leaf':
                continue
            name = pathlib.Path(spec['source_path']).parent.name
            out = pathlib.Path(cls.temp.name) / name
            out.mkdir()
            entry = materialize(cls.source, out, spec, component, registry)
            cls.outputs[name] = (out, out / entry / 'SKILL.md')

    def test_all_four_real_bundles_retain_operative_support_and_exact_policy_archive(self):
        self.assertEqual(set(self.outputs), {'qa', 'review', 'plan-eng-review', 'office-hours'})
        for name, (out, entry) in self.outputs.items():
            with self.subTest(name=name):
                validate(out)
                policy = out / 'source/docs/review-policy.md'
                if policy.exists():
                    self.assertEqual(policy.with_name('review-policy.upstream-reference.txt').read_bytes(),
                                     (self.source / 'docs/review-policy.md').read_bytes())
                    self.assertIn('## The blocking floor', policy.read_text())
                    self.assertIn('## Two checklist rules with ids', policy.read_text())
                self.assertTrue(entry.is_file())
        review_root = self.outputs['review'][0] / 'source'
        for rel in ['qa/sections/exploratory.md', 'qa/sections/scope.md',
                    'qa/templates/functional-report-template.md', 'qa/templates/qa-report-template.md',
                    'review/checklist.md', 'review/sections/review-army.md',
                    'plan-eng-review/sections/checklist.md', 'plan-eng-review/sections/review-sections.md',
                    'office-hours/sections/phase-2a-startup-diagnostic.md',
                    'office-hours/sections/phase-2b-builder-brainstorm.md']:
            self.assertTrue((review_root / rel).is_file(), rel)

    def test_operative_markdown_has_no_retired_executable_or_receipt_dependency(self):
        bad = re.compile(r'\$B\b|\$D\b|ASIDE_DIR|NEEDS_ASIDE|ASIDE_NOT_RUNNING|command -v aside|'
                         r'review_binding|snapshot_covered_paths|FIX_BASE|REVIEW_START|PASS_START|'
                         r'sharedLibsFingerprint|canReuseSharedLibsAdvisory|lib/review-evidence\.ts|'
                         r'--start review|\.claude/skills/gstack|the selected local support path|'
                         r'the corresponding documented native operation|EVIDENCE_TOOL|DEADLINE_TOOL|'
                         r'PROFILE_READ|PRIOR_SESSION_COUNT|SESSION_TIER|IMPECCABLE_READY')
        for name, (out, entry) in self.outputs.items():
            for file in out.rglob('*.md'):
                with self.subTest(name=name, file=str(file.relative_to(out))):
                    self.assertIsNone(bad.search(file.read_text()), str(file))
        office = self.outputs['office-hours'][1].read_text()
        self.assertNotIn('captured secret', office)
        self.assertNotIn('One explicit question before any browsing', office)
        self.assertNotIn('Download the connected native browser', office)

    def test_domain_taxonomies_and_report_templates_survive_controller_removal(self):
        review_root = self.outputs['review'][0] / 'source'
        gates = (review_root / 'review/gate-integrity.md').read_text()
        original = (self.source / 'review/gate-integrity.md').read_text()
        pattern = r'(?m)^### ((?:RH|PL)-[0-9]+)'
        self.assertEqual(re.findall(pattern, gates), re.findall(pattern, original))
        patterns = (review_root / 'qa/sections/qa-patterns.md').read_text()
        source_patterns = (self.source / 'qa/sections/qa-patterns.md').read_text()
        a = '## Health Score Rubric'
        b = '## Framework-Specific Guidance'
        self.assertEqual(patterns[patterns.index(a):patterns.index(b)],
                         source_patterns[source_patterns.index(a):source_patterns.index(b)])
        for method in ['system-functional', 'scope']:
            text = (review_root / f'qa/sections/{method}.md').read_text()
            source_text = (self.source / f'qa/sections/{method}.md').read_text()
            self.assertEqual(re.findall(r'(?m)^## .+$', text),
                             re.findall(r'(?m)^## .+$', source_text))
        self.assertIn('| Duplicates/idempotency |',
                      (review_root / 'qa/sections/system-functional.md').read_text())
        policy = (review_root / 'docs/review-policy.md').read_text()
        for risk in ['money', 'gate', 'auth', 'secret']:
            self.assertIn('| ' + risk + ' |', policy)
        for template in ['functional-report-template.md', 'qa-report-template.md']:
            self.assertTrue((review_root / 'qa/templates' / template).is_file())

    def test_installed_entry_aliases_resolve_imperative_support_and_specialist_graph(self):
        # Simulate the actual publisher layout with exposed natural-name symlinks.
        # A link-only Markdown validator did not catch the old inline ETHOS read.
        exposed = pathlib.Path(self.temp.name) / 'exposed'
        exposed.mkdir(exist_ok=True)
        required = {
            'review': ['checklist.md', 'greptile-triage.md', 'gate-integrity.md',
                       'sections/plan-completion.md', 'sections/review-army.md',
                       'sections/adversarial.md', 'sections/shared-code-reuse.md',
                       '../qa/sections/exploratory.md', '../qa/sections/scope.md'],
            'qa': ['sections/scope.md', 'sections/browser-setup.md',
                   'sections/test-bootstrap.md', 'sections/exploratory.md',
                   'sections/browser-verify.md', 'sections/system-functional.md',
                   'templates/functional-report-template.md', 'templates/qa-report-template.md'],
            'office-hours': ['sections/phase-2a-startup-diagnostic.md',
                             'sections/phase-2b-builder-brainstorm.md',
                             'sections/second-opinion.md', 'sections/visual-design.md',
                             'sections/design-and-handoff.md'],
            'plan-eng-review': ['sections/review-sections.md', 'sections/checklist.md'],
        }
        for name, (out, entry) in self.outputs.items():
            alias = exposed / ('gstack-' + name)
            alias.symlink_to(entry.parent)
            for relative in required[name]:
                with self.subTest(name=name, relative=relative):
                    self.assertTrue((alias / relative).is_file())
                    self.assertTrue((alias / relative).resolve().is_relative_to(out.resolve()))
            # Every retained copied Review Army must be independently complete.
            army = out / 'source/review/sections/review-army.md'
            for relative in re.findall(r'\]\((\.\./specialists/[^)]+)\)', army.read_text()):
                self.assertTrue((army.parent / relative).is_file(), str(army) + relative)
            for match in re.finditer(r'See `([^`]+\.md)`', entry.read_text()):
                self.assertTrue((entry.parent / match[1]).is_file(), str(entry) + match[1])

    def test_required_dispatch_decision_and_output_edges_have_definitions(self):
        review = self.outputs['review'][1].read_text()
        headings = re.findall(r'(?m)^#{2,4} (.+)$', review)
        for step in ['4.8', '5.8']:
            self.assertTrue(any(h.startswith('Step ' + step + ':') for h in headings))
        plan_root = self.outputs['plan-eng-review'][0] / 'source/plan-eng-review'
        sections = (plan_root / 'sections/review-sections.md').read_text()
        headings = set(re.findall(r'(?m)^#{2,4} (.+)$', sections))
        for required in ['Decision procedure', 'Review record and write policy',
                         'NOT in scope', 'What already exists', 'Diagrams', 'Failure modes',
                         'Worktree parallelization strategy', 'Implementation Tasks',
                         'Unresolved decisions', 'Completion summary', 'Required outputs']:
            self.assertIn(required, headings)
        # Preserved substantive task and dependency shapes, not orphan output names.
        tasks = sections[sections.index('## Implementation Tasks'):sections.index('### Unresolved decisions')]
        for field in ['Surfaced by:', 'Files:', 'Depends on:', 'Verify:']:
            self.assertIn(field, tasks)
        self.assertIn('| Step | Modules touched | Depends on |', sections)
        self.assertIn('silent failure', sections)
        self.assertNotIn('Outside Voice and outputs', self.outputs['plan-eng-review'][1].read_text())

    def test_each_mutation_and_reply_step_respects_actual_operation_authority(self):
        review = self.outputs['review'][1].read_text()
        for start, end in [('### Step 5b:', '### Step 5c:'),
                           ('### Step 5d:', '### Verification of claims')]:
            step = review[review.index(start):review.index(end)]
            self.assertRegex(step, r'(?i)review.only')
            self.assertRegex(step, r'(?i)authori(?:[sz]ed|[sz]ation|ty)')
        comments = review[review.index('### Review bot comment resolution'):review.index('## Step 5.8:')]
        for number, following in [('1.', '2.'), ('2.', '3.'), ('3.', '4.')]:
            segment = comments[comments.index(number + ' **'):comments.index(following + ' **')]
            self.assertIn('specific existing reply authority', segment)
        branch = review[review.index('## Step 1:'):review.index('## Step 1.5:')]
        for scope in ['staged', 'unstaged', 'untracked']:
            self.assertIn(scope, branch)
        self.assertNotRegex(branch, r'If on the base branch.*?stop')

    def test_browser_and_artifact_methods_bind_inputs_outputs_and_review_identity(self):
        qa = self.outputs['qa'][1].read_text()
        report = qa[qa.index('## Phase 10: Report'):qa.index('## Phase 11:')]
        self.assertIn('REPORT_DIR selected in Setup', report)
        self.assertNotIn('PROJECT_DIR', report)
        patterns = (self.outputs['qa'][0] / 'source/qa/sections/qa-patterns.md').read_text()
        self.assertNotRegex(patterns, r'\bpg\.(?:fill|getByRole|waitForSelector|waitForURL)\(')
        self.assertNotIn('use the read script', patterns)
        self.assertIn('Respect native denials', patterns)
        office_root = self.outputs['office-hours'][0] / 'source/office-hours'
        sketch = (office_root / 'sections/visual-design.md').read_text()
        self.assertIn('owning task', sketch)
        self.assertNotIn('PROJECT_DIR', sketch)
        self.assertNotIn('projects/<slug>', sketch)
        handoff = (office_root / 'sections/design-and-handoff.md').read_text()
        self.assertNotIn('## Cross-Model Perspective', handoff)
        self.assertEqual(handoff.count('## Independent Perspective'), 2)
        self.assertIn('distinct identities were observed', handoff)

    def test_rebuilding_at_different_absolute_roots_keeps_all_bundle_bytes_identical(self):
        registry = json.loads((ROOT / 'registry/manifest.json').read_text())
        component = next(c for c in registry['components'] if c['id'] == 'P006')
        for spec in registry['skills']:
            if spec['candidate_id'] != 'P006' or spec['delivery'] != 'narrow-patched leaf':
                continue
            name = pathlib.Path(spec['source_path']).parent.name
            first = self.outputs[name][0]
            # Resolve macOS /var -> /private/var too, exercising closure's resolved
            # support paths against the initially unresolved absolute builder root.
            second = (pathlib.Path(self.temp.name) / 'second-location' / name).resolve()
            second.mkdir(parents=True)
            materialize(self.source, second, spec, component, registry)
            files = lambda root: {str(p.relative_to(root)): p.read_bytes()
                                  for p in root.rglob('*') if p.is_file()}
            self.assertEqual(files(first), files(second), name)
            testing = first / 'source/review/specialists/testing.md'
            self.assertIn('https://github.com/garrytan/gstack/blob/' + PIN +
                          '/docs/test-value-bar.md#caller-check-unavailable', testing.read_text())

    def test_review_callers_preserve_parent_resolved_baseline_without_assumed_remote(self):
        out, entry = self.outputs['review']
        for file in [entry, out / 'source/review/sections/plan-completion.md',
                     out / 'source/review/greptile-triage.md']:
            text = file.read_text()
            self.assertNotIn('origin/<base>', text)
            self.assertNotIn('DIFF_BASE=$(git merge-base', text)
            self.assertRegex(text, r"(?:parent-resolved|Step 1's recorded)")
        self.assertNotIn('Operational Self-Improvement', entry.read_text())

    def test_remaining_shell_examples_parse_after_binding_documented_placeholders(self):
        for name, (out, entry) in self.outputs.items():
            for file in out.rglob('*.md'):
                text = file.read_text()
                for match in re.finditer(r'(?ms)^[ \t]*```(bash|sh|zsh)[ \t]*\n(.*?)^[ \t]*```', text):
                    # These are syntax checks only, never execution of target code.
                    code = match[2]
                    code = re.sub(r'<(?:base|prior-review-commit|only-verified-source-and-regression-files)>', 'BASE_REVISION', code)
                    shell = shutil.which('zsh') if match[1] == 'zsh' else shutil.which('bash')
                    if not shell:
                        self.fail('Required syntax checker unavailable: ' + match[1])
                    result = subprocess.run([shell, '-n'], input=code, text=True, capture_output=True)
                    self.assertEqual(result.returncode, 0, f'{name}/{file.relative_to(out)}: {result.stderr}')
                    self.assertNotIn('Use task-local native evidence;', code)
                    self.assertNotIn('Record the verified diff and checks.', code)

    def test_source_based_checks_do_not_promote_existence_to_behavior_or_authorize_commits(self):
        review = self.outputs['review'][0] / 'source/review/sections/plan-completion.md'
        text = review.read_text()
        self.assertNotIn('File exists → DONE', text)
        self.assertNotIn('MUST be classified DONE or NOT DONE based on', text)
        qa = self.outputs['qa'][1].read_text()
        self.assertNotIn('Commit each verified fix', qa)
        self.assertNotIn('git add <only-verified-source-and-regression-files>', qa)


if __name__ == '__main__':
    unittest.main()
