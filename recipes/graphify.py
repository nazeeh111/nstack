#!/usr/bin/env python3
"""Pinned on-demand Graphify code-only CLI. No upstream installer or host wiring."""
from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
import zipfile

VERSION = '0.9.106'
REVISION = '35d1d2038b9e9d470f117bf8f2473d415b5f5358'
ARCHIVE_HASH = '24da41e0f10c4ebef992745ddaa5b61d860bc2564cd51d219bdfd0f2f9f19d4c'
WHEEL_HASH = '3d1003bc420f4413da555d78946a151ccd41ec3decc583c5b2f034decf58c50e'
URL = 'https://codeload.github.com/Graphify-Labs/graphify/tar.gz/' + REVISION
ASSETS = Path(__file__).resolve().parent.parent / 'integrations/graphify'
ASSET_HASHES = {
    'SOURCE.json': 'facbb4e6e7a08f2af9afff1e4b484a43697d75a454fa95a3e5bb4ceb53b05560',
    'wheels-macos-arm64-cp312.json': '1dc325a177f37b03b8d10a6cb7ff32b4cdda72fcaacd5997ec4fe23dd2375e10',
    'DEPENDENCIES.json': '27acbb7a9e2d957731b88bf81373e345ae80a152ecf93a23c16fbe11cb5efaf8',
    'core-requirements.lock': '9c4a66a4559ca28ca89c1ebaa486fc1684801c555c783b86e2b97181adbe7bd7',
    'build-requirements.lock': 'b709b16a24023233b6c7d4d2f66707a4b7ae2844ef14ee81442de7cc3247c73f',
}
STATE = Path(os.environ.get('NSTACK_STATE', Path.home() / 'Library/Application Support/nstack'))
SENSITIVE = re.compile(r'(^\.env($|\.)|^\.?(ssh|gnupg|aws|gcloud|secrets?|credentials?|keychains?|obsidian)$|'
                       r'^(auth|credentials|secrets)\.json$|\.(pem|p12|pfx|key)$|^id_(rsa|ed25519)$)', re.I)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()


def concrete(path):
    p = Path(path).absolute()
    if p.resolve() != p: raise ValueError('Linked source/output/state path refused; preserved')
    return p


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2) + '\n')


def runtime_root(state=STATE):
    return concrete(state) / 'native-tools/graphify' / (VERSION + '-' + REVISION[:12])


def inventory(root):
    rows = {}
    for p in sorted(Path(root).rglob('*')):
        key = str(p.relative_to(root))
        if p.is_symlink(): rows[key] = {'link': os.readlink(p)}
        elif p.is_file(): rows[key] = {'sha256': digest(p), 'executable': bool(p.stat().st_mode & 0o111)}
        elif not p.is_dir(): raise ValueError('Unexpected special runtime file')
    return rows


def assets():
    for name, expected in ASSET_HASHES.items():
        if digest(ASSETS / name) != expected: raise ValueError('Integration asset changed: ' + name)
    source = json.loads((ASSETS / 'SOURCE.json').read_text())
    for row in source['upstream_files']:
        if digest(ASSETS / row['path']) != row['sha256']: raise ValueError('Upstream reference changed')
    dependencies = json.loads((ASSETS / 'DEPENDENCIES.json').read_text())
    for package in dependencies['packages']:
        for row in package['license_files']:
            if digest(ASSETS / row['path']) != row['sha256']: raise ValueError('Dependency notice changed')
    return json.loads((ASSETS / 'wheels-macos-arm64-cp312.json').read_text())


