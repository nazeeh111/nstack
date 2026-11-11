"""Offline provenance, complete method support and non-executable skill closure."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT / 'addons/strix-security-testing'
PIN = '685bbc8138d35fc9fe378ac37ec0d9198b9c46a3'
# Independently recorded from the reviewed immutable Git source, not generated
# from the package under test. These also bind the original method inventory.
SOURCES = {
    'api-security-testing': 'bd04c90d87be2353ebefee33363af0818746345e25c80ed36f63fcdd2b25509c',
    'application-security-testing': 'b3041c800a9a1d34e04164c5f700b6d12bbc237f098d760c09ec076c92d2a654',
    'ci-security-scanning-with-strix': '57801a50398cde76a50452ea6943afd2bf0dddb9ed470dc5aedadcf698b4700d',
    'find-security-vulnerabilities-in-code': 'e7c25f1a0aea437d011d96dd306736b644597b07aa5a6dbc5588eefaab248e0a',
    'fix-security-vulnerabilities-with-strix': 'bb1b351fd60c91e4875207f3fe4f35774ff5194261a00aea9f4752e459f24a9f',
    'managed-pentesting-with-strix': '45e1432ea897e59e67a5102513a4b9aac7372a5666d68d620ee867bbfa8b290b',
    'owasp-top-10-testing': '02b1cbe60d40c44493309418c7824f1f681d9f32bf0299ca246892c46cb130af',
    'penetration-testing-with-strix': 'd70bc1c9fc5c4557ae072467731eed0ff755a25d3e3aff958dc7d4a1ab615915',
    'web-app-penetration-testing': '2e8df0b9233971c496d0c0c7660808fc717c08d4165455a0423229045389608a',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(package):
    """Validate the distributable bytes alone; never import/run Strix."""
    info = json.loads((package / 'SOURCE.json').read_text())
    if info['repository'] != 'usestrix/strix' or info['revision'] != PIN:
        raise ValueError('Source identity changed')
    files = {str(p.relative_to(package)): digest(p) for p in package.rglob('*')
             if p.is_file() and p.name != 'SOURCE.json'}
    if any(p.is_symlink() for p in package.rglob('*')):
        raise ValueError('Linked package file')
    if files != info['files']:
        raise ValueError('Package bytes or support closure changed')
    if sorted(str(p.relative_to(package)) for p in package.rglob('SKILL.md')) != ['SKILL.md']:
        raise ValueError('Unexpected discoverable skill')
    if info['license'] != 'Apache-2.0' or digest(package / 'LICENSE') != info['license_sha256']:
        raise ValueError('License changed')
    methods = info['consumer_methods']
    if len(methods) != len(SOURCES):
        raise ValueError('Missing/duplicate method')
    seen = set()
    for row in methods:
        source = Path(row['source_path'])
        name = source.parent.name
        if name in seen or row['source_path'] != f'skills/{name}/SKILL.md' or name not in SOURCES:
            raise ValueError('Unexpected/duplicate method')
        seen.add(name)
        if row['stored_original_path'] != f'originals/{name}.md' or row['adapted_reference_path'] != f'references/{name}.md':
            raise ValueError('Invalid method path')
        if row['source_sha256'] != SOURCES[name] or digest(package / row['stored_original_path']) != SOURCES[name]:
            raise ValueError('Original source changed')
        if digest(package / row['adapted_reference_path']) != row['adapted_reference_sha256']:
            raise ValueError('Adapted reference changed')
        if digest(package / row['adapted_reference_path']) != SOURCES[name]:
            raise ValueError('Original active method changed')
    if seen != set(SOURCES):
        raise ValueError('Incomplete methods')
    active = [package / 'SKILL.md', *sorted((package / 'references').glob('*.md'))]
    if len(active) != 10:
        raise ValueError('Missing/extra active reference')
    reached = set()
    for path in active + [package / 'SOURCE.md', package / 'NATIVE-BINDINGS.md']:
        for raw in re.findall(r'\[[^\]]+\]\(([^)]+)\)', path.read_text()):
            target = urlsplit(raw)
            if target.scheme:
                if target.scheme != 'https':
                    raise ValueError('Unexpected external link')
                continue
            dest = (path.parent / unquote(target.path)).resolve()
            if not dest.is_relative_to(package.resolve()) or not dest.is_file():
                raise ValueError('Broken/escaping support link')
            reached.add(dest)
    if not {p.resolve() for p in active[1:]}.issubset(reached):
        raise ValueError('Unreachable method reference')
    # Preserve every original technical example byte-for-byte. Their presence
    # is not account/runtime authority; a separate binding is required first.
    if info.get('native_bindings') != 'NATIVE-BINDINGS.md':
        raise ValueError('Missing native execution binding')
    if '[native host/runtime bindings](NATIVE-BINDINGS.md)' not in (package / 'SKILL.md').read_text():
        raise ValueError('Native binding is not routed before source methods')
    binding = (package / 'NATIVE-BINDINGS.md').read_text()
    if 'No credential-store/config discovery' not in binding or 'never incidental setup' not in binding:
        raise ValueError('Missing source-example authority boundary')
    # The authored router must not add its own account/payment instructions.
    if re.search(r'(?im)^\s*strix\s+cloud\s+(?:login|billing|tokens|integrations|schedules)\b',
                 (package / 'SKILL.md').read_text()):
        raise ValueError('Operative account/payment example added to router')
    if any(p.suffix in {'.py', '.sh', '.js', '.cjs', '.mjs'} for p in package.rglob('*')):
        raise ValueError('Unexpected executable/runtime in instruction package')
    raw = (package / 'SOURCE.json').read_text()
    if '/Users/' in raw or '/private/' in raw or 'private_source_cache' in raw:
        raise ValueError('Private path in portable provenance')
    return info


class StrixAddonTests(unittest.TestCase):
    def copy(self, directory):
        copy = Path(directory) / 'strix'
        shutil.copytree(ADDON, copy)
        return copy

    def test_exact_source_archives_license_and_complete_linked_methods(self):
        info = audit(ADDON)
        self.assertFalse(info['runtime_included'])
        self.assertEqual(info['upstream_notice_files'], [])
        self.assertIn('Copyright 2025 OmniSecure Inc.', (ADDON / 'LICENSE').read_text())

    def test_original_mutation_cannot_be_authorized_by_rewriting_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            copy = self.copy(directory)
            path = copy / 'originals/api-security-testing.md'
            path.write_text(path.read_text() + '\nChanged original\n')
            info = json.loads((copy / 'SOURCE.json').read_text())
            info['files']['originals/api-security-testing.md'] = digest(path)
            for row in info['consumer_methods']:
                if row['source_path'] == 'skills/api-security-testing/SKILL.md':
                    row['source_sha256'] = digest(path)
            (copy / 'SOURCE.json').write_text(json.dumps(info))
            with self.assertRaisesRegex(ValueError, 'Original source changed'):
                audit(copy)

    def test_missing_or_modified_support_is_detected(self):
        for mutation in ('remove', 'change'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                copy = self.copy(directory)
                path = copy / 'references/api-security-testing.md'
                path.unlink() if mutation == 'remove' else path.write_text('Changed reference')
                with self.assertRaisesRegex(ValueError, 'Package bytes or support closure changed'):
                    audit(copy)

    def test_active_original_cannot_be_condensed_even_after_rehashing_package(self):
        with tempfile.TemporaryDirectory() as directory:
            copy = self.copy(directory)
            path = copy / 'references/api-security-testing.md'
            path.write_text('# Generic API checklist instead of the original method\n')
            info = json.loads((copy / 'SOURCE.json').read_text())
            info['files']['references/api-security-testing.md'] = digest(path)
            for row in info['consumer_methods']:
                if row['source_path'] == 'skills/api-security-testing/SKILL.md':
                    row['adapted_reference_sha256'] = digest(path)
            (copy / 'SOURCE.json').write_text(json.dumps(info))
            with self.assertRaisesRegex(ValueError, 'Original active method changed'):
                audit(copy)

    def test_new_nested_entry_is_rejected_even_with_updated_file_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            copy = self.copy(directory)
            path = copy / 'originals/SKILL.md'
            path.write_text('Unintended extra discovery')
            info = json.loads((copy / 'SOURCE.json').read_text())
            info['files']['originals/SKILL.md'] = digest(path)
            (copy / 'SOURCE.json').write_text(json.dumps(info))
            with self.assertRaisesRegex(ValueError, 'Unexpected discoverable skill'):
                audit(copy)

    def test_broken_link_and_operative_cloud_example_are_rejected(self):
        for extra, expected in [('\n[Missing method](references/missing.md)', 'Broken/escaping'),
                                ('\n```bash\nstrix cloud billing topup --credits 20 --yes\n```\n', 'Operative')]:
            with self.subTest(expected=expected), tempfile.TemporaryDirectory() as directory:
                copy = self.copy(directory)
                path = copy / 'SKILL.md'
                path.write_text(path.read_text() + extra)
                info = json.loads((copy / 'SOURCE.json').read_text())
                info['files']['SKILL.md'] = digest(path)
                (copy / 'SOURCE.json').write_text(json.dumps(info))
                with self.assertRaisesRegex(ValueError, expected):
                    audit(copy)


if __name__ == '__main__':
    unittest.main()
