"""Offline controls for the installer boundary and false-success render checks."""
import copy
import hashlib
import importlib.util
import io
import json
import pathlib
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('raea_recipe', ROOT / 'recipes/raea.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


class RaeA(unittest.TestCase):
    def test_archive_refuses_escape_link_parent_and_devices(self):
        with tempfile.TemporaryDirectory() as directory:
            base = pathlib.Path(directory)
            cases = []
            escaping = tarfile.TarInfo('../escaped'); escaping.size = 1; cases.append([escaping])
            link = tarfile.TarInfo('root/link'); link.type = tarfile.SYMTYPE; link.linkname = '../../outside'; cases.append([link])
            parent = tarfile.TarInfo('root/dir'); parent.type = tarfile.SYMTYPE; parent.linkname = 'inside'
            child = tarfile.TarInfo('root/dir/child'); child.size = 1; cases.append([child, parent])
            device = tarfile.TarInfo('root/device'); device.type = tarfile.CHRTYPE; cases.append([device])
            for index, members in enumerate(cases):
                archive = base / ('bad-%d.tar' % index)
                with tarfile.open(archive, 'w') as tf:
                    for member in members: tf.addfile(member, io.BytesIO(b'x') if member.isfile() else None)
                target = base / ('target-%d' % index); target.mkdir()
                with self.assertRaises(ValueError): m.extract(archive, target)
                self.assertEqual(list(target.iterdir()), [])
            self.assertFalse((base / 'escaped').exists())

    def test_safe_internal_link_and_source_support_extract(self):
        with tempfile.TemporaryDirectory() as directory:
            base = pathlib.Path(directory); archive = base / 'safe.tar'
            regular = tarfile.TarInfo('root/data'); regular.size = 5
            link = tarfile.TarInfo('root/link'); link.type = tarfile.SYMTYPE; link.linkname = 'data'
            with tarfile.open(archive, 'w') as tf:
                tf.addfile(link); tf.addfile(regular, io.BytesIO(b'value'))
            target = base / 'target'; target.mkdir(); m.extract(archive, target)
            self.assertEqual((target / 'root/link').read_bytes(), b'value')
            self.assertEqual(m.manifest(target)['root/link'], {'link': 'data'})

    def test_no_account_provider_or_proxy_environment_inherited(self):
        with patch.dict(m.os.environ, {'OPENAI_API_KEY': 'synthetic-not-a-key', 'GH_TOKEN': 'synthetic-only',
                                      'HTTPS_PROXY': 'synthetic-only', 'HOME': '/private/account-home'}):
            env = m.isolated_env('/private/owned/home', '/private/runtime/bin')
            self.assertFalse({'OPENAI_API_KEY', 'GH_TOKEN', 'HTTPS_PROXY'} & env.keys())
            self.assertEqual(env['HOME'], '/private/owned/home')
            self.assertEqual(env['RAEA_ENV_FILE'], '/dev/null')
            self.assertEqual((env['RAEA_OFFLINE'], env['RAEA_AUDIO_AUTOSETUP']), ('1', '0'))

    def test_installed_tamper_cannot_be_hidden_by_forging_local_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory); binary = root / 'payload/raea/bin/raea'; binary.parent.mkdir(parents=True)
            binary.write_bytes(b'original binary fixture'); binary.chmod(0o755)
            rows = m.manifest(root / 'payload')
            expected = hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            doc = {'archive_sha256': m.SHA256, 'revision': m.REVISION, 'skills_revision': m.SKILLS_REVISION, 'files': rows}
            (root / 'SOURCE.json').write_text(json.dumps(doc))
            with patch.object(m, 'FILES_SHA256', expected), patch.object(m, 'LICENSES', {}):
                self.assertEqual(m.verify(root), binary)
                binary.write_bytes(b'altered binary fixture'); doc['files'] = m.manifest(root / 'payload')
                (root / 'SOURCE.json').write_text(json.dumps(doc))
                with self.assertRaisesRegex(ValueError, 'differs'): m.verify(root)
                self.assertEqual(binary.read_bytes(), b'altered binary fixture')

    def test_bad_archive_not_executed_and_modified_runtime_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            base = pathlib.Path(directory).resolve(); archive = base / 'wrong.tar.gz'; archive.write_bytes(b'not the pinned release')
            with patch.object(m.platform, 'system', return_value='Darwin'), patch.object(m.platform, 'machine', return_value='arm64'), patch.object(m, 'attestation') as proof:
                with self.assertRaisesRegex(ValueError, 'SHA256'): m.install(base, archive)
                proof.assert_not_called()
                root = base / 'native-tools/raea' / m.VERSION; root.mkdir(); (root / 'later-work').write_text('keep')
                with self.assertRaisesRegex(ValueError, 'Unowned'): m.install(base, archive)
                self.assertEqual((root / 'later-work').read_text(), 'keep')

    def test_zero_exit_is_not_proof_gpu_and_artifact_controls(self):
        with tempfile.TemporaryDirectory() as directory:
            out = pathlib.Path(directory)
            manifest = {'width': 640, 'height': 360, 'fps': 30, 'frames': [{'frame': 0}, {'frame': 1}], 'clipping': [], 'not_applied': []}
            probe = {'streams': [{'codec_type': 'video', 'codec_name': 'h264', 'width': 640, 'height': 360,
                                 'nb_read_frames': '2', 'avg_frame_rate': '30/1'}], 'format': {'duration': '0.066667'}}
            for name in ['render.stdout.log', 'render.stderr.log']: (out / name).write_text('')
            (out / 'render.json').write_text(json.dumps(manifest)); m.check_artifact(out, 640, 360, 30, 2, probe)
            bad = []
            x = copy.deepcopy(manifest); x['not_applied'] = ['unsupported feature']; bad.append((x, probe, ''))
            x = copy.deepcopy(manifest); x['clipping'] = ['missing text']; bad.append((x, probe, ''))
            x = copy.deepcopy(manifest); x['frames'] = [{'frame': 0}]; bad.append((x, probe, ''))
            x = copy.deepcopy(probe); x['streams'][0]['nb_read_frames'] = '1'; bad.append((manifest, x, ''))
            x = copy.deepcopy(probe); x['streams'][0]['avg_frame_rate'] = '24/1'; bad.append((manifest, x, ''))
            x = copy.deepcopy(probe); x['streams'][0]['width'] = 320; bad.append((manifest, x, ''))
            x = copy.deepcopy(probe); x['format']['duration'] = '1.0'; bad.append((manifest, x, ''))
            bad.append((manifest, probe, 'APPLIED\nGPU validation error: incomplete frame'))
            for doc, observation, log in bad:
                (out / 'render.json').write_text(json.dumps(doc)); (out / 'render.stderr.log').write_text(log)
                with self.assertRaises(ValueError): m.check_artifact(out, 640, 360, 30, 2, observation)

    def test_failed_metadata_preflight_never_starts_video_render(self):
        with tempfile.TemporaryDirectory() as directory:
            base = pathlib.Path(directory); source = base / 'edit.tsx'; source.write_text('approved fixture')
            out = base / 'fresh'
            with patch.object(m, 'execute', return_value=1) as execute:
                with self.assertRaisesRegex(ValueError, 'preflight failed'):
                    m.render('/unused', source, out, ffmpeg='/unused', ffprobe='/unused')
                self.assertEqual(execute.call_count, 1)
            self.assertFalse((out / 'render.mp4').exists())
            self.assertEqual(json.loads((out / 'run.json').read_text())['status'], 'incomplete')

    def test_preflight_does_not_reset_the_total_work_deadline(self):
        with tempfile.TemporaryDirectory() as directory:
            base = pathlib.Path(directory); source = base / 'edit.tsx'; source.write_text('approved fixture')
            out = base / 'fresh'
            with patch.object(m, 'preflight'), patch.object(m, 'execute') as execute, patch.object(m.time, 'monotonic', side_effect=[100, 101, 131, 132]):
                with self.assertRaises(m.subprocess.TimeoutExpired):
                    m.render('/unused', source, out, timeout=30, ffmpeg='/unused', ffprobe='/unused')
                execute.assert_not_called()
            receipt = json.loads((out / 'run.json').read_text())
            self.assertEqual(receipt['status'], 'incomplete')
            self.assertEqual(receipt['runtime_budget_seconds'], 30)

    def test_render_preserves_existing_output_and_rejects_unbounded_request(self):
        with tempfile.TemporaryDirectory() as directory:
            base = pathlib.Path(directory); source = base / 'edit.tsx'; source.write_text('approved fixture')
            out = base / 'output'; out.mkdir(); (out / 'keep').write_text('later work')
            with self.assertRaisesRegex(ValueError, 'already exists'): m.render('/unavailable', source, out)
            with self.assertRaisesRegex(ValueError, 'bounded'): m.render('/unavailable', source, base / 'new', frames=7201)
            self.assertEqual((out / 'keep').read_text(), 'later work'); self.assertFalse((base / 'new').exists())


if __name__ == '__main__': unittest.main()