def clean_env(home, tmp, build=False):
    # Construct from constants, never inherit provider/proxy/account variables.
    home, tmp = Path(home), Path(tmp)
    return {'HOME': str(home), 'PATH': '/usr/bin:/bin' if build else str(home / 'empty-bin'),
            'LANG': 'en_US.UTF-8', 'TZ': 'UTC', 'TMPDIR': str(tmp), 'XDG_CONFIG_HOME': str(home / 'config'),
            'XDG_CACHE_HOME': str(home / 'cache'), 'PYTHONNOUSERSITE': '1', 'PYTHONDONTWRITEBYTECODE': '1',
            'GRAPHIFY_BACKEND': 'none', 'GRAPHIFY_QUERY_LOG_DISABLE': '1', 'GRAPHIFY_NO_CTA': '1',
            'GRAPHIFY_NO_TIPS': '1', 'GRAPHIFY_ALLOW_LOCAL_PROVIDERS': '0', 'GRAPHIFY_GOOGLE_WORKSPACE': '0',
            'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_TERMINAL_PROMPT': '0',
            'UV_NO_CONFIG': '1', 'UV_PYTHON_DOWNLOADS': 'never', 'UV_KEYRING_PROVIDER': 'disabled',
            'UV_CACHE_DIR': str(Path(tmp) / 'uv-cache'), 'PIP_CONFIG_FILE': '/dev/null',
            'SOURCE_DATE_EPOCH': '1794346676'}


def capture(argv, cwd, env, timeout=120):
    p = subprocess.Popen([str(x) for x in argv], cwd=cwd, env=env, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, start_new_session=True)
    try: stdout, stderr = p.communicate(timeout=timeout)
    except BaseException:
        try: os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError: pass
        p.communicate()
        raise
    result = {'argv': [str(x) for x in argv], 'returncode': p.returncode, 'stdout': stdout, 'stderr': stderr}
    return result


def checked(argv, cwd, env, log, timeout=120):
    result = capture(argv, cwd, env, timeout)
    write_json(log, result)
    if result['returncode']: raise ValueError('Subprocess failed; inspect ' + str(log))
    return result


def sandbox(profile):
    if platform.system() != 'Darwin' or not Path('/usr/bin/sandbox-exec').is_file():
        raise ValueError('Reviewed macOS sandbox-exec required; no unsandboxed fallback')
    return ['/usr/bin/sandbox-exec', '-p', profile]


def profile_for(root, source, out, interpreter):
    readable = [str(root), str(source), str(out), str(Path(interpreter).resolve().parent.parent)]
    return ('(version 1)\n(allow default)\n(deny network*)\n'
            # Restrict personal home contents while retaining native loader access
            # to OS caches. This is not an all-filesystem read allowlist.
            '(deny file-read-data file-read-xattr (require-all (subpath "/Users") ' + ' '.join('(require-not (subpath ' + json.dumps(p) + '))' for p in readable) + '))\n'
            '(deny file-write* (require-not (subpath ' + json.dumps(str(out)) + ')))\n')


def download(url, target, expected):
    # Anonymous HTTPS, no inherited proxy or credential-store integration.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(url, timeout=60) as response, Path(target).open('xb') as stream:
        shutil.copyfileobj(response, stream)
    if digest(target) != expected: raise ValueError('Download hash mismatch: ' + str(target))


def unpack(archive, target):
    target = Path(target); target.mkdir()
    with tarfile.open(archive) as tf:
        seen = set()
        for member in tf.getmembers():
            path = PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or member.name in seen: raise ValueError('Unsafe archive path')
            seen.add(member.name)
            if not (member.isfile() or member.isdir()): raise ValueError('Linked/special archive entry refused')
            destination = target.joinpath(*path.parts)
            if member.isdir(): destination.mkdir(parents=True, exist_ok=True)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                with tf.extractfile(member) as source, destination.open('xb') as stream: shutil.copyfileobj(source, stream)
                destination.chmod(0o755 if member.mode & 0o111 else 0o644)
    return target / ('graphify-' + REVISION)


