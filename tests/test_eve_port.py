"""An unrecognized Eve input must not become a partially patched live leaf."""
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'lib'))
from patch_conditional import patch


class EvePort(unittest.TestCase):
    def test_source_drift_fails_without_changing_existing_artifacts(self):
        for source in (
            '---\nname: eve\ndescription: changed source\n---\nUnrecognized bootstrap.\n',
            'Unrelated input without Eve frontmatter.\n',
        ):
            with self.subTest(source=source), tempfile.TemporaryDirectory() as temp:
                root = pathlib.Path(temp)
                skill = root / 'SKILL.md'
                skill.write_text(source)
                retained = root / 'retained.bin'
                retained.write_bytes(b'Existing uncommitted artifact\x00')
                before = {p.name: p.read_bytes() for p in root.iterdir()}
                with self.assertRaisesRegex(ValueError, 'Pinned Eve'):
                    patch('X-AUTO-EVE', root)
                self.assertEqual({p.name: p.read_bytes() for p in root.iterdir()}, before)


if __name__ == '__main__':
    unittest.main()
