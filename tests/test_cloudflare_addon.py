"""Pinned closure and detached offline validator contracts; no audit target."""
import hashlib
import difflib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import quote, unquote

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'lib')]
import native_setup as native

ADDON = ROOT / 'addons/cloudflare-security-audit'
PIN = 'c1c8a8c1471069fb0e188eeaff69b8e8db6564a8'
# Independent aggregate of source-path/hash pairs read from the Git-verified pin.
UPSTREAM_IDENTITY = '13d720708a4753008f7fd64d4ec311333c2141f337267d36dbe03f15a3e6a8fe'
NODE = shutil.which('node')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def files(root):
    return {str(p.relative_to(root)): sha(p.read_bytes()) for p in root.rglob('*') if p.is_file()}


class CloudflareAddonTests(unittest.TestCase):
    def test_complete_pinned_closure_license_and_one_active_entry(self):
        receipt = json.loads((ADDON / 'SOURCE.json').read_text())
        self.assertEqual(receipt['repository'], 'cloudflare/security-audit-skill')
        self.assertEqual(receipt['revision'], PIN)
        self.assertEqual(receipt['license'], 'MIT')
        upstream = receipt['upstream_files']
        self.assertEqual(len(upstream), 21)
        original = {entry['source_path']: entry['sha256'] for entry in upstream.values()}
        identity = sha(json.dumps(original, sort_keys=True, separators=(',', ':')).encode())
        self.assertEqual(identity, UPSTREAM_IDENTITY)
        for relative, entry in upstream.items():
            self.assertEqual(sha((ADDON / relative).read_bytes()), entry['sha256'], relative)
        self.assertEqual({str(p.relative_to(ADDON)) for p in ADDON.rglob('SKILL.md')}, {'SKILL.md'})
        self.assertFalse(any(p.is_symlink() for p in ADDON.rglob('*')))
        self.assertEqual(set(files(ADDON)), set(upstream) | {'SKILL.md', 'SOURCE.json', 'PORT.patch'})
        self.assertEqual(sha((ADDON / 'PORT.patch').read_bytes()), receipt['port_patch_sha256'])
        self.assertIn('Copyright (c) 2025-2026 Cloudflare, Inc.', (ADDON / 'LICENSE').read_text())
        original_entry = upstream['upstream/ORIGINAL-SKILL.md']
        self.assertEqual(original_entry['source_path'], 'skills/security-audit/SKILL.md')
        self.assertTrue(receipt['modifications'])
        self.assertNotIn('/Users/', json.dumps(receipt))
        self.assertNotIn('/private/tmp/', json.dumps(receipt))

    def test_active_method_preserves_upstream_except_name_and_support_bindings(self):
        original = (ADDON / 'upstream/ORIGINAL-SKILL.md').read_text()
        active = (ADDON / 'SKILL.md').read_text()
        restored = active.replace('name: cloudflare-security-audit\n', 'name: security-audit\n', 1)
        restored = restored.replace('**Skill directory**: the absolute `upstream/` subdirectory beside this active `SKILL.md`, containing the retained companions, schema and validators.', '**Skill directory**: the absolute directory containing this `SKILL.md`.')
        restored = restored.replace('](upstream/', '](')
        self.assertEqual(restored, original)
        expected = ''.join(difflib.unified_diff(original.splitlines(keepends=True), active.splitlines(keepends=True), fromfile='upstream/skills/security-audit/SKILL.md', tofile='active/SKILL.md'))
        self.assertEqual((ADDON / 'PORT.patch').read_text(), expected)
        self.assertIn('Reserve the four baseline reconnaissance calls', active)
        self.assertIn('budget_cannot_fund_reconnaissance_and_reserves', active)

    def test_all_relative_markdown_references_stay_in_retained_bundle(self):
        for path in ADDON.rglob('*.md'):
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if '://' in target or target.startswith('#'):
                    continue
                relative = unquote(target.split('#', 1)[0])
                resolved = (path.parent / relative).resolve()
                self.assertTrue(resolved.is_relative_to(ADDON.resolve()), (path, target))
                self.assertTrue(resolved.is_file(), (path, target))

    @unittest.skipUnless(NODE, 'Existing Node runtime required; no installer is used')
    def test_detached_native_bundle_preserves_inputs_and_enforces_verdict_and_ownership(self):
        with tempfile.TemporaryDirectory(prefix='cloudflare-addon-', dir='/private/tmp') as temp:
            base = Path(temp)
            release, index = native.prepare(base / 'state', [], ['cloudflare-security-audit'])
            repeated, rows = native.prepare(base / 'state', [], ['cloudflare-security-audit'])
            self.assertEqual((release, index), (repeated, rows))
            entry = release / 'skills/cloudflare-security-audit'
            self.assertEqual(Path(index[0]['skill_path']).read_bytes(), (ADDON / 'SKILL.md').read_bytes())
            before = files(release)
            scratch = base / 'synthetic'
            scratch.mkdir()
            (scratch / 'home').mkdir()
            (scratch / 'tmp').mkdir()
            # Inherit no credential, provider, runtime-hook or user configuration variables.
            environment = {'PATH': str(Path(NODE).parent) + ':/usr/bin:/bin',
                           'HOME': str(scratch / 'home'), 'TMPDIR': str(scratch / 'tmp'), 'TZ': 'UTC'}

            def validate(name, data, succeeds):
                source = scratch / name
                source.write_text(json.dumps(data))
                raw = source.read_bytes()
                validator = 'validate-findings.cjs' if name.startswith('findings') else 'validate-coverage-ledger.cjs'
                result = subprocess.run([NODE, '--max-old-space-size=128', str(entry / 'upstream' / validator), str(source)],
                                        cwd=scratch, env=environment, capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0 if succeeds else 1, result.stdout + result.stderr)
                self.assertEqual(source.read_bytes(), raw)
                self.assertNotIn('Stack trace', result.stderr)
                return result

            blocked = {'verdict': 'needs_validation', 'fingerprint': 'src-handler-boundary', 'title': 'Synthetic blocked lead',
                       'description': 'A synthetic boundary requires a controlled local test.',
                       'claimed_root_cause': 'The fixture lacks an observed result.',
                       'trace': [{'kind': 'entrypoint', 'file': 'src/fixture.js', 'line': 1, 'scope': 'handler',
                                  'description': 'Synthetic source path only.'}],
                       'evidence': [{'file': 'src/fixture.js', 'line': 1, 'description': 'Synthetic source observation.'}],
                       'blockers': ['Required OS execution sandbox is unavailable.'],
                       'validation_plan': {'local': 'Use a dummy fixture after every sandbox control is available.'}}
            validate('findings-valid.json', [blocked], True)
            invalid = dict(blocked, severity={'overall_severity': 'high'})
            validate('findings-invalid.json', [invalid], False)
            refs = {'surface': 'src/fixture.js#entry', 'boundary': 'src/fixture.js#owner',
                    'subsystem': 'src', 'attack_class': 'ATTACK-CLASSES.md#Access control'}
            coverage = {'coverage_id': '::'.join(quote(refs[key], safe='-._~') for key in refs),
                        'canonical_refs': refs, 'surface': 'Fixture entry', 'boundary': 'Fixture owner',
                        'subsystem': 'Fixture', 'attack_class': 'Access control', 'starting_paths': ['src/fixture.js'],
                        'ordinary_attack_class_block': 'ATTACK-CLASSES.md#Access control', 'selected_companion_blocks': [],
                        'excluded_blocks': [], 'prior_status': 'none', 'attempts': [], 'wave': 1, 'status': 'covered',
                        'agent_id': 'hunter-1', 'reviewed_paths': ['src/fixture.js'], 'local_checks': [{
                            'agent_id': 'hunter-1', 'reviewed_paths': ['src/fixture.js'], 'invariant': 'Synthetic ownership bound.',
                            'method': 'source', 'result': 'Source-only synthetic observation.', 'artifact': None}],
                        'result_fingerprints': [], 'unresolved': []}
            validate('ledger-valid.json', [coverage], True)
            wrong_owner = json.loads(json.dumps(coverage))
            wrong_owner['local_checks'][0].update(method='local', artifact='agents/other-owner/artifacts/result.txt')
            validate('ledger-wrong-owner.json', [wrong_owner], False)
            self.assertEqual(files(release), before)
            self.assertEqual(list((scratch / 'home').iterdir()), [])


if __name__ == '__main__':
    unittest.main()
