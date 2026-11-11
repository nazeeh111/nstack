"""Static scaffold compatibility checks, not an Obsidian rendering test.

The small evaluator covers only the documented filter expressions used by this
template. It fails on unfamiliar expressions rather than guessing app behavior.
"""
import pathlib
import re
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1] / 'templates/vault'


def properties(text):
    frontmatter = text.split('---', 2)[1]
    result = {}
    for line in frontmatter.strip().splitlines():
        key, value = line.split(':', 1)
        if key in result:
            raise AssertionError('Duplicate property: ' + key)
        result[key] = value.strip()
    return result


def selectors(base, view_name):
    global_block, views = base.split('views:\n', 1)
    expressions = []
    for line in global_block.splitlines():
        if line.strip().startswith('- '):
            expressions.append(line.strip()[2:].strip("'"))
    for view in views.split('  - type: ')[1:]:
        if '    name: ' + view_name + '\n' in view:
            match = re.search(r'^    filters: (.+)$', view, re.M)
            if not match:
                raise AssertionError('Expected an explicit state filter')
            return expressions + [match.group(1)], view
    raise AssertionError('Missing view: ' + view_name)


def included(path, text, expressions):
    props = properties(text)
    for expression in expressions:
        if expression == 'file.ext == "md"':
            match = path.suffix == '.md'
        elif expression == 'file.hasTag("knowledge")':
            tags = props.get('tags', '').strip('[]').split(',')
            match = 'knowledge' in [tag.strip().strip('"\'') for tag in tags]
        elif re.fullmatch(r'!file.inFolder\("[^"\n]+"\)', expression):
            folder = expression.split('"')[1]
            match = folder not in path.parts[:-1]
        elif re.fullmatch(r'state == "[^"\n]+"', expression):
            match = props.get('state') == expression.split('"')[1]
        else:
            raise AssertionError('Unsupported static selector: ' + expression)
        if not match:
            return False
    return True


class VaultTemplateTests(unittest.TestCase):
    def setUp(self):
        self.template = (ROOT / 'Templates/Knowledge Note.md').read_text()
        self.base = (ROOT / 'Knowledge Index.base').read_text()
        self.current, self.current_view = selectors(self.base, 'Current knowledge')
        self.historical, _ = selectors(self.base, 'Historical notes')

    def test_disposable_draft_becomes_current_with_visible_observation_date(self):
        with tempfile.TemporaryDirectory() as directory:
            note = pathlib.Path(directory) / 'Portable fixture.md'
            note.write_text(self.template)
            self.assertFalse(included(pathlib.Path('Library') / note.name,
                                      note.read_text(), self.current))
            checked = self.template.replace('state: draft', 'state: current')
            checked = checked.replace('observed_date:\n', 'observed_date: 2026-11-10\n')
            note.write_text(checked)
            props = properties(note.read_text())
            self.assertTrue(included(pathlib.Path('Library') / note.name,
                                     note.read_text(), self.current))
            self.assertEqual(props['observed_date'], '2026-11-10')
            self.assertIn('      - observed_date\n', self.current_view)
            self.assertEqual(props['generation'], '1')
            self.assertEqual(props['supersedes'], 'none')
            self.assertNotIn('observation_date', props)
            self.assertNotIn('supersedes_generation', props)

    def test_current_view_excludes_archive_templates_untagged_and_other_formats(self):
        checked = self.template.replace('state: draft', 'state: current')
        for path in ['Archive/Fixture.md', 'Templates/Fixture.md', 'Library/Fixture.canvas']:
            with self.subTest(path=path):
                self.assertFalse(included(pathlib.Path(path), checked, self.current))
        self.assertFalse(included(pathlib.Path('Library/Fixture.md'),
                                  checked.replace('tags: [knowledge]', 'tags: []'), self.current))

    def test_historical_reports_are_separate_from_current_claims(self):
        historical = self.template.replace('state: draft', 'state: historical-source-report')
        path = pathlib.Path('Library/Historical fixture.md')
        self.assertFalse(included(path, historical, self.current))
        self.assertTrue(included(path, historical, self.historical))


if __name__ == '__main__':
    unittest.main()
