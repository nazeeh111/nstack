#!/usr/bin/env python3
"""Pinned NVIDIA SkillSpector Stage 1 for explicit local agent-skill/source scopes."""
from __future__ import annotations

import argparse
import errno
from email.parser import BytesParser
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time

REVISION = '9dbf4fc75386169275e5f18c47686cb0d7274afa'
TREE = '9fc164e4724c2e993e95205e800896afb0eb71cd'
VERSION = '2.12.0'
SOURCE_HASH = 'c65e429b19dea27751dcf2873eb4fe8963c378eba3340d53be1a133ef1697ab4'
LOCK_HASH = '11f7b9c9873573222fe6990219226054fa342f50e71767949f6a5040b3ff8ca0'
REPOSITORY = 'https://github.com/NVIDIA/skillspector.git'
STATE = Path(os.environ.get('NSTACK_STATE', Path.home() / 'Library/Application Support/nstack'))
MAX_FILES = 10_000
MAX_BYTES = 64 * 1024 * 1024
SENSITIVE_NAMES = {'.env', '.env.local', '.env.production', '.env.development', 'auth.json',
                   'credentials.json', 'credentials', 'id_rsa', 'id_ed25519'}
PROBE = '''import errno,json,socket
s=socket.socket()
try:
 s.connect(('127.0.0.1',9))
except OSError as e:
 print(json.dumps({'errno':e.errno,'network_denied':e.errno in (errno.EPERM,errno.EACCES)}))
else:
 print(json.dumps({'network_denied':False}))
finally:
 s.close()
'''


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def json_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')
    Path(path).chmod(0o600)


def concrete(path):
    """Reject linked output/state ancestors before any writes."""
    path = Path(path).absolute()
    if path.resolve() != path:
        raise ValueError('State/output path contains a symlink; preserved')
    return path


def isolated_env(home, tmp, binary_dirs=()):
    # Deliberately construct rather than filter host environment/credential values.
    return {'HOME': str(home), 'PATH': ':'.join([*(str(x) for x in binary_dirs), '/usr/bin', '/bin', '/usr/sbin', '/sbin']),
            'LANG': 'en_US.UTF-8', 'TMPDIR': str(tmp), 'PYTHONNOUSERSITE': '1',
            'PYTHONDONTWRITEBYTECODE': '1', 'LANGSMITH_TRACING': 'false',
            'LANGCHAIN_TRACING_V2': 'false', 'SKILLSPECTOR_OSV_TIMEOUT': '0',
            'SKILLSPECTOR_BUILD_REVISION': REVISION, 'UV_NO_CONFIG': '1',
            'UV_PYTHON_DOWNLOADS': 'never', 'GIT_CONFIG_NOSYSTEM': '1',
            'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_TERMINAL_PROMPT': '0',
            'GIT_ASKPASS': '/usr/bin/false', 'GIT_ALLOW_PROTOCOL': 'https'}


def capture(argv, cwd, env, timeout=120):
    argv = [str(x) for x in argv]
    proc = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except BaseException:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.communicate()
        raise
    if proc.returncode:
        raise subprocess.CalledProcessError(proc.returncode, argv, stdout, stderr)
    return subprocess.CompletedProcess(argv, proc.returncode, stdout, stderr)


def build_cache_metadata(cache):
    # Observe downloaded public distribution metadata, without importing packages.
    rows = []
    for p in sorted(Path(cache).rglob('METADATA')):
        if p.parent.name.endswith('.dist-info') and not p.is_symlink():
            data = p.read_bytes(); meta = BytesParser().parsebytes(data, headersonly=True)
            rows.append({'name': meta.get('Name'), 'version': meta.get('Version'),
                         'metadata_sha256': hashlib.sha256(data).hexdigest()})
    return rows


