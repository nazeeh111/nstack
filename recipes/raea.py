#!/usr/bin/env python3
"""Pinned, isolated RAEA rendering; no upstream installer, hooks or provider access."""
import argparse, hashlib, json, os, pathlib, platform, re, shutil, signal, struct
import subprocess, tarfile, tempfile, time, urllib.request
from fractions import Fraction
P = pathlib.Path
VERSION = '0.1.0'
REVISION = 'd6f41c605ab71275162050cd08632cb56bd00e8a'
SHA256 = '730c02bafb4d00d94fc78c140d8f1a4c5bc0831269c938097599203671218228'
URL = 'https://github.com/shinyobjectz/raea/releases/download/v0.1.0/raea-0.1.0-macos-arm64.tar.gz'
SKILLS_REVISION = 'c507860150995eb7c22ef9db23dee636c832428a'
SKILLS_SHA256 = 'fc903796f9664dbe7bcd2b0610be33aa0c32beb0ae00e4cd6ef3d66530336459'
SKILLS_URL = 'https://codeload.github.com/shinyobjectz/raea-skills/tar.gz/' + SKILLS_REVISION
LICENSES = {'LICENSE': 'fe3ce8198545420f93b83a2fd02e6fff4a4414ffcb2309df50878adf39d1c392',
            'NOTICE': 'b1c99bce77af0225aa0dc888c9e717acb489b40a5fd2ca01c045469a815dee40'}
FILES_SHA256 = 'c18a9ab9963b0de2de3f9b0c1037376867bd685e8ecbe6d21c2798acfbe5ab49'
STATE = P(os.environ.get('NSTACK_STATE', P.home() / 'Library/Application Support/nstack'))
FATAL = re.compile(r'REFUSED|panicked at|GPU[^\n]*(?:error|stopped|out of memory)|wgpu[^\n]*error|Validation Error', re.I)


def digest(path):
    h = hashlib.sha256()
    with P(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()


def manifest(root):
    rows = {}
    for p in sorted(P(root).rglob('*')):
        key = str(p.relative_to(root))
        if p.is_symlink():
            if not p.resolve().is_relative_to(P(root).resolve()): raise ValueError('External runtime link')
            rows[key] = {'link': os.readlink(p)}
        elif p.is_file(): rows[key] = {'sha256': digest(p), 'executable': bool(p.stat().st_mode & 0o111)}
    return rows


def extract(archive, destination, select=None):
    """Extract files before links; refuse traversal, devices and external links."""
    destination = P(destination).resolve()
    with tarfile.open(archive) as tf:
        members = tf.getmembers(); names = set(); links = {m.name for m in members if m.issym()}
        for m in members:
            q = pathlib.PurePosixPath(m.name)
            if q.is_absolute() or '..' in q.parts or not q.parts: raise ValueError('Unsafe archive path')
            if m.name in names: raise ValueError('Duplicate archive path')
            names.add(m.name)
            if not (m.isdir() or m.isfile() or m.issym()): raise ValueError('Unsupported archive entry')
            if m.issym():
                if P(m.linkname).is_absolute() or not (destination / m.name).parent.joinpath(m.linkname).resolve().is_relative_to(destination):
                    raise ValueError('External archive link')
            if any(n != m.name and m.name.startswith(n.rstrip('/') + '/') for n in links):
                raise ValueError('Archive writes through a link')
        wanted = [m for m in members if select is None or select(m.name)]
        for m in wanted:
            if m.isdir(): (destination / m.name).mkdir(parents=True, exist_ok=True)
        for m in wanted:
            if m.isfile():
                p = destination / m.name; p.parent.mkdir(parents=True, exist_ok=True)
                with tf.extractfile(m) as src, p.open('xb') as dst: shutil.copyfileobj(src, dst)
                p.chmod(0o755 if m.mode & 0o111 else 0o644)
        for m in wanted:
            if m.issym():
                p = destination / m.name; p.parent.mkdir(parents=True, exist_ok=True); p.symlink_to(m.linkname)


def isolated_env(home, binary_dir):
    # No host HOME, provider variables, proxy credentials or ~/.raea/env.
    return {'HOME': str(home), 'PATH': str(binary_dir) + ':/usr/bin:/bin:/usr/sbin:/sbin',
            'LANG': 'en_US.UTF-8', 'RAEA_ENV_FILE': '/dev/null', 'RAEA_OFFLINE': '1',
            'RAEA_AUDIO_AUTOSETUP': '0', 'TMPDIR': tempfile.gettempdir()}


def attestation(archive, work, gh=None):
    url = 'https://api.github.com/repos/shinyobjectz/raea/attestations/sha256:' + SHA256
    with urllib.request.urlopen(urllib.request.Request(url, headers={'Accept': 'application/vnd.github+json'}), timeout=45) as r:
        response = json.load(r)
    entries = response.get('attestations', [])
    if not entries: raise ValueError('Official release build attestation unavailable')
    gh = gh or shutil.which('gh')
    if not gh: raise ValueError('Existing GitHub CLI required to verify the release attestation; no automatic installation')
    bundle = P(work) / 'attestation.json'; bundle.write_text(json.dumps(entries[0]['bundle']))
    home = P(work) / 'verification-home'; home.mkdir()
    env = isolated_env(home, P('/usr/bin')); env.update({'GH_CONFIG_DIR': str(home / 'gh'), 'GH_PROMPT_DISABLED': '1'})
    r = subprocess.run([str(gh), 'attestation', 'verify', str(archive), '--repo', 'shinyobjectz/raea',
        '--signer-workflow', 'shinyobjectz/raea/.github/workflows/release.yml', '--bundle', str(bundle), '--format', 'json'],
        env=env, capture_output=True, text=True, timeout=120)
    if r.returncode: raise ValueError('Official release attestation verification failed; no credentials requested')
    verified = json.loads(r.stdout)
    if not any(x['verificationResult']['signature']['certificate'].get('sourceRepositoryDigest') == REVISION for x in verified):
        raise ValueError('Unexpected attested source revision')
    return verified


def verify(root):
    root = P(root)
    if root.is_symlink() or not (root / 'SOURCE.json').is_file(): raise ValueError('Unowned runtime preserved')
    receipt = json.loads((root / 'SOURCE.json').read_text())
    if receipt.get('archive_sha256') != SHA256 or receipt.get('revision') != REVISION or receipt.get('skills_revision') != SKILLS_REVISION:
        raise ValueError('Runtime provenance differs; preserved')
    for name, expected in LICENSES.items():
        if not (root / name).is_file() or digest(root / name) != expected: raise ValueError('Runtime license or notice differs; preserved')
    rows = manifest(root / 'payload')
    if rows != receipt['files'] or hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()).hexdigest() != FILES_SHA256:
        raise ValueError('Installed runtime differs from its verified release; preserved')
    return root / 'payload/raea/bin/raea'


