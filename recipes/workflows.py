#!/usr/bin/env python3
"""On-demand, pinned local n8n. No owner creation, provider keys or host mounts."""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import socket
import subprocess
import tempfile
import time
import urllib.request

VERSION = '2.47.4'
IMAGE = 'docker.io/n8nio/n8n:2.47.4@sha256:56a3f0d56c2888b53ca7d89de4aa3de702888f33667c96a1f1d7118548f979e9'
ASSETS = Path(__file__).resolve().parents[1] / 'integrations/workflows/n8n'
ASSET_NAMES = ('compose.json', 'fixture.json', 'miswired.json', 'invalid.json', 'SOURCE.json', 'LICENSE.n8n.md')
STATE = Path(os.environ.get('NSTACK_STATE', Path.home() / 'Library/Application Support/nstack'))
LABEL = 'io.nstack.workflow-owner'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def redact(text):
    # n8n includes an internal resumeToken in even a synthetic CLI result.
    # Keep it only in the native runtime/database, never evidence or output.
    return re.sub(r'("[^"\n]*(?:token|secret|password|api.?key|encryption.?key)[^"\n]*"\s*:\s*)"(?:[^"\\]|\\.)*"',
                  r'\1"[redacted]"', text, flags=re.I)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def safe_path(path):
    path = Path(path).absolute()
    if path.resolve() != path:
        raise ValueError('Linked runtime path preserved; choose an unlinked private state directory')
    return path


def coordinates(state):
    state = safe_path(state)
    owner = sha(str(state).encode())[:16]
    return state / 'native-tools/workflows/n8n' / VERSION, 'nstack-n8n-' + owner, owner


def prepare(state=STATE, port=5678):
    if not 1024 <= port <= 65535:
        raise ValueError('Choose a nonprivileged localhost port')
    root, project, owner = coordinates(state)
    safe_path(root)
    expected = {name: sha((ASSETS / name).read_bytes()) for name in ASSET_NAMES}
    model = json.loads((ASSETS / 'compose.json').read_text())
    model['services']['n8n']['ports'][0]['published'] = str(port)
    model['services']['n8n']['labels'][LABEL] = owner
    model['volumes']['data']['labels'][LABEL] = owner
    model['networks']['default']['labels'][LABEL] = owner
    for key in ('N8N_EDITOR_BASE_URL', 'WEBHOOK_URL'):
        model['services']['n8n']['environment'][key] = f'http://localhost:{port}/'
    receipt = {'kind': 'nstack-n8n-owned-runtime-v1', 'version': VERSION, 'image': IMAGE,
               'project': project, 'owner': owner, 'port': port, 'assets': expected,
               'compose_sha256': sha((json.dumps(model, indent=2) + '\n').encode())}
    if root.exists():
        safe_path(root / 'OWNERSHIP.json')
        if not (root / 'OWNERSHIP.json').is_file() or json.loads((root / 'OWNERSHIP.json').read_text()) != receipt:
            raise ValueError('Existing runtime coordinates or assets differ; preserved')
        verify(root)
        return root
    root.mkdir(parents=True, mode=0o700)
    root.chmod(0o700)
    for name in ASSET_NAMES:
        shutil.copyfile(ASSETS / name, root / name)
    write_json(root / 'compose.json', model)
    for name in ('docker-config', 'cli-home', 'checks'):
        (root / name).mkdir(mode=0o700)
    write_json(root / 'OWNERSHIP.json', receipt)
    verify(root)
    return root


def verify(root):
    root = safe_path(root)
    safe_path(root / 'OWNERSHIP.json')
    r = json.loads((root / 'OWNERSHIP.json').read_text())
    if r.get('kind') != 'nstack-n8n-owned-runtime-v1' or r.get('image') != IMAGE:
        raise ValueError('Unowned runtime preserved')
    if sha(safe_path(root / 'compose.json').read_bytes()) != r['compose_sha256']:
        raise ValueError('Runtime Compose changed; preserved')
    for name, digest in r['assets'].items():
        if name != 'compose.json' and (Path(name).name != name or sha(safe_path(root / name).read_bytes()) != digest):
            raise ValueError('Runtime support changed; preserved')
    for name in ('docker-config', 'cli-home', 'checks'):
        safe_path(root / name)
    # A private empty Docker config avoids host credentials and mutable contexts.
    if any((root / 'docker-config').iterdir()):
        raise ValueError('Docker CLI configuration is no longer empty; preserved')
    return r