def verify(root):
    assets(); root = concrete(root)
    if root.is_symlink() or not (root / 'READY.json').is_file(): raise ValueError('Unowned/incomplete runtime preserved')
    receipt = json.loads((root / 'READY.json').read_text())
    if receipt.get('revision') != REVISION or receipt.get('wheel_sha256') != WHEEL_HASH: raise ValueError('Runtime provenance differs')
    if inventory(root / '.venv') != receipt['runtime_files']: raise ValueError('Runtime files changed; preserved')
    python = root / '.venv/bin/python'
    if digest(python.resolve(strict=True)) != receipt['interpreter_sha256']: raise ValueError('Base interpreter changed; re-review it')
    return python


def prepare(state=STATE, python=None, uv=None, wheelhouse=None, archive=None):
    if platform.system() != 'Darwin' or platform.machine() != 'arm64': raise ValueError('This lock supports Apple Silicon macOS only')
    spec = assets(); root = runtime_root(state)
    if root.exists() or root.is_symlink(): return verify(root)
    if python is None: raise ValueError('Pass an existing CPython3.12 interpreter; no interpreter download')
    python = Path(python).resolve(strict=True); uv = Path(uv or shutil.which('uv') or '').resolve(strict=True)
    if not uv.is_file(): raise ValueError('Existing uv required; no automatic bootstrap')
    prefix = sandbox('(version 1) (allow default) (deny network*)')
    with tempfile.TemporaryDirectory(prefix='nstack-graphify-install-', dir='/private/tmp') as name:
        work = Path(name); home = work / 'home'; home.mkdir(); env = clean_env(home, work, build=True)
        probe = capture([*prefix, python, '-I', '-S', '-c', 'import sys,platform;print(platform.python_implementation(),sys.version_info[:2])'], work, env)
        if probe['returncode'] or probe['stdout'].strip() != 'CPython (3, 12)': raise ValueError('Existing CPython3.12 required')
        root.parent.mkdir(parents=True, exist_ok=True); root.mkdir(mode=0o700)
        logs = root / 'install-logs'; logs.mkdir(); write_json(root / 'INSTALLING.json', {'revision': REVISION, 'status': 'incomplete'})
        wheels = work / 'wheels'; wheels.mkdir()
        for row in spec['wheels']:
            target = wheels / row['filename']
            if wheelhouse:
                supplied = Path(wheelhouse) / row['filename']
                if digest(supplied) != row['sha256']: raise ValueError('Supplied wheel hash differs')
                shutil.copyfile(supplied, target)
            else: download(row['url'], target, row['sha256'])
            with zipfile.ZipFile(target) as wheel:
                if row['scope'] == 'core' and any(p.endswith('.pth') or '.data/scripts/' in p for p in wheel.namelist()):
                    raise ValueError('Unexpected core startup code/scripts')
        tar = work / 'source.tar.gz'
        if archive:
            if digest(archive) != ARCHIVE_HASH: raise ValueError('Supplied archive hash differs')
            shutil.copyfile(archive, tar)
        else: download(URL, tar, ARCHIVE_HASH)
        source = unpack(tar, work / 'source')
        build = work / 'build-env'
        commands = [
            [uv, 'venv', '--python', python, '--no-python-downloads', '--no-project', build],
            [uv, 'pip', 'install', '--python', build / 'bin/python', '--offline', '--no-index', '--find-links', wheels,
             '--no-deps', '--no-build', '--require-hashes', '-r', ASSETS / 'build-requirements.lock'],
            [uv, 'build', source, '--python', build / 'bin/python', '--wheel', '--no-build-isolation', '--offline',
             '--no-index', '--no-sources', '--no-create-gitignore', '--out-dir', work / 'dist'],
        ]
        for i, command in enumerate(commands): checked([*prefix, *command], work, env, logs / f'{i:02d}.json')
        wheel = work / 'dist' / ('graphifyy-' + VERSION + '-py3-none-any.whl')
        if digest(wheel) != WHEEL_HASH: raise ValueError('Reproducible source wheel hash differs; preserved')
        shutil.copyfile(wheel, wheels / wheel.name)
        lock = root / 'requirements.lock'
        lock.write_text((ASSETS / 'core-requirements.lock').read_text() + 'graphifyy==' + VERSION + ' --hash=sha256:' + WHEEL_HASH + '\n')
        checked([*prefix, uv, 'venv', '--python', python, '--no-python-downloads', '--no-project', root / '.venv'], work, env, logs / '03.json')
        checked([*prefix, uv, 'pip', 'install', '--python', root / '.venv/bin/python', '--offline', '--no-index', '--find-links', wheels,
                 '--no-build', '--no-deps', '--require-hashes', '-r', lock], work, env, logs / '04.json')
        shutil.copyfile(tar, root / 'source.tar.gz'); shutil.copyfile(wheel, root / wheel.name)
        for filename in ('LICENSE', 'LICENSE-MIT', 'NOTICE'): shutil.copyfile(ASSETS / filename, root / filename)
        write_json(root / 'READY.json', {'revision': REVISION, 'version': VERSION, 'archive_sha256': ARCHIVE_HASH,
            'wheel_sha256': WHEEL_HASH, 'interpreter_sha256': digest(python), 'runtime_files': inventory(root / '.venv'),
            'dependency_lock_sha256': digest(lock), 'assets': ASSET_HASHES, 'extras': [], 'host_wiring': False})
    return verify(root)