def install(state=STATE, archive=None, skills_archive=None, gh=None):
    if platform.system() != 'Darwin' or platform.machine() != 'arm64': raise ValueError('This pin supports Apple Silicon macOS only')
    parent = P(state).absolute() / 'native-tools/raea'; parent.mkdir(parents=True, exist_ok=True)
    if parent.resolve() != parent: raise ValueError('Linked runtime parent preserved')
    root = parent / VERSION
    if root.exists() or root.is_symlink(): return verify(root)
    with tempfile.TemporaryDirectory(prefix='.prepare-', dir=parent) as tmp:
        work = P(tmp); engine = P(archive) if archive else work / 'engine.tar.gz'; skills = P(skills_archive) if skills_archive else work / 'skills.tar.gz'
        if archive is None: urllib.request.urlretrieve(URL, engine)
        if digest(engine) != SHA256: raise ValueError('Official engine archive SHA256 mismatch')
        proof = attestation(engine, work, gh)
        if skills_archive is None: urllib.request.urlretrieve(SKILLS_URL, skills)
        if digest(skills) != SKILLS_SHA256: raise ValueError('Version-matched skill archive SHA256 mismatch')
        staged = work / 'ready'; payload = staged / 'payload'; payload.mkdir(parents=True)
        extract(engine, payload)
        prefix = 'raea-skills-' + SKILLS_REVISION
        extract(skills, payload, lambda n: n.startswith(prefix + '/skills/raea/') or n == prefix + '/LICENSE')
        source = {'repository': 'shinyobjectz/raea', 'version': VERSION, 'revision': REVISION, 'url': URL,
            'archive_sha256': SHA256, 'engine_license': 'FSL-1.1-ALv2; retained separately from MIT nstack',
            'skills_revision': SKILLS_REVISION, 'skills_sha256': SKILLS_SHA256, 'skills_license': 'Apache-2.0',
            'attestation_verified': True, 'files': manifest(payload)}
        if hashlib.sha256(json.dumps(source['files'], sort_keys=True, separators=(',', ':')).encode()).hexdigest() != FILES_SHA256: raise ValueError('Unexpected release payload')
        for name, expected in LICENSES.items():
            urllib.request.urlretrieve('https://raw.githubusercontent.com/shinyobjectz/raea/' + REVISION + '/' + name, staged / name)
            if digest(staged / name) != expected: raise ValueError('Runtime license provenance differs')
        (staged / 'SOURCE.json').write_text(json.dumps(source, indent=2) + '\n')
        (staged / 'ATTESTATION.json').write_text(json.dumps(proof, indent=2) + '\n')
        if root.exists() or root.is_symlink(): raise ValueError('Concurrent runtime installation preserved')
        os.rename(staged, root)
    return verify(root)


