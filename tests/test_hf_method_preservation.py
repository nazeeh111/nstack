"""Pinned-source replay only: no models, Hub clients, jobs, accounts or network."""
import ast
import copy
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'lib'))
import patch_hf
import patch_training

PIN = '25910b3d0ba31a2ba102f901cdc9e008c278a69c'
SOURCE = pathlib.Path(os.environ.get('NSTACK_TEST_HF_SOURCE', str(
    pathlib.Path.home() / 'Library/Application Support/nstack/sources/huggingface--skills' / PIN)))
NAMES = ('train-sentence-transformers', 'hf-cli', 'huggingface-local-models',
         'trl-training', 'huggingface-datasets', 'huggingface-spaces')


def without_training_notice(text):
    return text.replace(patch_training.AUTHORITY_NOTE, '', 1)


class TrainingCore(ast.NodeTransformer):
    """Ignore only admitted publication/privacy edits, preserving training math/code."""
    def visit_Module(self, node):
        self.generic_visit(node)
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
            node.body.pop(0)
        return node

    def visit_ImportFrom(self, node):
        return None if node.module == 'nstack_publish_scope' else node

    def visit_FunctionDef(self, node):
        if node.name == 'log_trackio_dashboard':
            return None
        return self.generic_visit(node)

    def visit_If(self, node):
        if len(node.body) == 1 and isinstance(node.body[0], ast.Expr):
            call = node.body[0].value
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == 'log_trackio_dashboard':
                return None
        return self.generic_visit(node)

    def visit_Try(self, node):
        if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == 'push_to_hub' for n in ast.walk(node)):
            return None
        return self.generic_visit(node)

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == 'publish_if_authorized':
            return None
        return self.generic_visit(node)

    def visit_keyword(self, node):
        if node.arg == 'report_to':
            node.value = ast.Constant(value='none')
        return node


