import ctypes
import errno
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'lib'))
import native_copy


class GeneratedBundleCopy(unittest.TestCase):
    def fixture(self, root):
        source = root / 'source'
        (source / 'nested').mkdir(parents=True)
        (source / 'nested/data.bin').write_bytes(bytes(range(256)) * 64)
        (source / 'tool.sh').write_text('#!/bin/sh\nprintf fixture\\n\n')
        (source / 'tool.sh').chmod(0o555)
        (source / 'nested/data.bin').chmod(0o444)
        (source / 'nested').chmod(0o555)
        return source

    def assert_independent(self, source, destination):
        for original in source.rglob('*'):
            copied = destination / original.relative_to(source)
            self.assertEqual(original.stat().st_mode & 0o777, copied.stat().st_mode & 0o777)
            self.assertNotEqual(original.stat().st_ino, copied.stat().st_ino)
            if original.is_file():
                self.assertEqual(original.read_bytes(), copied.read_bytes())
        output = destination / 'nested/data.bin'
        output.chmod(0o644)
        output.write_bytes(b'changed output')
        self.assertEqual((source / 'nested/data.bin').read_bytes(), bytes(range(256)) * 64)
        original = source / 'tool.sh'
        original.chmod(0o755)
        original.write_text('changed original')
        self.assertNotEqual(original.read_bytes(), (destination / 'tool.sh').read_bytes())

    def test_off_darwin_matches_copy2_and_is_independent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            source = self.fixture(root)
            with patch.object(native_copy.sys, 'platform', 'linux'), patch.object(native_copy, '_clonefile') as clone:
                native_copy.copy_generated_tree(source, root / 'copy')
            clone.assert_not_called()
            self.assert_independent(source, root / 'copy')

    def test_unsupported_clone_falls_back_without_changing_source(self):
        for error in (errno.ENOTSUP, errno.EXDEV, errno.ENOSYS):
            with self.subTest(error=error), tempfile.TemporaryDirectory() as temp:
                root = pathlib.Path(temp)
                source = self.fixture(root)
                def unsupported(*args):
                    ctypes.set_errno(error)
                    return -1
                with patch.object(native_copy.sys, 'platform', 'darwin'), patch.object(native_copy, '_clonefile', return_value=unsupported):
                    native_copy.copy_generated_tree(source, root / 'copy')
                self.assert_independent(source, root / 'copy')

    def test_permission_failure_is_not_retried_as_an_ordinary_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            source = self.fixture(root)
            def denied(*args):
                ctypes.set_errno(errno.EACCES)
                return -1
            with patch.object(native_copy.sys, 'platform', 'darwin'), patch.object(native_copy, '_clonefile', return_value=denied), patch.object(native_copy.shutil, 'copy2') as fallback:
                with self.assertRaises(shutil.Error):
                    native_copy.copy_generated_tree(source, root / 'copy')
            fallback.assert_not_called()

    @unittest.skipUnless(sys.platform == 'darwin', 'requires native clonefile')
    def test_native_clone_has_exact_bytes_modes_and_independent_writes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            source = self.fixture(root)
            native = native_copy._clonefile()
            results = []
            def observed(*args):
                result = native(*args)
                results.append(result)
                return result
            with patch.object(native_copy, '_clonefile', return_value=observed):
                native_copy.copy_generated_tree(source, root / 'copy')
            self.assertTrue(results)
            self.assertEqual(results, [0] * len(results), 'native clone support was unavailable in this test filesystem')
            self.assert_independent(source, root / 'copy')


if __name__ == '__main__':
    unittest.main()