def execute(args, cwd, env, prefix, timeout):
    with P(str(prefix) + '.stdout.log').open('wb') as stdout, P(str(prefix) + '.stderr.log').open('wb') as stderr:
        p = subprocess.Popen([str(x) for x in args], cwd=cwd, env=env, stdout=stdout, stderr=stderr, start_new_session=True)
        try: return p.wait(timeout=timeout)
        except BaseException:
            try: os.killpg(p.pid, signal.SIGTERM)
            except ProcessLookupError: pass
            try: p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try: os.killpg(p.pid, signal.SIGKILL)
                except ProcessLookupError: pass
                p.wait()
            raise


def check_artifact(out, width, height, fps, frames, probe):
    out = P(out); doc = json.loads((out / 'render.json').read_text())
    if doc.get('not_applied') or doc.get('clipping'): raise ValueError('Render reports unsupported or clipped content')
    if (doc.get('width'), doc.get('height'), doc.get('fps')) != (width, height, fps): raise ValueError('Manifest dimensions or timing differ')
    if [x.get('frame') for x in doc.get('frames', [])] != list(range(frames)): raise ValueError('Manifest is incomplete')
    video = next((s for s in probe.get('streams', []) if s.get('codec_type') == 'video'), None)
    if video is None or video.get('codec_name') != 'h264': raise ValueError('Expected independently decoded H264 video')
    if (video.get('width'), video.get('height'), int(video.get('nb_read_frames', -1))) != (width, height, frames): raise ValueError('Decoded video dimensions or frame count differ')
    if Fraction(video['avg_frame_rate']) != Fraction(fps): raise ValueError('Decoded video rate differs')
    if abs(float(probe['format']['duration']) - frames / fps) > 1 / fps + .001: raise ValueError('Decoded video duration differs')
    for name in ('render.stdout.log', 'render.stderr.log'):
        if FATAL.search((out / name).read_text(errors='replace')): raise ValueError('Runtime reported a GPU/render failure despite its exit code')


def preflight(binary, source, out, env, width, height, fps, frames, timeout):
    # This release keeps the Composition's settings instead of CLI overrides.
    # Read the actual SDK registry, then reject a mismatch before video rendering.
    script = P(out) / 'preflight.ts'
    expected = {'width': width, 'height': height, 'fps': fps, 'durationInFrames': frames}
    script.write_text('import ' + json.dumps(str(source)) + ';\n'
        'import {getCompositions} from "raea";\nconst c=getCompositions();\nconst e=' + json.dumps(expected) + ';\n'
        'if(c.length!==1||Object.keys(e).some(k=>c[0][k]!==e[k]))'
        'throw new Error("NSTACK_PREFLIGHT_MISMATCH: expected one composition with "+JSON.stringify(e));\n'
        'export default function(){}\n')
    # Keep the script's5s execution cap, allowing bounded cold bootstrap time.
    script_limit, phase_limit = min(5, timeout), min(30, timeout)
    code = execute([binary, 'run', script, '--timeout', script_limit], P(source).parent, env, P(out) / 'preflight', phase_limit)
    if code: raise ValueError('Composition settings do not match the requested bounded render, or metadata preflight failed; inspect preflight logs')