@contextlib.contextmanager
def locked(root):
    with (safe_path(root) / '.writer.lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


@contextlib.contextmanager
def check_cancellation():
    """Let a cancelled CLI check run its owned-resource finally block."""
    previous = signal.getsignal(signal.SIGTERM)
    def cancelled(_signum, _frame):
        raise KeyboardInterrupt('Workflow check interrupted')
    signal.signal(signal.SIGTERM, cancelled)
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, previous)


def docker_env(root, endpoint=None):
    candidates = [Path.home() / '.docker/run/docker.sock', Path('/var/run/docker.sock')]
    if endpoint is None:
        endpoint = next(('unix://' + str(p) for p in candidates if p.is_socket()), None)
    if not endpoint or not endpoint.startswith('unix:///'):
        raise ValueError('A running local Unix Docker socket is required; no automatic daemon/settings changes')
    if not Path(endpoint[7:]).is_socket():
        raise ValueError('Selected local Docker socket is unavailable')
    return {'PATH': os.environ.get('PATH', '/usr/local/bin:/usr/bin:/bin'),
            'HOME': str(root / 'cli-home'), 'DOCKER_CONFIG': str(root / 'docker-config'),
            'DOCKER_HOST': endpoint, 'LANG': 'en_US.UTF-8', 'COMPOSE_ANSI': 'never'}


def docker(root, args, timeout=120, endpoint=None, input=None):
    verify(root)
    binary = shutil.which('docker')
    if not binary:
        raise ValueError('Existing Docker CLI is required; no automatic installer')
    return subprocess.run([binary, *map(str, args)], env=docker_env(root, endpoint),
                          input=input, capture_output=True, text=True, timeout=timeout)


def compose(root, args, timeout=120, endpoint=None):
    r = verify(root)
    return docker(root, ['compose', '-p', r['project'], '-f', root / 'compose.json', *args], timeout, endpoint)


def require(result, operation):
    if result.returncode:
        # Docker/CLI logs can contain internal auth material. Keep them off transcripts.
        raise ValueError(operation + ' failed; no secret-bearing logs printed')
    return result


def owned(root, endpoint=None):
    """Check labels before touching existing project resources; never inspect env."""
    r = verify(root)
    ids = require(docker(root, ['ps', '-aq', '--filter', 'label=com.docker.compose.project=' + r['project']], endpoint=endpoint), 'Project inventory').stdout.split()
    for ident in ids:
        labels = json.loads(require(docker(root, ['inspect', '--format', '{{json .Config.Labels}}', ident], endpoint=endpoint), 'Ownership readback').stdout)
        if labels.get(LABEL) != r['owner']:
            raise ValueError('A project container has different ownership; preserved')
    for kind, name in [('volume', r['project'] + '_data'), ('network', r['project'] + '_default')]:
        inspect = docker(root, [kind, 'inspect', '--format', '{{json .Labels}}', name], endpoint=endpoint)
        if inspect.returncode == 0 and json.loads(inspect.stdout).get(LABEL) != r['owner']:
            raise ValueError('A project resource has different ownership; preserved')
    return ids


def pull(root, endpoint=None):
    owned(root, endpoint)
    require(docker(root, ['pull', IMAGE], timeout=900, endpoint=endpoint), 'Pinned image pull')
    return {'image': IMAGE, 'pulled': True, 'observed': image_info(root, endpoint)}


def image_info(root, endpoint=None):
    fmt = '{"id":{{json .Id}},"architecture":{{json .Architecture}},"repo_digests":{{json .RepoDigests}}}'
    info = json.loads(require(docker(root, ['image', 'inspect', '--format', fmt, IMAGE], endpoint=endpoint), 'Pinned image readback').stdout)
    if not any(x.endswith('@' + IMAGE.split('@')[1]) for x in info['repo_digests']):
        raise ValueError('Observed image digest differs')
    return info


