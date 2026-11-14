"""Real local discovery boundaries and missing-capability behavior."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import os

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "addons/01/scripts/capabilities.py"
spec = importlib.util.spec_from_file_location("adaptive_capabilities", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DiscoveryTests(unittest.TestCase):
    def test_later_addon_description_runtime_and_no_irrelevant_or_private_reads(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            entry = state / "native-releases/fixture/bundles/added/SKILL.md"
            entry.parent.mkdir(parents=True)
            entry.write_text("---\nname: added\ndescription: Render unusual local figures\n"
                             "disable-model-invocation: true\n---\nFull task guidance.\n")
            outside = state / "private/SKILL.md"
            outside.parent.mkdir()
            outside.write_text("---\ndescription: figure credential sentinel\n---\nsynthetic\n")
            escape = state / "native-releases/escape/SKILL.md"
            escape.parent.mkdir()
            escape.symlink_to(outside)
            rows = [{"name": "added", "skill_path": str(entry), "deployment": "on demand"},
                    {"name": "unsafe", "skill_path": str(outside)},
                    {"name": "escape", "skill_path": str(escape)},
                    {"name": "wrong-file", "skill_path": str(state / "native-releases/auth.json")}]
            (state / "native-skill-index.json").write_text(json.dumps(rows))
            (state / "native-tools").mkdir()
            (state / "native-tools/index.json").write_text(json.dumps([
                {"name": "figure-renderer", "version": "fixture", "binary": "/fixture/bin",
                 "checks": "Prior figure output checked", "apiKey": "never-emit-this"}]))
            result = module.search(state, ["figures", "figure"], 8)
            self.assertEqual({x["name"] for x in result["matches"]}, {"added", "figure-renderer"})
            self.assertTrue(next(x for x in result["matches"] if x["kind"] == "skill")["manual_only"])
            self.assertNotIn("never-emit-this", json.dumps(result))
            self.assertEqual(len(result["sources"]), 2)
            self.assertEqual(module.search(state, ["unrelated-objective"])["matches"], [])
            run = subprocess.run([sys.executable, str(SCRIPT), "--state", str(state),
                                  "--limit", "1", "figure"], capture_output=True, text=True, check=True)
            self.assertEqual(len(json.loads(run.stdout)["matches"]), 1)
            self.assertEqual(json.loads(run.stdout)["total_matches"], 2)

    def test_uninstalled_or_malformed_inventory_is_not_false_readiness(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            self.assertEqual(module.search(state, ["render"])["matches"], [])
            (state / "native-skill-index.json").write_text("{}")
            with self.assertRaisesRegex(ValueError, "array"):
                module.search(state, ["render"])


class CurrentSkillDiscoveryTests(unittest.TestCase):
    def test_native_opencode_manual_metadata_is_reported_and_refreshes(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); state = base / 'state'; state.mkdir(); root = base / 'skills'
            entry = root / 'manual' / 'SKILL.md'; entry.parent.mkdir(parents=True)
            entry.write_text('---\nname: manual\ndescription: Calibrate beacon logs\nmetadata: # invocation policy\n# comment before mapping children\n  opencode/autoinvoke: false # explicit only\n---\nInstructions.\n')
            self.assertTrue(module.search(state, ['beacon'], skill_roots=[root])['matches'][0]['manual_only'])
            entry.write_text(entry.read_text().replace('false # explicit only', 'true'))
            self.assertNotIn('manual_only', module.search(state, ['beacon'], skill_roots=[root])['matches'][0])
            entry.write_text(entry.read_text().replace('  opencode/autoinvoke: true', '  other:\n    opencode/autoinvoke: false'))
            self.assertNotIn('manual_only', module.search(state, ['beacon'], skill_roots=[root])['matches'][0])

    def skill(self, root, name, description, body=b'Body must never be decoded: \xff'):
        path = root / name / 'SKILL.md'
        path.parent.mkdir(parents=True)
        path.write_bytes(('---\nname: ' + name.split('/')[-1] + '\ndescription: ' + description + '\n---\n').encode() + body)
        return path

    def test_new_removed_and_edited_metadata_is_fresh_on_each_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); state = base / 'state'; root = base / 'skills'
            state.mkdir(); root.mkdir()
            self.assertEqual(module.search(state, ['aurora'], skill_roots=[root])['matches'], [])
            entry = self.skill(root, 'group/aurora', '>-\n  Plot aurora measurements\n  with uncertainty')
            first = module.search(state, ['aurora', 'uncertainty'], skill_roots=[root])
            self.assertEqual(len(first['matches']), 1)
            self.assertEqual(first['matches'][0]['description'], 'Plot aurora measurements with uncertainty')
            self.assertNotIn('Body must never', json.dumps(first))
            entry.write_bytes(entry.read_bytes().replace(b'aurora measurements', b'ion measurements'))
            changed = module.search(state, ['ion'], skill_roots=[root])
            self.assertEqual(len(changed['matches']), 1)
            self.assertNotEqual(first['sources'][0]['sha256'], changed['sources'][0]['sha256'])
            entry.unlink()
            self.assertEqual(module.search(state, ['uncertainty'], skill_roots=[root])['matches'], [])

    def test_plain_multiline_description_is_searchable_and_refreshes(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); state = base / 'state'; state.mkdir(); root = base / 'skills'
            entry = self.skill(root, 'composition-patterns',
                               '\n  React composition patterns that scale. Use when refactoring components with\n'
                               '  boolean prop proliferation, building flexible component libraries, or\n'
                               '  designing reusable APIs. Triggers on tasks involving compound components,\n'
                               '  render props, context providers, or component architecture.')
            found = module.search(state, ['compound', 'render props'], skill_roots=[root])
            self.assertEqual(found['total_matches'], 1)
            self.assertIn('compound components, render props', found['matches'][0]['description'])
            entry.write_bytes(entry.read_bytes().replace(b'compound components', b'composable controls'))
            self.assertEqual(module.search(state, ['compound'], skill_roots=[root])['total_matches'], 0)
            self.assertEqual(module.search(state, ['composable'], skill_roots=[root])['total_matches'], 1)

    def test_literal_metadata_stops_before_body_and_nested_support_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); root = base / 'skills'; state = base / 'state'; state.mkdir()
            entry = self.skill(root, 'outer', '|\n  Map sensor vectors\n  Preserve units')
            self.skill(entry.parent, 'support/hidden', 'Hidden sentinel capability')
            self.skill(root, '__pycache__/hidden', 'Hidden sentinel capability')
            found = module.search(state, ['sensor'], skill_roots=[root])
            self.assertEqual(found['matches'][0]['description'], 'Map sensor vectors\nPreserve units')
            self.assertEqual(module.search(state, ['sentinel'], skill_roots=[root])['matches'], [])

    def test_deduplicates_aliases_handles_cycles_and_never_opens_redirects(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); state = base / 'state'; state.mkdir()
            root = base / 'skills'; root.mkdir()
            entry = self.skill(state / 'native-releases/build/bundles', 'shared', 'Calibrate spectral sensors')
            (state / 'native-skill-index.json').write_text(json.dumps([{'name': 'shared', 'skill_path': str(entry)}]))
            (root / 'shared').symlink_to(entry.parent, target_is_directory=True)
            (root / 'alias').symlink_to(entry.parent, target_is_directory=True)
            (root / 'cycle').symlink_to(root, target_is_directory=True)
            (root / 'self').symlink_to('self', target_is_directory=True)
            secret = self.skill(base / '.aws', 'protected', 'Credential sentinel')
            (root / 'credential-link').symlink_to(secret.parent, target_is_directory=True)
            auth = base / 'private/auth.json'; auth.parent.mkdir(); auth.write_text('credential sentinel')
            bad = root / 'wrong'; bad.mkdir(); (bad / 'SKILL.md').symlink_to(auth)
            outside = self.skill(base / 'unrelated', 'redirect', 'Credential sentinel')
            (root / 'outside').symlink_to(outside.parent, target_is_directory=True)
            ordinary_open = Path.open
            def checked(path, *args, **kwargs):
                if path.resolve() in {secret.resolve(), auth.resolve(), outside.resolve()}:
                    raise AssertionError('Private or out-of-scope file was opened')
                return ordinary_open(path, *args, **kwargs)
            with patch.object(Path, 'open', checked):
                result = module.search(state, ['spectral', 'sentinel'], skill_roots=[root])
            self.assertEqual([x['name'] for x in result['matches']], ['shared'])
            self.assertNotIn('Credential sentinel', json.dumps(result))
            self.assertGreater(result['sources'][-1]['skipped'], 0)

    def test_cli_state_is_isolated_and_defaults_include_current_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); home = base / 'home'; home.mkdir(); state = base / 'state'; state.mkdir()
            project = base / 'project'; project.mkdir(); (project / '.git').mkdir()
            root = project / '.opencode/skills'; self.skill(root, 'later', 'Correlate beacon logs')
            nested = project / 'src'; nested.mkdir()
            env = {**os.environ, 'HOME': str(home), 'NSTACK_STATE': str(state)}
            def run(*args):
                return json.loads(subprocess.check_output([sys.executable, str(SCRIPT), *args, 'beacon'], cwd=nested, env=env, text=True))
            self.assertEqual(run('--state', str(state))['matches'], [])
            self.assertEqual([x['name'] for x in run('--state', str(state), '--skills-root', str(root))['matches']], ['later'])
            self.assertEqual([x['name'] for x in run()['matches']], ['later'])

    def test_frontmatter_and_traversal_have_explicit_bounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); state = base / 'state'; state.mkdir(); root = base / 'skills'
            self.skill(root, 'huge', 'x' * (module.MAX_FRONTMATTER + 1))
            result = module.search(state, ['huge'], skill_roots=[root])
            self.assertEqual(result['matches'], [])
            self.assertGreater(result['sources'][0]['skipped'], 0)
            with patch.object(module, 'MAX_PATHS', 1):
                limited = module.search(state, ['anything'], skill_roots=[root])
            self.assertTrue(limited['sources'][0]['path_budget_exhausted'])


    def test_index_symlink_inside_state_is_rejected_before_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp); private = state / 'private/account.json'
            private.parent.mkdir(); private.write_text('[{"name":"sentinel","apiKey":"not-for-discovery"}]')
            (state / 'native-tools').mkdir()
            (state / 'native-tools/index.json').symlink_to(private)
            ordinary_open = Path.open
            def checked(path, *args, **kwargs):
                if path.resolve() == private:
                    raise AssertionError('Account metadata was read')
                return ordinary_open(path, *args, **kwargs)
            with patch.object(Path, 'open', checked):
                with self.assertRaisesRegex(ValueError, 'without redirects'):
                    module.search(state, ['sentinel'])


class DescriptorBoundaryTests(unittest.TestCase):
    def fixture(self, base):
        base = base.resolve()
        state = base / 'state'; state.mkdir()
        root = base / 'skills'; entry = root / 'current/SKILL.md'; entry.parent.mkdir(parents=True)
        entry.write_text('---\nname: current\ndescription: ordinary beacon\n---\n')
        secret = base / '.aws/synthetic/SKILL.md'; secret.parent.mkdir(parents=True)
        secret.write_text('---\nname: private\ndescription: private sentinel\n---\nSynthetic only\n')
        return state, root, entry, secret

    def no_private_stream(self, secret):
        original = module.os.fdopen
        info = secret.stat()
        def checked(descriptor, *args, **kwargs):
            actual = os.fstat(descriptor)
            if (actual.st_dev, actual.st_ino) == (info.st_dev, info.st_ino):
                raise AssertionError('Private fixture descriptor reached a content reader')
            return original(descriptor, *args, **kwargs)
        return checked

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'FIFO requires POSIX')
    def test_fifo_named_skill_exits_within_timeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve(); state = base / 'state'; state.mkdir()
            root = base / 'skills'; entry = root / 'queued/SKILL.md'; entry.parent.mkdir(parents=True)
            os.mkfifo(entry)
            result = subprocess.run([sys.executable, str(SCRIPT), '--state', str(state),
                                     '--skills-root', str(root), 'beacon'], capture_output=True,
                                    text=True, timeout=2, check=True)
            found = json.loads(result.stdout)
            self.assertEqual(found['matches'], [])
            self.assertEqual(found['sources'][0]['skipped'], 1)

    def test_final_file_swap_after_validation_never_reads_redirect(self):
        with tempfile.TemporaryDirectory() as tmp:
            state, root, entry, secret = self.fixture(Path(tmp))
            original = module.regular_file
            swapped = []
            def swap(path):
                if path == entry and not swapped:
                    entry.unlink(); entry.symlink_to(secret); swapped.append(True)
                return original(path)
            with patch.object(module, 'regular_file', swap), patch.object(module.os, 'fdopen', self.no_private_stream(secret)):
                result = module.search(state, ['sentinel'], skill_roots=[root])
            self.assertTrue(swapped)
            self.assertEqual(result['matches'], [])

    def test_parent_directory_swap_after_validation_never_reads_redirect(self):
        with tempfile.TemporaryDirectory() as tmp:
            state, root, entry, secret = self.fixture(Path(tmp))
            original = module.regular_file
            swapped = []
            def swap(path):
                if path == entry and not swapped:
                    entry.parent.rename(root / 'retained-original')
                    entry.parent.symlink_to(secret.parent, target_is_directory=True)
                    swapped.append(True)
                return original(path)
            with patch.object(module, 'regular_file', swap), patch.object(module.os, 'fdopen', self.no_private_stream(secret)):
                result = module.search(state, ['sentinel'], skill_roots=[root])
            self.assertTrue(swapped)
            self.assertEqual(result['matches'], [])

    def test_index_file_and_parent_swaps_fail_before_account_read(self):
        for parent_swap in (False, True):
            with self.subTest(parent_swap=parent_swap), tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp).resolve(); state = base / 'state'; state.mkdir()
                index = state / 'native-tools/index.json'; index.parent.mkdir(); index.write_text('[]')
                private = base / '.aws/synthetic/index.json'; private.parent.mkdir(parents=True)
                private.write_text('[{"name":"sentinel","apiKey":"synthetic-not-for-discovery"}]')
                original = module.regular_file
                swapped = []
                def swap(path):
                    if path == index and not swapped:
                        if parent_swap:
                            index.parent.rename(state / 'retained-index')
                            index.parent.symlink_to(private.parent, target_is_directory=True)
                        else:
                            index.unlink(); index.symlink_to(private)
                        swapped.append(True)
                    return original(path)
                with patch.object(module, 'regular_file', swap), patch.object(module.os, 'fdopen', self.no_private_stream(private)):
                    with self.assertRaises((OSError, ValueError)):
                        module.search(state, ['sentinel'])
                self.assertTrue(swapped)

    def test_unsupported_descriptor_boundary_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, _, entry, _ = self.fixture(Path(tmp))
            with patch.object(module.os, 'supports_dir_fd', set()):
                with self.assertRaisesRegex(ValueError, 'unavailable'):
                    module.frontmatter(entry)


class ClaudeDiscoveryTests(unittest.TestCase):
    def fixture(self, base):
        state, home, project = base / 'state', base / 'home', base / 'project'
        state.mkdir(); home.mkdir(); project.mkdir(); (project / '.git').mkdir()
        for host, prefix in [('native', 'native'), ('claude', 'claude')]:
            entry = state / (prefix + '-releases') / 'fixture/bundles/shared/SKILL.md'
            entry.parent.mkdir(parents=True)
            entry.write_text('---\nname: shared\ndescription: beacon ' + host + ' methods\n---\n')
            (state / (prefix + '-skill-index.json')).write_text(json.dumps([{'name': 'shared', 'skill_path': str(entry)}]))
            root = home / ('.claude/skills' if host == 'claude' else '.agents/skills')
            root.mkdir(parents=True)
            (root / 'shared').symlink_to(entry.parent)
        (state / 'native-tools').mkdir()
        (state / 'native-tools/index.json').write_text(json.dumps([{'name': 'beacon-runtime', 'command': '/example/bin'}]))
        return state, home, project

    def test_native_and_claude_default_scopes_do_not_crowd_each_other(self):
        with tempfile.TemporaryDirectory() as temporary:
            state, home, project = self.fixture(Path(temporary).resolve())
            for host in ('native', 'claude'):
                roots = module.default_skill_roots(home, project, host=host)
                result = module.search(state, ['beacon'], skill_roots=roots, host=host)
                self.assertEqual(result['host'], host)
                self.assertEqual(result['total_matches'], 2)
                skills = [row for row in result['matches'] if row['kind'] == 'skill']
                self.assertEqual(len(skills), 1)
                self.assertEqual(skills[0]['description'], 'beacon ' + host + ' methods')
            local = project / '.claude/skills/project/SKILL.md'
            local.parent.mkdir(parents=True)
            local.write_text('---\nname: project\ndescription: beacon project-only methods\n---\n')
            found = module.search(state, ['project-only'], host='claude',
                                  skill_roots=module.default_skill_roots(home, project, host='claude'))
            self.assertEqual([row['name'] for row in found['matches']], ['project'])

    def test_installed_claude_helper_infers_host_and_isolated_state_stays_isolated(self):
        with tempfile.TemporaryDirectory() as temporary:
            state, home, project = self.fixture(Path(temporary).resolve())
            script = state / 'claude-releases/helper/scripts/capabilities.py'
            script.parent.mkdir(parents=True)
            script.write_bytes(SCRIPT.read_bytes())
            env = {**os.environ, 'HOME': str(home)}
            command = [sys.executable, str(script), '--state', str(state), 'beacon']
            result = json.loads(subprocess.check_output(command, cwd=project, env=env, text=True))
            self.assertEqual(result['host'], 'claude')
            self.assertEqual(len(result['sources']), 2)
            self.assertTrue(all('claude-releases' in row['path'] for row in result['matches'] if row['kind'] == 'skill'))
            explicit = json.loads(subprocess.check_output(command + ['--host', 'native'], cwd=project, env=env, text=True))
            self.assertEqual(explicit['host'], 'native')
            self.assertTrue(all('native-releases' in row['path'] for row in explicit['matches'] if row['kind'] == 'skill'))

    def test_custom_config_env_only_changes_current_user_claude_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            current, other, configured, project = base / 'current', base / 'other', base / 'custom', base / 'project'
            codex = base / 'custom-codex'
            project.mkdir(); (project / '.git').mkdir()
            with patch.object(Path, 'home', return_value=current), patch.dict(os.environ, {
                    'CLAUDE_CONFIG_DIR': str(configured), 'CODEX_HOME': str(codex)}):
                roots = module.default_skill_roots(current, project, host='claude')
                self.assertEqual(roots[0], configured / 'skills')
                self.assertNotIn(current / '.claude/skills', roots)
                self.assertIn(project / '.claude/skills', roots)
                foreign = module.default_skill_roots(other, project, host='claude')
                self.assertEqual(foreign[0], other / '.claude/skills')
                native = module.default_skill_roots(current, project, host='native')
                self.assertNotIn(configured / 'skills', native)
                self.assertIn(codex / 'skills', native)
                self.assertNotIn(current / '.codex/skills', native)
                foreign_native = module.default_skill_roots(other, project, host='native')
                self.assertIn(other / '.codex/skills', foreign_native)
                self.assertNotIn(codex / 'skills', foreign_native)
