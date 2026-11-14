#!/usr/bin/env python3
"""Pinned Craft Anything app package; bounded, offline static-file CLI only."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import plistlib
import shutil
import signal
import subprocess
import sys
import tempfile
import urllib.request
import uuid

VERSION = '0.6.1'
REVISION = '48a9c5a60ff83ff620f98661339be6281a7debc6'
URL = 'https://github.com/storytold/craft-anything/releases/download/v0.6.1/craft-anything-0.6.1-macos-universal.dmg'
DMG_SHA256 = 'bbb777d221a4ffe693323c1b6e625f02e71bfa04d74d32a5d50c4542655ed664'
APP_MANIFEST_SHA256 = '7e1b2c59efc743bff09888ce70479f00d4c517f2cfa274bec56d2eb33f5f156c'
CLI_SHA256 = '53d86f0e541be5b8eb0e5ab67b7a0aa421bfa2f05eea5e207a9721a32039d114'
TEAM = 'DJ6XS33FX8'
STATE = Path(os.environ.get('NSTACK_STATE', Path.home() / 'Library/Application Support/nstack'))
TOOLS = {
    'triage', 'native-functions-list', 'native-sections-list', 'native-strings-browse',
    'native-functions-search', 'native-strings-find', 'native-function-show',
    'native-function-disassemble', 'native-function-pseudocode', 'native-call-graph-show',
    'native-function-callers-list', 'native-function-callees-list', 'apple-macho-show',
    'apple-slices-list', 'formats-wasm-module-show', 'native-library-calls-list',
    'native-offered-symbols-list', 'native-layout-show',
}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def concrete(path):
    path = Path(path).absolute()
    if path.resolve() != path:
        raise ValueError('Linked input/output/runtime path preserved')
    return path


def runtime_root(state=STATE):
    return concrete(concrete(state) / 'native-tools/craft-anything' / VERSION)


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')
    Path(path).chmod(0o600)


def manifest(app):
    rows = {}
    for p in sorted(Path(app).rglob('*')):
        rel = str(p.relative_to(app))
        if p.is_symlink():
            rows[rel] = {'link': os.readlink(p)}
        elif p.is_file():
            rows[rel] = {'sha256': digest(p), 'mode': p.stat().st_mode & 0o777}
        elif not p.is_dir():
            raise ValueError('Unexpected special package file')
    return rows


def manifest_hash(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def capture(argv, cwd=None, env=None, timeout=120):
    process = subprocess.Popen([str(x) for x in argv], cwd=cwd, env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, start_new_session=True)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except BaseException:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()
        raise
    return {'argv': [str(x) for x in argv], 'exit_code': process.returncode,
            'stdout': stdout, 'stderr': stderr}


def checked(argv, **kwargs):
    result = capture(argv, **kwargs)
    if result['exit_code']:
        raise ValueError('Native operation rejected or failed: ' + json.dumps(result))
    return result


def host():
    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        raise ValueError('This accepted route requires Apple Silicon macOS')
    if not Path('/usr/bin/sandbox-exec').is_file():
        raise ValueError('macOS sandbox-exec is required; no unrestricted fallback')


def assess_app(app):
    # Assess the intact notarized application. The standalone CLI ZIP was
    # rejected by Gatekeeper and is deliberately not a fallback distribution.
    code = checked(['/usr/bin/codesign', '--verify', '--deep', '--strict', '--verbose=2', app])
    identity = checked(['/usr/bin/codesign', '-dv', '--verbose=4', app])
    if 'TeamIdentifier=' + TEAM not in identity['stderr'] or 'Notarization Ticket=stapled' not in identity['stderr']:
        raise ValueError('Unexpected application signing identity/notarization; preserved')
    assessment = checked(['/usr/sbin/spctl', '--assess', '--type', 'execute', '--verbose=4', app])
    return {'signature': code, 'identity': identity, 'assessment': assessment}


def verify(state=STATE):
    host()
    root = runtime_root(state)
    app = root / 'Craft Anything.app'
    receipt = root / 'SOURCE.json'
    if receipt.is_symlink() or not receipt.is_file() or app.is_symlink() or not app.is_dir():
        raise ValueError('No owned intact commissioned application')
    saved = json.loads(receipt.read_text())
    if saved.get('revision') != REVISION or saved.get('dmg_sha256') != DMG_SHA256:
        raise ValueError('Runtime source receipt differs; preserved')
    if manifest_hash(manifest(app)) != APP_MANIFEST_SHA256:
        raise ValueError('Runtime package differs from exact official payload; preserved')
    cli = app / 'Contents/MacOS/craft-anything-cli'
    if digest(cli) != CLI_SHA256:
        raise ValueError('Embedded CLI differs; preserved')
    assess_app(app)
    return cli


@contextmanager
def writer(parent):
    parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (parent / '.writer.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def install(state=STATE, dmg=None):
    host()
    root = runtime_root(state)
    with writer(root.parent):
        if root.exists() or root.is_symlink():
            return verify(state)
        with tempfile.TemporaryDirectory(prefix='nstack-craft-install-', dir='/private/tmp') as directory:
            temporary = Path(directory)
            image = concrete(dmg) if dmg else temporary / 'official.dmg'
            if dmg is None:
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                with opener.open(URL, timeout=120) as response, image.open('xb') as stream:
                    shutil.copyfileobj(response, stream)
            if not image.is_file() or digest(image) != DMG_SHA256:
                raise ValueError('Official disk-image SHA256 differs; not mounted or executed')
            image_assessment = checked(['/usr/sbin/spctl', '--assess', '--type', 'open', '--context', 'context:primary-signature', '--verbose=4', image])
            ticket = checked(['/usr/bin/xcrun', 'stapler', 'validate', image])
            mount = temporary / 'mount'
            mount.mkdir()
            attached = False
            stage = None
            try:
                result = checked(['/usr/bin/hdiutil', 'attach', '-readonly', '-nobrowse', '-mountpoint', mount, '-plist', image])
                attached = True
                details = plistlib.loads(result['stdout'].encode())
                if not any(row.get('mount-point') == str(mount) for row in details.get('system-entities', [])):
                    raise ValueError('Disk image did not mount at the owned target')
                app = mount / 'Craft Anything.app'
                if manifest_hash(manifest(app)) != APP_MANIFEST_SHA256:
                    raise ValueError('Official app payload differs from fixed manifest')
                proof = assess_app(app)
                # Preserve the notarization/signing chain and all package notices.
                # No global /Applications, host setup, ownership overwrite or app launch.
                stage = Path(tempfile.mkdtemp(prefix='.prepare-', dir=root.parent))
                checked(['/usr/bin/ditto', '--rsrc', '--extattr', '--acl', app, stage / app.name])
                if manifest_hash(manifest(stage / app.name)) != APP_MANIFEST_SHA256:
                    raise ValueError('Copied application differs; failed stage retained')
                assess_app(stage / app.name)
                write(stage / 'SOURCE.json', {'revision': REVISION, 'version': VERSION,
                    'distribution_url': URL, 'dmg_sha256': DMG_SHA256,
                    'package_manifest_sha256': APP_MANIFEST_SHA256, 'embedded_cli_sha256': CLI_SHA256,
                    'artifact_identity': 'Official signed release package; not a reproducible source build attestation',
                    'image_assessment': image_assessment, 'stapled_ticket': ticket, 'app_assessment': proof,
                    'readiness': 'Native package accepted; static fixture check remains separate'})
                os.rename(stage, root)
                stage = None
            finally:
                if attached:
                    checked(['/usr/bin/hdiutil', 'detach', mount])
                # A failed same-volume stage is retained for diagnosis, never
                # discarded as if it were a successful installed runtime.
    return verify(state)


def environment(run):
    run = Path(run)
    return {'HOME': str(run / 'home'), 'PATH': str(run / 'empty-bin'),
            'CRAFT_ANYTHING_CONFIG_DIR': str(run / 'config'),
            'XDG_CONFIG_HOME': str(run / 'config'), 'XDG_CACHE_HOME': str(run / 'cache'),
            'TMPDIR': str(run / 'tmp'), 'LANG': 'en_US.UTF-8', 'TZ': 'UTC'}


def guard_python():
    # Framework bin/python can be a launcher which spawns this real interpreter.
    # Use the interpreter directly so the execution allowlist stays exact.
    native = Path(sys.base_prefix) / 'Resources/Python.app/Contents/MacOS/Python'
    return native.resolve() if native.is_file() else Path(sys.executable).resolve()


def profile(cli, source, out):
    python = guard_python()
    readable = [cli.parent.parent.parent, Path(source), Path(out), Path(sys.base_prefix)]
    excluded = ' '.join('(require-not (subpath ' + json.dumps(str(p)) + '))' for p in readable)
    return ('(version 1)\n(allow default)\n(deny network*)\n'
            # The same bounded personal-content policy used by Graphify. Native
            # loaders retain OS access; this is not an all-filesystem sandbox.
            '(deny file-read-data file-read-xattr (require-all (subpath "/Users") ' + excluded + '))\n'
            '(deny file-write* (require-not (subpath ' + json.dumps(str(out)) + ')))\n'
            '(deny process-exec (require-all (require-not (literal ' + json.dumps(str(cli)) + '))'
            ' (require-not (literal ' + json.dumps(str(python)) + '))))\n')


def approved_file(source):
    source = concrete(source)
    forbidden = {'.ssh', '.codex', '.claude', '.config', '.aws', '.gnupg', '.docker',
                 'keychains', 'credentials', 'secrets', 'passwords', '.obsidian'}
    if forbidden.intersection(part.casefold() for part in source.parts):
        raise ValueError('Credential/configuration/vault input is outside this static route')
    if not source.is_file() or source.stat().st_size > 128 * 1024 * 1024:
        raise ValueError('Select one regular input file at most 128 MiB')
    return source


def execute(state, source, out, tool='triage', params=None):
    if tool not in TOOLS:
        raise ValueError('Tool is outside the admitted static-file route')
    if params is None:
        params = {}
    if not isinstance(params, dict) or any(k in params for k in ('path', 'project', 'allow_run', 'deep', 'clean_room')):
        raise ValueError('Pass tool options only; input/project/mode are owned by the wrapper')
    if tool == 'triage' and params:
        raise ValueError('Triage has no additional tool options')
    cli = verify(state)
    source = approved_file(source)
    out = concrete(out)
    if out == source or out.is_relative_to(runtime_root(state)) or source.is_relative_to(out):
        raise ValueError('Select separate task input/output outside the sealed runtime')
    identity = {'revision': REVISION, 'source': str(source), 'sha256': digest(source)}
    if out.exists():
        receipt = out / 'OWNERSHIP.json'
        if receipt.is_symlink() or not receipt.is_file() or json.loads(receipt.read_text()) != identity:
            raise ValueError('Unowned, changed or different-input output preserved')
    else:
        out.mkdir(parents=True, mode=0o700)
        write(out / 'OWNERSHIP.json', identity)
    with writer(out):
        run = out / 'runs' / uuid.uuid4().hex
        run.mkdir(parents=True, mode=0o700)
        for name in ('home', 'config', 'cache', 'tmp', 'empty-bin'):
            (run / name).mkdir(mode=0o700)
        env = environment(run)
        rules = profile(cli, source, out)
        (run / 'sandbox.sb').write_text(rules)
        # Test only a synthetic owned file outside the readable paths. Never
        # inspect an actual credential/personal file to check containment.
        with tempfile.TemporaryDirectory(prefix='nstack-craft-guard-', dir=runtime_root(state).parent) as guarddir:
            sentinel = Path(guarddir) / 'synthetic.txt'
            sentinel.write_text('synthetic guard only')
            probe = ('import errno,json,socket,sys\n'
                     'checks={}\n'
                     'try:\n open(sys.argv[1]).read()\n checks["read_denied"]=False\n'
                     'except OSError as e:\n checks["read_denied"]=e.errno in (errno.EPERM,errno.EACCES)\n'
                     'try:\n socket.create_connection(("127.0.0.1",9),timeout=1)\n checks["network_denied"]=False\n'
                     'except OSError as e:\n checks["network_denied"]=e.errno in (errno.EPERM,errno.EACCES)\n'
                     'print(json.dumps(checks))\n'
                     'sys.exit(0 if all(checks.values()) else 1)')
            guard = capture(['/usr/bin/sandbox-exec', '-p', rules, guard_python(), '-I', '-B', '-S', '-c', probe, sentinel], cwd=run, env=env, timeout=30)
            write(run / 'guard.json', guard)
            if guard['exit_code']:
                raise ValueError('Static OS containment probe failed; target not opened: ' + str(run))
        argv = ['/usr/bin/sandbox-exec', '-p', rules, cli, '--deep', '--project', out / 'investigation.cany', tool, source]
        if tool != 'triage':
            argv += ['--json', json.dumps(params)]
        result = capture(argv, cwd=run, env=env, timeout=120)
        write(run / 'execution.json', result)
        if digest(source) != identity['sha256']:
            raise ValueError('Input changed during static analysis; result is stale')
        if result['exit_code']:
            raise ValueError('Static command failed; inspect ' + str(run))
        parsed = json.loads(result['stdout'])
        if not isinstance(parsed, dict) or 'error' in parsed:
            raise ValueError('Missing successful structured static result; inspect ' + str(run))
        write(run / 'result.json', parsed)
        receipt = {'revision': REVISION, 'tool': tool, 'input': identity,
                   'output': str(run / 'result.json'), 'network': 'OS denied',
                   'target_execution': False, 'provider_calls': 0,
                   'limits': 'Static evidence only; no runtime/rebuild or all-format acceptance'}
        write(run / 'receipt.json', receipt)
        return receipt


def assert_fixture(documents, negative, expected_hash):
    if len(documents) != 3 or any(not isinstance(d, dict) for d in [*documents, negative]):
        raise ValueError('Missing structured fixture evidence')
    records = [*documents, negative]
    ids = [d.get('id') for d in records]
    if any(not isinstance(i, str) or not i.startswith('ev_') for i in ids) or len(set(ids)) != 4:
        raise ValueError('Fixture evidence IDs missing or repeated')
    if any(d.get('subject', {}).get('sha256') != expected_hash for d in records):
        raise ValueError('Fixture evidence refers to different bytes')
    if documents[0].get('result', {}).get('format') != 'mach-o' or documents[0]['result'].get('architecture') != 'arm64':
        raise ValueError('Fixture format/architecture was not observed')
    functions = documents[1].get('result', {}).get('functions', [])
    strings = documents[2].get('result', {}).get('matches', [])
    if not any(f.get('name') == '_craft_answer' for f in functions):
        raise ValueError('Known fixture function absent from parsed results')
    if not any(m.get('text') == 'NSTACK_CRAFT_SENTINEL' for m in strings):
        raise ValueError('Known fixture string absent from parsed results')
    if negative.get('result', {}).get('matches') != [] or negative['result'].get('total') != 0:
        raise ValueError('Absent-string control did not return zero matches')


def check(state=STATE):
    # A tiny owned Mach-O with an independently known export and string. It is
    # compiled with the existing Apple compiler and never executed.
    cli = verify(state)
    compiler = shutil.which('cc')
    if not compiler:
        raise ValueError('Existing Apple C compiler required for the synthetic check')
    root = runtime_root(state)
    run = root.parent / ('check-' + uuid.uuid4().hex)
    run.mkdir(mode=0o700)
    source = run / 'fixture.c'
    source.write_text('#include <stdio.h>\nint craft_answer(void){return 42;}\nint main(void){puts("NSTACK_CRAFT_SENTINEL");return craft_answer();}\n')
    target = run / 'fixture'
    checked([compiler, '-O0', '-g', '-o', target, source], cwd=run)
    original = digest(target)
    metadata = run / 'metadata'
    metadata.mkdir()
    for name in ('home', 'config', 'cache', 'tmp', 'empty-bin'):
        (metadata / name).mkdir(mode=0o700)
    env = environment(metadata)
    rules = profile(cli, target, run)
    version = checked(['/usr/bin/sandbox-exec', '-p', rules, cli, '--version'], cwd=metadata, env=env, timeout=30)
    if version['stdout'].strip() != 'craft-anything-cli ' + VERSION:
        raise ValueError('Embedded CLI version differs from selected release')
    help_result = checked(['/usr/bin/sandbox-exec', '-p', rules, cli, '--help'], cwd=metadata, env=env, timeout=30)
    write(metadata / 'version.json', version)
    write(metadata / 'help.json', help_result)
    results = [execute(state, target, run / 'evidence', 'triage'),
               execute(state, target, run / 'evidence', 'native-functions-list', {'limit': 50}),
               execute(state, target, run / 'evidence', 'native-strings-find', {'pattern': 'NSTACK_CRAFT_SENTINEL'})]
    documents = [json.loads(Path(r['output']).read_text()) for r in results]
    if digest(target) != original:
        raise ValueError('Synthetic target changed')
    # A non-matching search must not manufacture the known marker.
    negative = execute(state, target, run / 'evidence', 'native-strings-find', {'pattern': 'NSTACK_ABSENT_SENTINEL'})
    assert_fixture(documents, json.loads(Path(negative['output']).read_text()), original)
    result = {'passed': True, 'fixture': str(run), 'checks': results, 'negative': negative,
              'input_unchanged': True, 'target_executed': False, 'provider_calls': 0,
              'qualification': 'Tiny Mach-O triage/function/string fixture only'}
    write(run / 'CHECK.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', default=str(STATE))
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('install'); p.add_argument('--dmg')
    sub.add_parser('verify'); sub.add_parser('check')
    p = sub.add_parser('inspect'); p.add_argument('--source', required=True); p.add_argument('--outdir', required=True)
    p.add_argument('--tool', choices=sorted(TOOLS), default='triage'); p.add_argument('--params', default='{}')
    args = parser.parse_args()
    try:
        if args.command == 'install':
            result = {'cli': str(install(args.state, args.dmg)), 'readiness': 'Package verified; run check'}
        elif args.command == 'verify':
            result = {'cli': str(verify(args.state)), 'revision': REVISION}
        elif args.command == 'check':
            result = check(args.state)
        else:
            result = execute(args.state, args.source, args.outdir, args.tool, json.loads(args.params))
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