def status(root, endpoint=None):
    ids = owned(root, endpoint)
    rows = []
    for ident in ids:
        fmt = '{"id":{{json .Id}},"running":{{json .State.Running}},"status":{{json .State.Status}},"ports":{{json .NetworkSettings.Ports}},"restart":{{json .HostConfig.RestartPolicy.Name}},"mounts":{{json .Mounts}},"image_id":{{json .Image}},"memory_limit":{{json .HostConfig.Memory}},"nano_cpus":{{json .HostConfig.NanoCpus}},"privileged":{{json .HostConfig.Privileged}},"cap_drop":{{json .HostConfig.CapDrop}},"security_options":{{json .HostConfig.SecurityOpt}}}'
        row = json.loads(require(docker(root, ['inspect', '--format', fmt, ident], endpoint=endpoint), 'Status readback').stdout)
        # Mount.Source for named Docker volumes is engine-local, not user content.
        rows.append(row)
    return {'project': verify(root)['project'], 'containers': rows, 'owner_setup': 'User action pending; no API/MCP connection configured'}


def start(root, endpoint=None):
    ids = owned(root, endpoint)
    r = verify(root)
    if not any(x['running'] for x in status(root, endpoint)['containers']):
        with socket.socket() as s:
            try:
                s.bind(('127.0.0.1', r['port']))
            except OSError as e:
                raise ValueError('Local port occupied; existing listener preserved') from e
    try:
        require(compose(root, ['up', '-d', '--pull', 'never'], endpoint=endpoint), 'Project startup')
        result = status(root, endpoint)
        for row in result['containers']:
            if row['restart'] != 'no' or any(m['Type'] == 'bind' for m in row['mounts']):
                raise ValueError('Unexpected restart policy or host mount')
            if row['memory_limit'] != 2 * 1024 ** 3 or row['nano_cpus'] != 2000000000 or row['privileged'] or 'ALL' not in row['cap_drop'] or 'no-new-privileges:true' not in row['security_options']:
                raise ValueError('Runtime resource or privilege settings differ')
            for mappings in row['ports'].values():
                if mappings and any(x['HostIp'] != '127.0.0.1' for x in mappings):
                    raise ValueError('Unexpected public port binding')
            if row['ports'].get('5678/tcp') != [{'HostIp': '127.0.0.1', 'HostPort': str(r['port'])}]:
                raise ValueError('Expected localhost UI port was not published')
        return result
    except BaseException as error:
        # up can partially start a service before failing. Stop verifies every
        # project label and never deletes the persistent named data volume.
        try:
            stop(root, endpoint)
        except BaseException:
            if hasattr(error, 'add_note'):
                error.add_note('Owned project cleanup also failed; inspect its status before retrying.')
        raise


def stop(root, endpoint=None):
    owned(root, endpoint)
    require(compose(root, ['stop'], endpoint=endpoint), 'Project stop')
    # Timed-out `compose run` clients can leave their one-off engine containers.
    # Stop only label-verified containers from this exact project, too.
    for row in status(root, endpoint)['containers']:
        if row['running']:
            require(docker(root, ['stop', '--time', '10', row['id']], endpoint=endpoint), 'Owned one-off stop')
    return status(root, endpoint)


def cli(root, args, endpoint=None):
    # Call only while the server is stopped, preventing SQLite/task-broker races.
    if any(x['running'] for x in status(root, endpoint)['containers']):
        raise ValueError('Stop the owned UI before CLI execution')
    return compose(root, ['run', '--rm', '--no-deps', '-T', '--pull', 'never', 'n8n', *args], timeout=180, endpoint=endpoint)