def approved_source(source):
    source = concrete(source)
    if not source.is_dir() or source == Path.home() or len(source.parts) < 4: raise ValueError('Pass one explicit approved project directory')
    if (source / '.obsidian').exists() or source == Path.home() / 'Knowledge': raise ValueError('Vault indexing is outside this code-only route')
    count = total = 0
    for parent, dirs, files in os.walk(source, followlinks=False):
        # Native VCS objects are not a corpus; never inspect their contents.
        dirs[:] = [d for d in dirs if d not in ('.git', '.hg', '.svn')]
        for name in [*dirs, *files]:
            p = Path(parent) / name
            if p.is_symlink(): raise ValueError('Source symlink refused before extraction')
            if SENSITIVE.search(name): raise ValueError('Sensitive-name/vault input refused before reading: ' + name)
            mode = p.stat().st_mode
            if stat.S_ISREG(mode): count += 1; total += p.stat().st_size
            elif not stat.S_ISDIR(mode): raise ValueError('Source special file refused')
            if count > 10000 or total > 128 * 1024 * 1024: raise ValueError('Source exceeds this bounded route (10000 files /128MiB)')
    return source


def run(root, source, out, command='extract', terms=(), timeout=120):
    if not 1 <= timeout <= 900: raise ValueError('Timeout must be 1-900 seconds')
    python = verify(root); source = approved_source(source); out = concrete(out)
    if out.is_relative_to(source) or source.is_relative_to(out): raise ValueError('Keep source and output separate')
    marker = out / 'nstack-graphify.json'
    if out.exists():
        if not marker.is_file(): raise ValueError('Unowned output preserved; choose a fresh directory')
        old = json.loads(marker.read_text())
        if old.get('source') != str(source) or old.get('revision') != REVISION: raise ValueError('Output belongs to another source/pin')
    else:
        if command != 'extract': raise ValueError('Build the code-only graph first')
        out.mkdir(parents=True, mode=0o700)
        write_json(marker, {'source': str(source), 'revision': REVISION, 'derived_private_data': True})
    for p in out.rglob('*'):
        if p.is_symlink(): raise ValueError('Linked output refused')
    log = out / 'runs' / str(time.time_ns()); log.mkdir(parents=True)
    home = log / 'home'; home.mkdir(); (home / 'empty-bin').mkdir(); tmp = log / 'tmp'; tmp.mkdir()
    env = clean_env(home, tmp); profile = profile_for(root, source, out, python); (log / 'sandbox.sb').write_text(profile)
    prefix = sandbox(profile)
    # Probe only an owned synthetic file outside the allowlist, never real personal data.
    with tempfile.TemporaryDirectory(prefix='nstack-graphify-denial-', dir=Path.home() / 'Library/Caches') as denied:
        sentinel = Path(denied) / 'synthetic.txt'; sentinel.write_text('owned probe\n')
        script = ('import errno,json,socket,sys\nr={}\n'
                  'try:\n s=socket.socket();s.connect(("127.0.0.1",9));r["network_denied"]=False\n'
                  'except OSError as e:r["network_errno"]=e.errno;r["network_denied"]=e.errno in (errno.EPERM,errno.EACCES)\n'
                  'try:\n open(sys.argv[1]).read();r["outside_read_denied"]=False\n'
                  'except OSError as e:r["read_errno"]=e.errno;r["outside_read_denied"]=e.errno in (errno.EPERM,errno.EACCES)\n'
                  'print(json.dumps(r))\n')
        probe = checked([*prefix, python, '-I', '-B', '-S', '-c', script, sentinel], out, env, log / 'guard.json', 30)
        guard = json.loads(probe['stdout'])
        if not guard.get('network_denied') or not guard.get('outside_read_denied'): raise ValueError('OS boundary probe failed; upstream not started')
    if command == 'extract': args = ['extract', str(source), '--code-only', '--no-cluster', '--max-workers', '1', '--out', str(out)]
    elif command in ('query', 'explain') and len(terms) == 1: args = [command, terms[0]]
    elif command == 'path' and len(terms) == 2: args = [command, *terms]
    else: raise ValueError('Unsupported bounded command')
    result = checked([*prefix, python, '-I', '-B', '-m', 'graphify', *args], out, env, log / 'command.json', timeout)
    graph = out / 'graphify-out/graph.json'
    if not graph.is_file(): raise ValueError('No graph artifact produced')
    doc = json.loads(graph.read_text()); nodes = doc.get('nodes', []); edges = doc.get('edges', doc.get('links', [])); ids = {n['id'] for n in nodes}
    if not nodes or len(ids) != len(nodes) or any(e.get('source') not in ids or e.get('target') not in ids for e in edges):
        raise ValueError('Empty/duplicate/dangling graph; inspect retained outputs')
    receipt = {'revision': REVISION, 'version': VERSION, 'command': command, 'guard': guard, 'provider_calls': 0,
               'mode': 'code-only/no-cluster', 'source': str(source), 'nodes': len(nodes), 'edges': len(edges),
               'graph_sha256': digest(graph), 'logs': str(log), 'status': 'bounded_command_passed'}
    write_json(log / 'receipt.json', receipt)
    if command != 'extract': print(result['stdout'], end='')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--state', default=str(STATE))
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare'); p.add_argument('--python', required=True); p.add_argument('--uv'); p.add_argument('--wheelhouse'); p.add_argument('--archive')
    sub.add_parser('verify')
    for name in ('extract', 'query', 'path', 'explain'):
        p = sub.add_parser(name); p.add_argument('--source', required=True); p.add_argument('--outdir', required=True); p.add_argument('--timeout', type=int, default=120)
        if name in ('query', 'explain'): p.add_argument('terms', nargs=1)
        elif name == 'path': p.add_argument('terms', nargs=2)
    args = parser.parse_args()
    try:
        root = runtime_root(args.state)
        if args.command == 'prepare': binary = prepare(args.state, args.python, args.uv, args.wheelhouse, args.archive); print(json.dumps({'python': str(binary), 'revision': REVISION}))
        elif args.command == 'verify': print(json.dumps({'python': str(verify(root)), 'revision': REVISION}))
        else: print(json.dumps(run(root, args.source, args.outdir, args.command, getattr(args, 'terms', ()), args.timeout), indent=2))
    except (ValueError, OSError, subprocess.SubprocessError) as exc: parser.exit(2, str(exc) + '\n')


if __name__ == '__main__': main()