def render(binary, source, outdir, width=640, height=360, fps=30, frames=90, timeout=180, ffmpeg=None, ffprobe=None):
    if not (64 <= width <= 3840 and 64 <= height <= 2160 and 1 <= fps <= 60 and 1 <= frames <= 7200 and 1 <= timeout <= 1800):
        raise ValueError('Render exceeds the bounded dimensions, rate, frames or timeout')
    source = P(source).resolve(strict=True)
    if not source.is_file() or source.suffix != '.tsx': raise ValueError('Provide an existing approved local TSX composition')
    out = P(outdir).absolute()
    if out.exists() or out.is_symlink(): raise ValueError('Output already exists; choose a fresh task-owned directory')
    ffmpeg = ffmpeg or shutil.which('ffmpeg'); ffprobe = ffprobe or shutil.which('ffprobe')
    if not ffmpeg or not ffprobe: raise ValueError('Existing FFmpeg and FFprobe required for independent artifact checks')
    out.mkdir(parents=True); home = out / 'isolated-home'; home.mkdir(); env = isolated_env(home, P(binary).parent)
    before = digest(source); start = time.monotonic(); result = {'version': VERSION, 'source_sha256': before,
        'offline': True, 'credentials_inherited': False, 'paid_features': False, 'runtime_budget_seconds': timeout, 'status': 'incomplete'}
    def remaining():
        left = timeout - (time.monotonic() - start)
        if left <= 0: raise subprocess.TimeoutExpired('RAEA pipeline', timeout)
        return left
    try:
        preflight(binary, source, out, env, width, height, fps, frames, remaining())
        if digest(source) != before: raise ValueError('Composition changed during preflight')
        result['composition_settings_checked_before_video_render'] = True
        code = execute([binary, 'render', source, '-o', out / 'render.mp4', '--manifest', out / 'render.json',
            '--w', width, '--h', height, '--fps', fps, '--frames', frames], source.parent, env, out / 'render', remaining())
        if code: raise ValueError('Renderer failed; partial outputs retained')
        probe = subprocess.run([str(ffprobe), '-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', str(out / 'render.mp4')],
            capture_output=True, text=True, env=env, timeout=remaining(), check=True)
        if probe.stderr.strip(): raise ValueError('Independent decoder reported an error')
        doc = json.loads(probe.stdout); (out / 'ffprobe.json').write_text(json.dumps(doc, indent=2))
        check_artifact(out, width, height, fps, frames, doc)
        sample = sorted({0, frames // 2, frames - 1}); selection = 'select=' + '+'.join('eq(n\\,%d)' % n for n in sample)
        code = execute([ffmpeg, '-v', 'error', '-xerror', '-i', out / 'render.mp4', '-vf', selection, '-vsync', '0', out / 'frame-%02d.png'],
            out, env, out / 'decode', remaining())
        if code: raise ValueError('Independent full decode failed')
        pngs = sorted(out.glob('frame-*.png'))
        if len(pngs) != len(sample): raise ValueError('Missing independently decoded preview frames')
        for png in pngs:
            raw = png.read_bytes()
            if raw[:8] != b'\x89PNG\r\n\x1a\n' or struct.unpack('>II', raw[16:24]) != (width, height): raise ValueError('Invalid decoded preview')
        if digest(source) != before: raise ValueError('Composition changed during rendering; reconcile before acceptance')
        result.update({'status': 'technical_checks_passed_requires_visual_review', 'frames': frames, 'fps': fps,
            'size': [width, height], 'preview_frames': sample, 'video_sha256': digest(out / 'render.mp4'),
            'manifest_sha256': digest(out / 'render.json'), 'known_limit': 'Release0.1.0 predates an upstream GPU-error fix. Inspect decoded frames and current source before accepting; these checks do not prove every possible partial render is detected.'})
    except (ValueError, OSError, subprocess.SubprocessError) as e:
        result['error'] = str(e); raise
    finally:
        result['elapsed_seconds'] = round(time.monotonic() - start, 3); (out / 'run.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--state', default=str(STATE)); sub = p.add_subparsers(dest='command', required=True)
    a = sub.add_parser('install'); a.add_argument('--archive'); a.add_argument('--skills-archive'); a.add_argument('--gh')
    sub.add_parser('verify'); sub.add_parser('help')
    a = sub.add_parser('run'); a.add_argument('--source', required=True); a.add_argument('--outdir', required=True); a.add_argument('--offline', action='store_true', help='Explicit offline mode; this recipe always enforces it')
    for flag, default in [('width',640),('height',360),('fps',30),('frames',90),('timeout',180)]: a.add_argument('--' + flag, type=int, default=default)
    args = p.parse_args(); root = P(args.state) / 'native-tools/raea' / VERSION
    try:
        binary = install(args.state, args.archive, args.skills_archive, args.gh) if args.command == 'install' else verify(root)
        if args.command in ('install', 'verify'): print(json.dumps({'binary': str(binary), 'version': VERSION, 'sha256': digest(binary), 'skill_support': str(root / 'payload' / ('raea-skills-' + SKILLS_REVISION) / 'skills/raea')}))
        elif args.command == 'help':
            with tempfile.TemporaryDirectory(prefix='nstack-raea-help-') as home:
                subprocess.run([str(binary), '--help'], env=isolated_env(home, binary.parent), check=True, timeout=30)
        else: print(json.dumps(render(binary, args.source, args.outdir, args.width, args.height, args.fps, args.frames, args.timeout), indent=2))
    except (ValueError, OSError, subprocess.SubprocessError) as e: p.exit(2, str(e) + '\n')
if __name__ == '__main__': main()