def execution_document(text):
    # n8n startup messages may precede the --rawOutput JSON. Accept a whole
    # execution record, not arbitrary later JSON fragments or success messages.
    decoder = json.JSONDecoder()
    for match in re.finditer(r'(?m)^\{', text):
        try:
            value, _ = decoder.raw_decode(text[match.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and isinstance(value.get('data', {}).get('resultData'), dict):
            return value
    raise ValueError('No execution result record returned')


def assert_execution(text):
    data = execution_document(text)
    result = data['data']['resultData']
    if result.get('error') or data.get('status') != 'success':
        raise ValueError('Workflow failed despite CLI exit status')
    runs = result.get('runData', {})
    if 'Rejected' in runs:
        raise ValueError('Wrong valid branch executed')
    try:
        output = runs['Result'][0]['data']['main'][0]
    except (KeyError, IndexError, TypeError) as e:
        raise ValueError('Expected result node did not execute') from e
    if [x['json'] for x in output] != [{'accepted': True, 'total': 42}]:
        raise ValueError('Workflow output differs from independent known result')
    return {'accepted': True, 'total': 42}


def check(root, endpoint=None):
    r = verify(root)
    owned(root, endpoint)
    out = root / 'checks' / str(time.time_ns())
    out.mkdir(mode=0o700)
    result = {'status': 'incomplete', 'version': VERSION, 'image': IMAGE, 'project': r['project'],
              'external_effects': False, 'owner_or_api_created': False, 'code_nodes': False}
    result['observed_image'] = image_info(root, endpoint)
    fixture_ids = {}
    # Fresh IDs avoid overwriting even edited old fixture workflows on a rerun.
    for name in ('fixture', 'miswired', 'invalid'):
        fixture = json.loads((root / (name + '.json')).read_text())
        fixture['id'] += out.name
        fixture_ids[name] = fixture['id']
        write_json(out / (name + '.json'), fixture)
    def run(args, name):
        proc = cli(root, args, endpoint)
        # Only synthetic fixture runs: no app log, config, auth or credential dump.
        (out / (name + '.stdout.log')).write_text(redact(proc.stdout))
        (out / (name + '.stderr.log')).write_text(redact(proc.stderr))
        return proc
    try:
        stop(root, endpoint)
        require(compose(root, ['config', '--quiet'], endpoint=endpoint), 'Compose validation')
        seed(root, endpoint, fixtures=out)
        for fixture in ('fixture', 'miswired', 'invalid'):
            proc = run(['import:workflow', '--input=/home/node/.n8n/nstack-' + fixture + '.json'], fixture + '-import')
            # Fixtures are supplied via named-volume copy, never a host mount.
            require(proc, 'Fixture import')
        good = run(['execute', '--id=' + fixture_ids['fixture'], '--rawOutput'], 'good')
        require(good, 'Fixture execution')
        result['output'] = assert_execution(good.stdout)
        miswired = run(['execute', '--id=' + fixture_ids['miswired'], '--rawOutput'], 'miswired')
        try:
            assert_execution(miswired.stdout)
        except ValueError:
            result['valid_but_miswired_rejected'] = True
        else:
            raise ValueError('Structurally valid wrong branch passed')
        invalid = run(['execute', '--id=' + fixture_ids['invalid'], '--rawOutput'], 'invalid')
        try:
            doc = execution_document(invalid.stdout)
            rejected = bool(doc['data']['resultData'].get('error')) or doc.get('status') != 'success'
        except ValueError:
            rejected = 'Execution was NOT successful' in invalid.stdout or 'Error executing workflow' in invalid.stderr or invalid.returncode != 0
        if not rejected:
            raise ValueError('Invalid workflow was accepted')
        result['invalid_workflow_rejected'] = True
        exported = run(['export:workflow', '--id=' + fixture_ids['fixture']], 'export')
        require(exported, 'Fixture export')
        # Current server export logs the workflow JSON to stdout without --output.
        wf = extract_workflow(exported.stdout, fixture_ids['fixture'])
        expected = json.loads((root / 'fixture.json').read_text())
        if wf['connections'] != expected['connections'] or wf.get('active'):
            raise ValueError('Persisted connections or activation differs')
        result['persisted_connections_checked'] = True
        started = start(root, endpoint)
        deadline = time.monotonic() + 75
        while True:
            try:
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                with opener.open(f'http://127.0.0.1:{r["port"]}/healthz', timeout=2) as response:
                    if response.status == 200:
                        break
            except OSError:
                pass
            if time.monotonic() > deadline:
                raise ValueError('Local health endpoint did not become ready')
            time.sleep(.5)
        result['localhost_health'] = True
        stop(root, endpoint)
        replay = run(['execute', '--id=' + fixture_ids['fixture'], '--rawOutput'], 'after-restart')
        require(replay, 'Persisted fixture execution')
        assert_execution(replay.stdout)
        result['restart_persistence'] = True
        result['status'] = 'passed'
        result['containers_after_stop'] = status(root, endpoint)['containers']
    finally:
        stop(root, endpoint)
        write_json(out / 'check.json', result)
    return result, out


def extract_workflow(text, fixture_id='NstackFixture01'):
    decoder = json.JSONDecoder()
    for match in re.finditer(r'(?m)^[\[{]', text):
        try:
            value, _ = decoder.raw_decode(text[match.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(value, list) and len(value) == 1:
            value = value[0]
        if isinstance(value, dict) and value.get('id') == fixture_id and 'connections' in value:
            return value
    raise ValueError('No exported fixture returned')


def seed(root, endpoint=None, fixtures=None):
    """Create the stopped owned container, then copy synthetic files only."""
    owned(root, endpoint)
    require(compose(root, ['create', '--pull', 'never'], endpoint=endpoint), 'Owned container creation')
    ids = owned(root, endpoint)
    if len(ids) != 1:
        raise ValueError('Expected exactly one owned core container')
    # Only synthetic files enter the owned named volume; none are copied out.
    for name in ('fixture', 'miswired', 'invalid'):
        require(docker(root, ['cp', (fixtures or root) / (name + '.json'), ids[0] + ':/home/node/.n8n/nstack-' + name + '.json'], endpoint=endpoint), 'Synthetic fixture copy')


def trigger_prepare(state=STATE):
    """Fetch exact upstream source only. Deliberately has no start/deploy path."""
    manifest = json.loads((ASSETS.parent / 'trigger/SOURCE.json').read_text())
    parent = safe_path(state) / 'native-tools/workflows/trigger'
    root = safe_path(parent / manifest['version'])
    def verify_source(folder):
        receipt = json.loads(safe_path(folder / 'SOURCE.json').read_text())
        if receipt != manifest:
            raise ValueError('Existing Trigger source manifest differs; preserved')
        for row in manifest['files']:
            path = Path(row['path'])
            if path.is_absolute() or '..' in path.parts:
                raise ValueError('Unsafe pinned source path')
            data = safe_path(folder / path).read_bytes()
            blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            if blob != row['git_blob']:
                raise ValueError('Trigger source Git blob differs; preserved')
    if root.exists():
        verify_source(root)
    else:
        parent.mkdir(parents=True, exist_ok=True)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with tempfile.TemporaryDirectory(prefix='.prepare-', dir=parent) as tmp:
            stage = Path(tmp) / 'source'
            stage.mkdir()
            for row in manifest['files']:
                path = Path(row['path'])
                if path.is_absolute() or '..' in path.parts or not row['url'].startswith('https://raw.githubusercontent.com/' + manifest['repository'] + '/' + manifest['revision'] + '/'):
                    raise ValueError('Unsafe pinned source locator')
                target = stage / path
                target.parent.mkdir(parents=True, exist_ok=True)
                with opener.open(row['url'], timeout=45) as response:
                    data = response.read(row['bytes'] + 1)
                if len(data) != row['bytes']:
                    raise ValueError('Trigger source length differs')
                target.write_bytes(data)
                target.chmod(0o755 if row['mode'] == '100755' else 0o644)
            write_json(stage / 'SOURCE.json', manifest)
            verify_source(stage)
            if root.exists():
                raise ValueError('Concurrent Trigger preparation preserved')
            os.rename(stage, root)
    return {'source': str(root), 'version': manifest['version'], 'revision': manifest['revision'],
            'files_verified': len(manifest['files']), 'state': 'source ready; full runtime not started',
            'gates': [manifest['resource_gate'], manifest['isolation_gate']],
            'credentials_generated': False, 'containers_started': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state', type=Path, default=STATE)
    p.add_argument('--docker-host', help='Existing local unix:/// socket only')
    p.add_argument('--port', type=int, default=5678)
    p.add_argument('command', choices=['prepare', 'pull', 'check', 'start', 'stop', 'status', 'trigger-prepare'])
    a = p.parse_args()
    try:
        if a.command == 'trigger-prepare':
            print(json.dumps(trigger_prepare(a.state), indent=2))
            return
        root = prepare(a.state, a.port)
        with locked(root):
            if a.command == 'prepare':
                result = {'root': str(root), **verify(root)}
            elif a.command == 'pull':
                result = pull(root, a.docker_host)
            elif a.command == 'check':
                with check_cancellation():
                    result, out = check(root, a.docker_host)
                result = {**result, 'evidence': str(out)}
            else:
                result = globals()[a.command](root, a.docker_host)
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, subprocess.TimeoutExpired) as e:
        p.exit(2, '\n'.join([str(e), *getattr(e, '__notes__', [])]) + '\n')
    except KeyboardInterrupt as e:
        p.exit(130, '\n'.join([str(e) or 'Workflow operation interrupted.', *getattr(e, '__notes__', [])]) + '\n')


if __name__ == '__main__':
    main()
