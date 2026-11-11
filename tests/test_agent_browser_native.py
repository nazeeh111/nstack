"""Real pinned source replay and safe CLI guide introspection, no accounts/install.

Optional NSTACK_AGENT_BROWSER_SOURCE and NSTACK_AGENT_BROWSER_BINARY provide an
existing offline source/native binary in isolated clone checks. Missing source
reports an explicit skip; no network or dependency acquisition occurs.
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
import uuid

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'lib')]
from closure import validate
from patch_agent_browser import REVISION, VERSION, materialize_runtime_guides, patch_core, render_runtime_wrapper, session_commands
from skill_build import materialize

STATE = pathlib.Path.home() / 'Library/Application Support/nstack'
SOURCE = STATE / 'sources/vercel-labs--agent-browser' / REVISION
BINARY = STATE / 'native-tools/agent-browser/0.41.2/agent-browser'


class AgentBrowserNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = pathlib.Path(os.environ.get('NSTACK_AGENT_BROWSER_SOURCE', SOURCE))
        try:
            receipt = json.loads((cls.source / '.nstack-source.json').read_text())
        except (OSError, ValueError) as exc:
            raise unittest.SkipTest('Exact offline browser source unavailable; no fetch: ' + type(exc).__name__)
        if receipt.get('revision') != REVISION or receipt.get('repository') != 'vercel-labs/agent-browser':
            raise AssertionError('Wrong source identity')
        for f in (cls.source / 'skill-data').rglob('*'):
            if f.is_file():
                if hashlib.sha256(f.read_bytes()).hexdigest() != receipt['files'].get(str(f.relative_to(cls.source))):
                    raise AssertionError('Pinned source guide changed')
        cls.temp = tempfile.TemporaryDirectory(prefix='nstack-browser-port-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.base = pathlib.Path(cls.temp.name)
        cls.registry = json.loads((ROOT / 'registry/manifest.json').read_text())
        cls.component = next(x for x in cls.registry['components'] if x['id'] == 'P066')
        cls.outputs = {}
        for spec in cls.registry['skills']:
            if spec['candidate_id'] == 'P066' and spec['delivery'] == 'narrow-patched leaf':
                name = pathlib.Path(spec['source_path']).parent.name
                out = cls.base / name
                out.mkdir()
                materialize(cls.source, out, spec, cls.component, cls.registry)
                # Match native_setup's natural entry-name adaptation exactly.
                skill = out / 'SKILL.md'
                skill.write_text(re.sub(r'(?m)^name:.*$', 'name: ' + name, skill.read_text(), count=1))
                cls.outputs[name] = out
        cls.runtime = cls.base / 'guide-overlay'
        cls.identity = materialize_runtime_guides(cls.source, cls.runtime)
        cls.core = cls.runtime / 'skill-data/core'

    def test_installed_and_cli_core_complete_bytes_match_and_archives_bind_originals(self):
        installed = self.outputs['core']
        self.assertEqual({str(f.relative_to(installed)): f.read_bytes() for f in installed.rglob('*') if f.is_file()},
                         {str(f.relative_to(self.core)): f.read_bytes() for f in self.core.rglob('*') if f.is_file()})
        validate(installed)
        record = json.loads((installed / 'NATIVE-ADAPTATION.json').read_text())
        for rel, change in record['modifications'].items():
            original = self.source / 'skill-data/core' / rel
            self.assertEqual((installed / change['archival_original']).read_bytes(), original.read_bytes())
            self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(), change['source_sha256'])
        self.assertEqual(len(list(installed.rglob('SKILL.md'))), 1)
        self.assertEqual({p.parent.name for p in (self.runtime / 'skill-data').glob('*/SKILL.md')},
                         {p.parent.name for p in (self.source / 'skill-data').glob('*/SKILL.md')})

    def test_overlay_is_deterministic_across_roots_and_has_complete_notice_and_seal(self):
        other = (self.base / 'resolved-root' / 'overlay').resolve()
        identity = materialize_runtime_guides(self.source, other)
        self.assertEqual(identity, self.identity)
        files = lambda root: {str(f.relative_to(root)): f.read_bytes() for f in root.rglob('*') if f.is_file()}
        self.assertEqual(files(self.runtime), files(other))
        self.assertEqual((self.runtime / 'LICENSE').read_bytes(), (self.source / 'LICENSE').read_bytes())
        seal = json.loads((self.runtime / 'RUNTIME-GUIDES.json').read_text())
        for rel, sha in seal['files'].items():
            self.assertEqual(hashlib.sha256((self.runtime / rel).read_bytes()).hexdigest(), sha)

    def test_discovery_and_session_recipes_preserve_native_route_and_per_worker_owner(self):
        core = (self.core / 'SKILL.md').read_text()
        front = core.split('---', 2)[1]
        self.assertIn('already selected', front.replace('explicitly selected', 'already selected'))
        self.assertNotIn('allowed-tools:', front)
        session = core[core.index('## Always use your own session'):core.index('## The core loop')]
        self.assertIn('uuid.uuid4()', session)
        self.assertNotIn('session id --scope worktree', session)
        for file in (self.core / 'references').glob('*.md'):
            text = file.read_text()
            # Every literal command example selecting a session must use a task
            # variable; globally shared fixed labels are not worker isolation.
            self.assertNotRegex(text, r'agent-browser --session [A-Za-z][A-Za-z0-9_-]*(?:\s|$)')
        # A session-ID utility is deliberately stable; the UUID allocation recipe
        # must allocate different worker IDs without touching any CLI session.
        code = re.search(r"python3 -c '([^']+)'", session)[1]
        first = subprocess.check_output([sys.executable, '-c', code], text=True).strip()
        second = subprocess.check_output([sys.executable, '-c', code], text=True).strip()
        self.assertNotEqual(first, second)

    def test_active_auth_boundary_and_templates_do_not_bootstrap_accounts_or_default_session(self):
        auth = (self.core / 'references/authentication.md').read_text()
        self.assertNotIn('auth save', auth)
        self.assertNotIn('--auto-connect state save', auth)
        self.assertIn('archival data', auth)
        core = (self.core / 'SKILL.md').read_text()
        self.assertNotIn('npm i -g', core)
        self.assertNotIn('`doctor --fix` also runs', core)
        self.assertIn('specific authority', core)
        for name in ['form-automation.sh', 'capture-workflow.sh']:
            path = self.core / 'templates' / name
            text = path.read_text()
            self.assertIn('${NSTACK_TASK_SESSION:?', text)
            self.assertIn('agent-browser --session "$NSTACK_TASK_SESSION" "$@"', text)
            self.assertNotIn('agent-browser open ', text)
            self.assertNotIn('/tmp/form-result.png', text)
            r = subprocess.run(['/bin/bash', '-n', str(path)], text=True, capture_output=True)
            self.assertEqual(r.returncode, 0, r.stderr)
        # The former auto-import/login/state-deletion script now exits before any
        # browser or secret path is accessed; only its archive retains the source.
        r = subprocess.run(['/bin/sh', str(self.core / 'templates/authenticated-session.sh')],
                           text=True, capture_output=True)
        self.assertEqual(r.returncode, 2)
        self.assertIn('no credential/bootstrap script ran', r.stderr)

    def test_templates_bind_every_actual_call_and_preserve_output_paths_with_spaces(self):
        fakebin = self.base / 'fake-template-bin'
        fakebin.mkdir()
        record = self.base / 'template-calls.jsonl'
        fake = fakebin / 'agent-browser'
        fake.write_text('#!' + sys.executable + '\nimport json,pathlib,sys\n' +
                        'p=pathlib.Path(' + repr(str(record)) + ')\n' +
                        'with p.open("a") as f:f.write(json.dumps(sys.argv[1:])+"\\n")\n' +
                        'print("https://example.com" if sys.argv[-2:]==["get","url"] else "fixture")\n')
        fake.chmod(0o755)
        for name, worker in [('form-automation.sh', 'worker-one'), ('capture-workflow.sh', 'worker-two')]:
            output = self.base / ('output with spaces ' + worker)
            env = {'PATH': str(fakebin) + ':/usr/bin:/bin', 'LANG': 'C', 'NSTACK_TASK_SESSION': worker}
            result = subprocess.run(['/bin/bash', str(self.core / 'templates' / name),
                                     'https://example.com', str(output)], env=env,
                                    cwd=self.base, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            calls = [json.loads(x) for x in record.read_text().splitlines()]
            self.assertTrue(calls)
            self.assertTrue(all(call[:2] == ['--session', worker] for call in calls))
            shots = [call for call in calls if 'screenshot' in call]
            self.assertTrue(shots)
            self.assertTrue(all(str(output) in call[-1] for call in shots))
            record.unlink()

    def test_staged_cli_serves_exact_native_core_and_refs_without_live_reactivation(self):
        binary = pathlib.Path(os.environ.get('NSTACK_AGENT_BROWSER_BINARY', BINARY))
        if not binary.is_file():
            self.skipTest('Reviewed native binary unavailable; no install')
        config = self.base / 'empty-cli-config.json'
        config.write_text('{}\n')
        session = 'test-native-guide-' + uuid.uuid4().hex[:12]
        env = {'PATH': '/usr/bin:/bin:/usr/sbin:/sbin', 'LANG': 'C',
               'AGENT_BROWSER_SKILLS_DIR': str(self.runtime / 'skill-data')}
        prefix = [str(binary), '--session', session, '--config', str(config)]
        def call(*args):
            return subprocess.run(prefix + list(args), cwd=self.base, env=env,
                                  text=True, capture_output=True, timeout=15)
        version = call('--version')
        self.assertEqual(version.returncode, 0)
        self.assertEqual(version.stdout.strip(), 'agent-browser ' + VERSION)
        core = call('skills', 'get', 'core')
        self.assertEqual(core.returncode, 0, core.stderr)
        self.assertEqual(core.stdout.encode(), (self.outputs['core'] / 'SKILL.md').read_bytes())
        for ref in ['commands', 'references/session-management.md', 'references/authentication.md',
                    'references/trust-boundaries.md', 'templates/form-automation.sh']:
            r = call('skills', 'get', 'core', '--ref', ref)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertNotIn('npm i -g agent-browser', r.stdout)

    def test_source_drift_fails_before_modifying_an_unrecognized_core(self):
        out = self.base / 'drift'
        out.mkdir()
        (out / 'SKILL.md').write_text('---\nname: unrelated\n---\nDifferent document\n')
        before = (out / 'SKILL.md').read_bytes()
        with self.assertRaisesRegex(ValueError, 'Pinned agent-browser'):
            patch_core(out)
        self.assertEqual((out / 'SKILL.md').read_bytes(), before)


class BrowserGuideContextAndGuard(unittest.TestCase):
    def test_markdown_prose_is_unchanged_while_all_cli_subcommands_are_bound(self):
        prose = ('Use this only after agent-browser is the selected route. '
                 'Pass --session on every command; --session as the key is not allocation.\n')
        commands = ['keydown Alt', 'keyup Alt', 'storage local get x', 'window new',
                    'highlight @e1', 'inspect', 'a11y audit', 'removeinitscript',
                    'stream status', 'dashboard stop', '-p example open https://example.com',
                    'future-command --unknown value']
        source = prose + '\n```bash\n' + '\n'.join('agent-browser ' + x for x in commands)
        source += '\ntimeout 60 agent-browser get title\n' + '```\n`agent-browser storage local clear`\n'
        result = session_commands(source)
        self.assertTrue(result.startswith(prose))
        self.assertIn('timeout 60 agent-browser --session "$NSTACK_TASK_SESSION" get title', result)
        for command in commands:
            self.assertIn('agent-browser --session "$NSTACK_TASK_SESSION" ' + command, result)
        self.assertIn('`agent-browser --session "$NSTACK_TASK_SESSION" storage local clear`', result)
        self.assertEqual(session_commands(result), result)

    def test_wrapper_rejects_unscoped_future_commands_and_preserves_exact_arguments(self):
        with tempfile.TemporaryDirectory(prefix='native-browser-wrapper-') as temp:
            base = pathlib.Path(temp)
            record = base / 'calls.jsonl'
            binary = base / 'fake binary'
            binary.write_text('#!' + sys.executable + '\nimport json,pathlib,sys\n' +
                              'p=pathlib.Path(' + repr(str(record)) + ')\n' +
                              'with p.open("a") as f:f.write(json.dumps(sys.argv[1:])+"\\n")\n')
            binary.chmod(0o755)
            wrapper = base / 'wrapper'
            wrapper.write_text(render_runtime_wrapper(binary, base / 'guide root',
                                                       base / 'browser binary', base / 'sockets'))
            wrapper.chmod(0o755)
            for args in [['open', 'https://example.com'], ['future-command'], ['close'],
                         ['--args', '--session', 'open', 'https://example.com'],
                         ['open', 'https://example.com', '--', '--session', 'pretend'],
                         ['--session'], ['--session', '']]:
                result = subprocess.run([str(wrapper), *args], text=True, capture_output=True)
                self.assertEqual(result.returncode, 2, args)
                self.assertIn('no browser command ran', result.stderr)
                self.assertFalse(record.exists(), args)
            accepted = [['--help'], ['--version'], ['doctor', '--help'], ['skills', 'get', 'core'],
                        ['--session', 'worker-a', 'future-command', 'value with spaces'],
                        ['--session', 'worker-b', 'open', 'https://example.com']]
            for args in accepted:
                result = subprocess.run([str(wrapper), *args], text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual([json.loads(x) for x in record.read_text().splitlines()], accepted)


if __name__ == '__main__':
    unittest.main()
