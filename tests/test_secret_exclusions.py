"""Check real Git staging boundaries, including usable nonsecret templates."""
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class SecretExclusionTests(unittest.TestCase):
    def test_local_secret_files_ignored_and_templates_trackable(self):
        with tempfile.TemporaryDirectory(prefix='nstack-ignore-') as directory:
            work = pathlib.Path(directory)
            (work / '.gitignore').write_bytes((ROOT / '.gitignore').read_bytes())
            subprocess.run(['git', 'init', '-q', str(work)], check=True)
            private = ['.env', '.env.local', 'project/.env', 'project/.env.production',
                       'project/provider.env', 'auth.json', '.opencode/auth.json',
                       '.opencode/secrets/local.json']
            shareable = ['.env.example', '.env.sample', 'project/.env.example',
                         'project/.env.sample', 'opencode.json', 'project/settings.json',
                         'examples/provider-config.json']
            for name in private + shareable:
                target = work / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('synthetic fixture\n')
            result = subprocess.run(['git', 'check-ignore', '--stdin'], cwd=work,
                                    input='\n'.join(private + shareable) + '\n',
                                    text=True, capture_output=True, check=True)
            self.assertEqual(set(result.stdout.splitlines()), set(private))
            subprocess.run(['git', 'add', '.'], cwd=work, check=True)
            staged = subprocess.run(['git', 'diff', '--cached', '--name-only'], cwd=work,
                                    capture_output=True, text=True, check=True)
            self.assertEqual(set(staged.stdout.splitlines()), {'.gitignore', *shareable})


if __name__ == '__main__':
    unittest.main()