def source_inventory(source, git, env):
    commit = capture([git, 'rev-parse', 'HEAD'], source, env).stdout.strip()
    tree = capture([git, 'rev-parse', 'HEAD^{tree}'], source, env).stdout.strip()
    if (commit, tree) != (REVISION, TREE):
        raise ValueError('Source Git pin/tree mismatch')
    names = capture([git, 'ls-files', '-z'], source, env).stdout.split('\0')[:-1]
    rows = {}
    for name in names:
        p = source / name
        if p.is_symlink() or not p.is_file():
            raise ValueError('Unexpected linked/missing pinned source file')
        rows[name] = digest(p)
    if json_hash(rows) != SOURCE_HASH or digest(source / 'uv.lock') != LOCK_HASH:
        raise ValueError('Pinned source or uv.lock bytes differ')
    capture([git, '-c', 'core.hooksPath=/dev/null', 'diff', '--exit-code', 'HEAD', '--'], source, env)
    return rows


def runtime_inventory(root):
    rows = {}
    for p in sorted((root / '.venv').rglob('*')):
        name = p.relative_to(root).as_posix()
        if p.is_symlink():
            rows[name] = {'link': os.readlink(p)}
        elif p.is_file():
            rows[name] = {'sha256': digest(p), 'mode': stat.S_IMODE(p.stat().st_mode)}
    return rows


def runtime_root(state):
    return concrete(state) / 'native-tools/skillspector' / REVISION


def verify(root):
    root = concrete(root)
    receipt = json.loads((root / 'SOURCE.json').read_text())
    if (receipt.get('revision'), receipt.get('tree'), receipt.get('lock_sha256')) != (REVISION, TREE, LOCK_HASH):
        raise ValueError('Runtime provenance mismatch; preserved')
    git = shutil.which('git')
    if not git:
        raise ValueError('Existing Git binary required for source verification')
    with tempfile.TemporaryDirectory(prefix='nstack-skillspector-verify-', dir='/private/tmp') as tmp:
        home = Path(tmp) / 'home'; home.mkdir()
        rows = source_inventory(root, git, isolated_env(home, tmp))
    if receipt.get('source_files') != rows or receipt.get('runtime_files') != runtime_inventory(root):
        raise ValueError('Installed source/runtime bytes changed; preserved')
    python = root / '.venv/bin/python'
    if digest(python.resolve(strict=True)) != receipt['interpreter_sha256']:
        raise ValueError('Underlying Python interpreter changed; re-review runtime')
    return root / '.venv/bin/skillspector'


def sandbox_profile(root, work):
    # This boundary enforces network denial only. Filesystem scope is the explicit
    # materialized input plus clean HOME/environment, not a claimed OS read sandbox.
    concrete(root); concrete(work)
    return '(version 1)\n(allow default)\n(deny network*)'


def network_guard(root, work, env):
    if platform.system() != 'Darwin' or not Path('/usr/bin/sandbox-exec').is_file():
        raise ValueError('Native macOS sandbox-exec network denial is required; no fallback')
    profile = sandbox_profile(root, work)
    prefix = ['/usr/bin/sandbox-exec', '-p', profile]
    result = capture([*prefix, root / '.venv/bin/python', '-I', '-B', '-c', PROBE], work, env, 30)
    proof = json.loads(result.stdout)
    if proof.get('network_denied') is not True or proof.get('errno') not in (errno.EPERM, errno.EACCES):
        raise ValueError('OS network denial probe failed; upstream scanner not started')
    return prefix, proof