class HFMethodPreservation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        receipt = SOURCE / '.nstack-source.json'
        if not receipt.is_file():
            raise unittest.SkipTest('Exact pinned offline source unavailable; no acquisition')
        data = json.loads(receipt.read_text())
        assert (data['repository'], data['revision']) == ('huggingface/skills', PIN)
        cls.temp = tempfile.TemporaryDirectory(prefix='nstack-hf-fidelity-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.outputs = {}
        for name in NAMES:
            raw = SOURCE / 'skills' / name
            for file in raw.rglob('*'):
                assert not file.is_symlink(), 'Unexpected source symlink; do not follow it'
                if file.is_file():
                    assert hashlib.sha256(file.read_bytes()).hexdigest() == data['files'][str(file.relative_to(SOURCE))]
            out = pathlib.Path(cls.temp.name) / name
            shutil.copytree(raw, out, symlinks=True)
            if name == 'train-sentence-transformers':
                patch_training.patch(out, ROOT / 'lib')
            else:
                patch_hf.patch(name, out)
            cls.outputs[name] = out

    def test_all_173_jobs_lines_and_submission_monitoring_recipes_survive(self):
        raw = (SOURCE / 'skills/train-sentence-transformers/references/hf_jobs_execution.md').read_text()
        active = (self.outputs['train-sentence-transformers'] / 'references/hf_jobs_execution.md').read_text()
        self.assertEqual(len(raw.splitlines()), 173)
        self.assertEqual(without_training_notice(active), raw)
        self.assertIn('hf jobs uv run', active)
        self.assertIn('## Monitoring a running job', active)
        self.assertIn('hub_strategy="every_save"', active)
        self.assertIn('within the user\'s existing named destination', active)

    def test_logging_resume_ddp_and_tensorboard_source_are_preserved(self):
        raw = (SOURCE / 'skills/train-sentence-transformers/references/training_args.md').read_text()
        active = (self.outputs['train-sentence-transformers'] / 'references/training_args.md').read_text()
        self.assertEqual(without_training_notice(active), raw.replace('report_to="trackio"', 'report_to="none"'))
        for phrase in ('## Hub push', '## Logging', 'logging_steps=0.01', 'logging_first_step=True',
                       'logging_dir=None', 'rank 0 under DDP', '**TensorBoard**',
                       'trackio.init(project=', 'resume_from_checkpoint=True'):
            self.assertIn(phrase, active)

    def test_full_upload_tracker_troubleshooting_keeps_native_account_status(self):
        raw = (SOURCE / 'skills/train-sentence-transformers/references/troubleshooting.md').read_text()
        old = '1. Run `hf auth whoami`. If it fails, run `hf auth login`.'
        new = '1. Confirm the authorized account and write access through supported native account status; do not inspect token stores. Account setup needs the task\'s existing authority.'
        active = (self.outputs['train-sentence-transformers'] / 'references/troubleshooting.md').read_text()
        self.assertEqual(without_training_notice(active), raw)
        self.assertIn('## Hub push fails', active)
        self.assertIn('## Tracker (Trackio / W&B / TensorBoard) not logging', active)
        self.assertIn('Point TB at the parent.', active)

    def test_all_thirteen_training_cores_and_local_logs_keep_upstream_code(self):
        out = self.outputs['train-sentence-transformers']
        files = sorted((out / 'scripts').glob('train_*_example.py'))
        self.assertEqual(len(files), 13)
        for file in files:
            with self.subTest(file=file.name):
                raw_tree = ast.parse((SOURCE / 'skills/train-sentence-transformers/scripts' / file.name).read_text())
                actual_tree = ast.parse(file.read_text())
                expected = TrainingCore().visit(copy.deepcopy(raw_tree))
                actual = TrainingCore().visit(copy.deepcopy(actual_tree))
                self.assertEqual(ast.dump(actual, include_attributes=False), ast.dump(expected, include_attributes=False))
                self.assertNotIn('def log_trackio_dashboard', file.read_text())
                self.assertNotIn('whoami(', file.read_text())
                self.assertIn('report_to="none"', file.read_text())
                self.assertIn('publish_if_authorized(', file.read_text())
                self.assertIn('save_pretrained(', file.read_text())
        self.assertEqual((out / 'scripts/nstack_publish_scope.py').read_bytes(), (ROOT / 'lib/publish_scope.py').read_bytes())

    def test_hf_cli_has_full_active_catalog_and_saved_support(self):
        raw = (SOURCE / 'skills/hf-cli/SKILL.md').read_text()
        active = (self.outputs['hf-cli'] / 'SKILL.md').read_text()
        catalog = raw[raw.index('## Commands'):]
        self.assertEqual(active[active.index('## Commands'):], catalog)
        support = (self.outputs['hf-cli'] / 'references/command-catalog.md').read_text()
        self.assertIn(catalog, support)
        self.assertIn('immutable', active)
        self.assertIn('never inspect token stores or print keys', active)
        self.assertNotIn('## Exact operation', active)

    def test_spaces_hosted_iteration_is_exact_and_real_privacy_optins_remain(self):
        raw = (SOURCE / 'skills/huggingface-spaces/SKILL.md').read_text()
        active = (self.outputs['huggingface-spaces'] / 'SKILL.md').read_text()
        start = raw.index('## 6. Iterate on the Space, not locally')
        end = raw.index('## 7. Verify', start)
        self.assertIn(raw[start:end], active)
        for header in ('## 7. Verify', '## 8. Permanent storage (buckets)', '## 9. When things break'):
            self.assertIn(raw[raw.index(header):raw.index(header) + len(header)], active)
        self.assertIn('.launch(share=False, mcp_server=False)', active)
        self.assertNotIn('.launch(mcp_server=True)', active)
        self.assertIn('--private \\', active)
        self.assertIn('public or protected only when the user explicitly authorizes', active)
        self.assertNotIn('## Commissioning boundary', active)
        self.assertNotIn('before publication', active)

    def test_no_generic_framework_and_no_bulk_session_upload_regression(self):
        self.assertEqual(patch_hf.SPLIT, '')
        raw = (SOURCE / 'skills/trl-training/SKILL.md').read_text()
        self.assertEqual((self.outputs['trl-training'] / 'SKILL.md').read_text(), raw)
        local = (self.outputs['huggingface-local-models'] / 'SKILL.md').read_text()
        self.assertNotIn('## Target acceptance', local)
        self.assertIn('cmake --build build --config Release', local)
        self.assertIn('NSTACK_REVIEWED_LLAMA_COMMIT', local)
        self.assertIn('NSTACK_MODEL_COMMIT', local)
        datasets = (self.outputs['huggingface-datasets'] / 'SKILL.md').read_text()
        self.assertNotIn('## Agent Traces', datasets)
        self.assertNotIn('~/.codex/sessions', datasets)
        self.assertIn('/rows?', datasets)
        self.assertIn('dataset repo', datasets)


if __name__ == '__main__':
    unittest.main()