def install(state=STATE, python=None, uv=None):
    """Explicit only. Failed/incomplete roots are preserved, never overwritten."""
    if platform.system() != 'Darwin':
        raise ValueError('This reviewed offline runtime recipe currently supports macOS')
    git = shutil.which('git'); uv = uv or shutil.which('uv')
    python = Path(python or sys.executable).resolve(strict=True)
    if not git or not uv:
        raise ValueError('Existing Git and uv required; no automatic bootstrap')
    root = runtime_root(state)
    if root.exists() or root.is_symlink():
        return verify(root)
    root.parent.mkdir(parents=True, exist_ok=True)
    root.mkdir(mode=0o700)  # stable venv shebang path; concurrent/incomplete roots fail closed
    write_json(root / 'INSTALLING.json', {'revision': REVISION, 'status': 'incomplete'})
    with tempfile.TemporaryDirectory(prefix='nstack-skillspector-install-', dir='/private/tmp') as directory:
        work = Path(directory); home = work / 'home'; home.mkdir()
        env = isolated_env(home, work, [python.parent, Path(uv).parent])
        env['UV_CACHE_DIR'] = str(work / 'uv-cache')
        logdir = root / 'install-logs'; logdir.mkdir(mode=0o700)
        step_index = 0
        def step(argv, timeout=120):
            nonlocal step_index
            step_index += 1
            try:
                result = capture(argv, root, env, timeout)
            except subprocess.CalledProcessError as exc:
                write_json(logdir / f'{step_index:02d}.json', {'argv': [str(x) for x in argv],
                    'returncode': exc.returncode, 'stdout': exc.stdout, 'stderr': exc.stderr})
                raise
            write_json(logdir / f'{step_index:02d}.json', {'argv': [str(x) for x in argv],
                'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
            return result
        step([git, 'init', '.'])
        step([git, '-c', 'core.hooksPath=/dev/null', '-c', 'credential.helper=',
                 '-c', 'core.askPass=', 'fetch', '--depth=1', REPOSITORY, REVISION])
        step([git, '-c', 'core.hooksPath=/dev/null', 'checkout', '--detach', REVISION])
        source_files = source_inventory(root, git, env)
        info = json.loads(capture([python, '-I', '-B', '-c',
            'import json,sys;print(json.dumps({"version":list(sys.version_info[:3]),"prefix":sys.base_prefix}))'], root, env).stdout)
        if not (3, 12) <= tuple(info['version'][:2]) < (3, 16):
            raise ValueError('Use an existing supported Python >=3.12,<3.16')
        # Frozen artifacts, isolated durable venv, no extras/dev, no user uv config or Python download.
        step([uv, '--no-config', 'sync', '--frozen', '--no-dev', '--no-editable',
                 '--python', python], 900)
        health = step([uv, '--no-config', 'pip', 'check', '--python', root / '.venv/bin/python'])
        distributions = json.loads(step([uv, '--no-config', 'pip', 'list', '--format', 'json',
                                           '--python', root / '.venv/bin/python']).stdout)
        source_inventory(root, git, env)
        prefix, proof = network_guard(root, work, env)
        version = capture([*prefix, root / '.venv/bin/skillspector', '--version'], work, env, 30).stdout.strip()
        if f'v{VERSION}' not in version:
            raise ValueError('Installed scanner version mismatch')
        receipt = {'repository': REPOSITORY, 'revision': REVISION, 'tree': TREE, 'version': VERSION,
            'lock_sha256': LOCK_HASH, 'source_files': source_files, 'runtime_files': runtime_inventory(root),
            'interpreter': str(python), 'interpreter_sha256': digest(python), 'python': info,
            'uv_sha256': digest(Path(uv).resolve()), 'distributions': distributions,
            'downloaded_distribution_metadata': build_cache_metadata(work / 'uv-cache'),
            'dependency_health': health.stdout + health.stderr, 'network_guard': proof,
            'version_observed': version, 'provider_calls': False,
            'build_backend_limit': 'Standard hatchling build backend resolved by uv; build-isolation distributions are not retained in runtime inventory. Runtime artifact bytes and installed metadata are recorded, not a full dependency-source audit.'}
        write_json(root / 'SOURCE.json', receipt)
        (root / 'INSTALLING.json').unlink()
    return verify(root)


def snapshot(target, destination):
    selected = Path(target).absolute()
    source = selected.resolve(strict=True)  # root links intentionally resolved and recorded
    if ({'.ssh', '.aws', '.gnupg', 'Keychains'} & set(source.parts) or
            not source.is_dir() or source == Path(source.anchor) or source == Path.home()):
        raise ValueError('Select an explicit source component, not a credential store or broad home/root')
    destination.mkdir()
    rows = {}; skipped = []; used = 0
    # Do not follow directory links during discovery. Internal file links are materialized.
    for base, dirs, files in os.walk(source, followlinks=False):
        for name in list(dirs):
            p = Path(base) / name
            if p.is_symlink():
                raise ValueError('Nested directory symlink requires an explicitly materialized source scope')
            if name == '.git':
                dirs.remove(name); skipped.append(str(p.relative_to(source)) + '/')
        for name in sorted(files):
            p = Path(base) / name; rel = p.relative_to(source).as_posix()
            if name == '.git' or name in SENSITIVE_NAMES or name.startswith('.env.') and name not in {'.env.example', '.env.sample', '.env.template'}:
                skipped.append(rel); continue
            actual = p.resolve(strict=True)
            if not actual.is_relative_to(source):
                raise ValueError('Nested file link escapes the selected component')
            if not actual.is_file() or not stat.S_ISREG(actual.stat().st_mode):
                raise ValueError('Unsupported non-regular component file')
            if len(rows) >= MAX_FILES or used + actual.stat().st_size > MAX_BYTES:
                raise ValueError('Component exceeds snapshot bound; split into explicit scopes')
            b = actual.read_bytes(); used += len(b)
            q = destination / rel; q.parent.mkdir(parents=True, exist_ok=True); q.write_bytes(b); q.chmod(0o700 if actual.stat().st_mode & 0o111 else 0o600)
            # Execute mode retained only as metadata; copied scripts are never launched.
            rows[rel] = {'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b),
                         'source_executable': bool(actual.stat().st_mode & 0o111)}
    return {'selected': str(selected), 'resolved': str(source), 'files': rows,
            'skipped': skipped, 'bytes': used, 'sha256': json_hash(rows)}


def execute(argv, cwd, env, stdout, stderr, timeout):
    with Path(stdout).open('xb') as out, Path(stderr).open('xb') as err:
        proc = subprocess.Popen([str(x) for x in argv], cwd=cwd, env=env,
                                stdout=out, stderr=err, start_new_session=True)
        try:
            return proc.wait(timeout=timeout)
        except BaseException:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
            raise


def report_summary(report, code):
    if not isinstance(report, dict) or code not in (0, 1):
        raise ValueError('Scanner failed; inspect retained raw report/logs')
    if report.get('execution_successful') is not True:
        raise ValueError('Scanner reports unsuccessful execution')
    for key in ('issues', 'components'):
        if not isinstance(report.get(key), list):
            raise ValueError('Scanner report missing issue/component evidence')
    meta = report.get('metadata', {})
    if not isinstance(meta, dict):
        raise ValueError('Scanner report metadata is malformed')
    if meta.get('skillspector_version') != VERSION:
        raise ValueError('Scanner report version differs from pinned runtime')
    if meta.get('llm_requested') is not False or meta.get('inference_usage') or meta.get('llm_calls_attempted', 0):
        raise ValueError('Static-only scanner contract violated')
    completeness = report.get('analysis_completeness')
    if not isinstance(completeness, dict) or 'is_complete' not in completeness:
        raise ValueError('Scanner report missing actual completeness evidence')
    return {'status': 'scanned_requires_source_adjudication', 'returncode': code,
            'risk_assessment': report.get('risk_assessment'), 'issues': len(report['issues']),
            'components': report['components'], 'analysis_completeness': completeness,
            'live_osv': 'unavailable_offline', 'semantic_scanner': 'disabled',
            'dependency_artifact_contents': 'not_requested', 'transitive_fetch': 'not_requested'}


def run(root, targets, outdir, timeout=300):
    if not targets or not 1 <= timeout <= 1800:
        raise ValueError('Explicit targets and a 1-1800 second per-component timeout required')
    binary = verify(root)
    root = concrete(root); out = concrete(outdir)
    if out.exists() or out.is_symlink():
        raise ValueError('Output exists; choose a fresh private task directory')
    # Keep outputs outside all selected source roots, avoiding self-inclusion.
    for target in targets:
        if out.is_relative_to(Path(target).resolve(strict=True)):
            raise ValueError('Output must be outside scan sources')
    out.mkdir(parents=True, mode=0o700)
    receipt = {'revision': REVISION, 'version': VERSION, 'status': 'incomplete',
               'offline': True, 'provider_calls': False, 'results': []}
    try:
        with tempfile.TemporaryDirectory(prefix='nstack-skillspector-run-', dir='/private/tmp') as directory:
            work = Path(directory); home = work / 'home'; home.mkdir()
            env = isolated_env(home, work)
            prefix, proof = network_guard(root, work, env)
            receipt['network_guard'] = proof
            for i, target in enumerate(targets):
                item = out / f'component-{i:04d}'; item.mkdir(mode=0o700)
                snap = item / 'snapshot'
                inventory = snapshot(target, snap)
                write_json(item / 'input.json', inventory)
                # Report is stdout: it avoids granting scanner write access to durable evidence.
                argv = [*prefix, binary, 'scan', snap, '--no-llm', '--format', 'json']
                start = time.monotonic()
                raw_report = work / f'report-{i:04d}.json'; raw_error = work / f'stderr-{i:04d}.log'
                try:
                    code = execute(argv, work, env, raw_report, raw_error, timeout)
                finally:
                    for src, dst in [(raw_report, item / 'report.json'), (raw_error, item / 'stderr.log')]:
                        if src.is_file():
                            shutil.copyfile(src, dst); dst.chmod(0o600)
                current = {}
                for p in sorted(snap.rglob('*')):
                    if p.is_symlink():
                        raise ValueError('Scan snapshot gained a link during upstream execution')
                    if p.is_file():
                        b = p.read_bytes(); current[p.relative_to(snap).as_posix()] = {
                            'sha256': hashlib.sha256(b).hexdigest(), 'bytes': len(b),
                            'source_executable': bool(p.stat().st_mode & 0o111)}
                if current != inventory['files']:
                    raise ValueError('Scan input changed during upstream execution')
                summary = report_summary(json.loads((item / 'report.json').read_text()), code)
                summary.update({'target': str(target), 'input_sha256': inventory['sha256'],
                                'skipped_input_paths': inventory['skipped'],
                                'report_sha256': digest(item / 'report.json'),
                                'elapsed_seconds': round(time.monotonic() - start, 3)})
                write_json(item / 'summary.json', summary)
                receipt['results'].append(summary)
            verify(root)
            receipt['status'] = 'scanned_requires_source_adjudication'
    except (ValueError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        receipt['error'] = str(exc)
        raise
    finally:
        write_json(out / 'run.json', receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', default=str(STATE))
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('install'); p.add_argument('--python'); p.add_argument('--uv')
    sub.add_parser('verify'); sub.add_parser('help')
    p = sub.add_parser('run'); p.add_argument('--target', action='append', required=True)
    p.add_argument('--outdir', required=True); p.add_argument('--timeout', type=int, default=300)
    args = parser.parse_args(); root = runtime_root(args.state)
    try:
        if args.command == 'install':
            binary = install(args.state, args.python, args.uv)
        elif args.command == 'run':
            print(json.dumps(run(root, args.target, args.outdir, args.timeout), indent=2)); return 0
        else:
            binary = verify(root)
        if args.command == 'help':
            with tempfile.TemporaryDirectory(prefix='nstack-skillspector-help-', dir='/private/tmp') as directory:
                work = Path(directory); home = work / 'home'; home.mkdir()
                env = isolated_env(home, work); prefix, _ = network_guard(root, work, env)
                print(capture([*prefix, binary, 'scan', '--help'], work, env, 30).stdout)
        else:
            print(json.dumps({'binary': str(binary), 'revision': REVISION, 'version': VERSION,
                              'source_receipt': str(root / 'SOURCE.json')}))
        return 0
    except (ValueError, OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        parser.exit(2, str(exc) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
