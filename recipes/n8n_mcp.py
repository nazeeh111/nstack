#!/usr/bin/env python3
"""Pinned offline n8n-mcp docs/validation over raw MCP stdio, on demand only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import select
import shutil
import signal
import subprocess
import sys
import time
import uuid

VERSION = '2.101.0'
IMAGE = 'ghcr.io/czlonkowski/n8n-mcp:2.101.0@sha256:0803ecd2a9df1863f805d4ceca84ca69e1337eb775b55eb30aef518a110c8928'
IMAGE_REVISION = '86b993e70008c4987902a235271e11bc03ef3f84'
ASSETS = Path(__file__).resolve().parents[1] / 'integrations/workflows/n8n-mcp'
ASSET_NAMES = ('SOURCE.json', 'LICENSE.n8n-mcp', 'fixture.json', 'miswired.json', 'invalid.json')
STATE = Path(os.environ.get('NSTACK_STATE', Path.home() / 'Library/Application Support/nstack'))
LABEL = 'io.nstack.n8n-mcp-owner'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe(path):
    path = Path(path).absolute()
    if path != path.resolve():
        raise ValueError('Linked runtime path preserved')
    return path


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def prepare(state=STATE):
    state = safe(state)
    root = safe(state / 'native-tools/workflows/n8n-mcp' / VERSION)
    receipt = {'kind': 'nstack-n8n-mcp-docs-v1', 'version': VERSION, 'image': IMAGE,
               'owner': digest(str(state).encode())[:16],
               'assets': {n: digest((ASSETS / n).read_bytes()) for n in ASSET_NAMES}}
    if root.exists():
        if json.loads(safe(root / 'OWNERSHIP.json').read_text()) != receipt:
            raise ValueError('Existing runtime differs; preserved')
    else:
        root.mkdir(parents=True, mode=0o700)
        root.chmod(0o700)
        for n in ASSET_NAMES:
            shutil.copyfile(ASSETS / n, root / n)
        for n in ('docker-config', 'cli-home', 'checks'):
            (root / n).mkdir(mode=0o700)
        write(root / 'OWNERSHIP.json', receipt)
    verify(root)
    return root


def verify(root):
    root = safe(root)
    receipt = json.loads(safe(root / 'OWNERSHIP.json').read_text())
    if receipt.get('kind') != 'nstack-n8n-mcp-docs-v1' or receipt.get('image') != IMAGE:
        raise ValueError('Unowned runtime preserved')
    for n, expected in receipt['assets'].items():
        if Path(n).name != n or digest(safe(root / n).read_bytes()) != expected:
            raise ValueError('Frozen source/fixtures changed; preserved')
    for n in ('docker-config', 'cli-home', 'checks'):
        safe(root / n)
    if any((root / 'docker-config').iterdir()):
        raise ValueError('Private Docker config must remain empty')
    return receipt


def environment(root):
    endpoint = next(('unix://' + str(p) for p in (Path.home() / '.docker/run/docker.sock', Path('/var/run/docker.sock')) if p.is_socket()), None)
    if endpoint is None:
        raise ValueError('Start the existing local Docker engine; no automatic engine/settings change')
    return {'PATH': os.environ.get('PATH', '/usr/local/bin:/usr/bin:/bin'), 'HOME': str(root / 'cli-home'),
            'DOCKER_CONFIG': str(root / 'docker-config'), 'DOCKER_HOST': endpoint, 'LANG': 'en_US.UTF-8'}


def docker(root, args, timeout=90):
    verify(root)
    binary = shutil.which('docker')
    if not binary:
        raise ValueError('Existing Docker CLI required')
    return subprocess.run([binary, *args], env=environment(root), capture_output=True, text=True, timeout=timeout)


def require(proc, action):
    if proc.returncode:
        raise ValueError(action + ' failed; raw Docker logs withheld')
    return proc


def image_info(root):
    fmt = '{"id":{{json .Id}},"architecture":{{json .Architecture}},"repo_digests":{{json .RepoDigests}},"revision":{{json (index .Config.Labels "org.opencontainers.image.revision")}},"version":{{json (index .Config.Labels "org.opencontainers.image.version")}}}'
    info = json.loads(require(docker(root, ['image', 'inspect', '--format', fmt, IMAGE]), 'Image inspection').stdout)
    if not any(d.endswith('@' + IMAGE.split('@')[1]) for d in info['repo_digests']) or info['revision'] != IMAGE_REVISION or info['version'] != VERSION:
        raise ValueError('Image digest/source/version differs')
    return info


def pull(root):
    require(docker(root, ['pull', IMAGE], timeout=600), 'Pinned image pull')
    return image_info(root)


def launch_args(root, name):
    owner = verify(root)['owner']
    return ['run', '--rm', '-i', '--name', name, '--label', LABEL + '=' + owner,
            '--network', 'none', '--memory', '768m', '--cpus', '1', '--pids-limit', '128',
            '--read-only', '--tmpfs', '/tmp:rw,nosuid,noexec,size=64m',
            '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges:true', '--no-healthcheck',
            '--env', 'MCP_MODE=stdio', '--env', 'LOG_LEVEL=error', '--env', 'DISABLE_CONSOLE_OUTPUT=true',
            '--env', 'N8N_MCP_TELEMETRY_DISABLED=true', '--env', 'HOME=/tmp',
            IMAGE]


def cleanup(root, name):
    proc = docker(root, ['inspect', '--format', '{{json .Config.Labels}}', name])
    if proc.returncode:
        return
    if json.loads(proc.stdout).get(LABEL) != verify(root)['owner']:
        raise ValueError('Container ownership differs; preserved')
    require(docker(root, ['rm', '-f', name]), 'Owned MCP container cleanup')


def container_info(root, name):
    fmt = '{"network":{{json .HostConfig.NetworkMode}},"mounts":{{json .Mounts}},"memory":{{json .HostConfig.Memory}},"nano_cpus":{{json .HostConfig.NanoCpus}},"privileged":{{json .HostConfig.Privileged}},"readonly":{{json .HostConfig.ReadonlyRootfs}},"ports":{{json .NetworkSettings.Ports}}}'
    info = json.loads(require(docker(root, ['inspect', '--format', fmt, name]), 'Container readback').stdout)
    if info['network'] != 'none' or info['mounts'] or info['privileged'] or not info['readonly'] or info['memory'] != 768 * 1024 ** 2 or info['nano_cpus'] != 1000000000 or any(info['ports'].values()):
        raise ValueError('Offline docs container boundaries differ')
    return info


class Client:
    """Minimal JSON-RPC transport only; tool contents stay upstream-owned."""
    def __init__(self, root):
        self.root = root
        self.name = 'nstack-n8nmcp-' + verify(root)['owner'] + '-' + uuid.uuid4().hex[:12]
        self.proc = subprocess.Popen([shutil.which('docker'), *launch_args(root, self.name)],
                                     env=environment(root), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, bufsize=0)
        self.buffer = b''
        self.errors = bytearray()
        self.sequence = 0
        self.messages = []
        self.closed_streams = set()

    def request(self, method, params=None, timeout=45):
        self.sequence += 1
        request = {'jsonrpc': '2.0', 'id': self.sequence, 'method': method}
        if params is not None:
            request['params'] = params
        self.send(request)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if b'\n' in self.buffer:
                line, self.buffer = self.buffer.split(b'\n', 1)
                if not line.strip():
                    continue
                response = json.loads(line)
                self.messages.append(response)
                if response.get('id') == self.sequence:
                    return response
                continue
            ready, _, _ = select.select([s for s in (self.proc.stdout, self.proc.stderr) if s not in self.closed_streams], [], [], max(0, deadline - time.monotonic()))
            for stream in ready:
                data = os.read(stream.fileno(), 65536)
                if not data:
                    self.closed_streams.add(stream)
                    if stream is self.proc.stdout:
                        raise ValueError('MCP stdout closed before response')
                    continue
                if stream is self.proc.stdout:
                    self.buffer += data
                    if len(self.buffer) > 12 * 1024 ** 2:
                        raise ValueError('MCP response exceeds bounded transport size')
                else:
                    self.errors.extend(data[:max(0, 65536 - len(self.errors))])
            if self.proc.poll() is not None and not self.buffer:
                raise ValueError('MCP process exited before response')
        raise ValueError('MCP response timed out')

    def send(self, value):
        self.proc.stdin.write((json.dumps(value) + '\n').encode())
        self.proc.stdin.flush()

    def initialize(self):
        response = self.request('initialize', {'protocolVersion': '2024-11-05', 'capabilities': {}, 'clientInfo': {'name': 'nstack-offline-check', 'version': '1'}})
        # Empty tools capability objects are valid; key presence matters.
        if 'error' in response or 'tools' not in response.get('result', {}).get('capabilities', {}):
            raise ValueError('MCP initialization did not advertise tools')
        if response.get('result', {}).get('serverInfo', {}).get('version') != VERSION:
            raise ValueError('MCP server version differs from the selected catalog')
        self.send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
        return response

    def close(self):
        # Upstream container mode may intentionally ignore stdin EOF. Explicit
        # label-checked cleanup closes exactly this transient container.
        cleanup(self.root, self.name)
        try:
            self.proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.communicate()


def tool_document(response):
    if 'error' in response or response.get('result', {}).get('isError'):
        raise ValueError('Upstream MCP tool returned an error')
    content = response.get('result', {}).get('content', [])
    for item in content:
        if item.get('type') == 'text':
            try:
                return json.loads(item['text'])
            except (json.JSONDecodeError, KeyError):
                continue
    structured = response.get('result', {}).get('structuredContent')
    if structured is not None:
        return structured
    raise ValueError('Expected upstream JSON tool content')


def check(root):
    out = root / 'checks' / str(time.time_ns())
    out.mkdir(mode=0o700)
    result = {'status': 'incomplete', 'image': image_info(root), 'scope': 'offline docs/schema/validation only', 'api_credentials_configured': False}
    client = Client(root)
    try:
        response = client.initialize()
        write(out / 'initialize.json', response)
        result['server_info'] = response['result']['serverInfo']
        result['container'] = container_info(root, client.name)
        listed = client.request('tools/list')
        write(out / 'tools-list.json', listed)
        tools = listed.get('result', {}).get('tools', [])
        names = [t['name'] for t in tools]
        if not {'get_node', 'search_nodes', 'validate_node', 'validate_workflow'}.issubset(names) or any(n.startswith('n8n_') for n in names):
            raise ValueError('Docs-only tool inventory differs or API tools unexpectedly exposed')
        result['tools'] = names
        node = client.request('tools/call', {'name': 'get_node', 'arguments': {'nodeType': 'nodes-base.if', 'detail': 'standard'}})
        write(out / 'get-node.json', node)
        doc = tool_document(node)
        if doc.get('nodeType') != 'nodes-base.if' or not doc.get('commonProperties'):
            raise ValueError('Expected real IF-node information')
        result['node_information'] = True
        for fixture in ('fixture', 'miswired', 'invalid'):
            workflow = json.loads((root / (fixture + '.json')).read_text())
            response = client.request('tools/call', {'name': 'validate_workflow', 'arguments': {'workflow': workflow}})
            write(out / (fixture + '-validation.json'), response)
            result[fixture] = tool_document(response)
        if result['fixture'].get('valid') is not True:
            raise ValueError('Runtime-accepted builtin fixture failed structural validation')
        if result['miswired'].get('valid') is not True:
            raise ValueError('Expected valid-but-miswired structural control to pass schema validation')
        if result['invalid'].get('valid') is not False:
            raise ValueError('Invalid-node structural control was accepted')
        result['semantic_limit'] = 'Miswired fixture validates structurally but core CLI output assertion rejects it; validation is not execution proof.'
        result['status'] = 'passed'
    finally:
        client.close()
        write(out / 'check.json', result)
        (out / 'stderr.log').write_bytes(client.errors)
    return {**result, 'evidence': str(out)}


def serve(root):
    image_info(root)
    name = 'nstack-n8nmcp-' + verify(root)['owner'] + '-' + uuid.uuid4().hex[:12]
    proc = subprocess.Popen([shutil.which('docker'), *launch_args(root, name)], env=environment(root),
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
    def interrupted(_signum, _frame):
        raise KeyboardInterrupt()
    previous = signal.signal(signal.SIGTERM, interrupted)
    try:
        # Forward the original bytes. EOF from the host ends this on-demand
        # server even though upstream Docker mode deliberately ignores EOF.
        streams = {sys.stdin.fileno(): proc.stdin.fileno(), proc.stdout.fileno(): sys.stdout.fileno(), proc.stderr.fileno(): sys.stderr.fileno()}
        while proc.poll() is None:
            readable, _, _ = select.select(list(streams), [], [], .25)
            for source in readable:
                data = os.read(source, 65536)
                if not data:
                    if source == sys.stdin.fileno():
                        return 0
                    streams.pop(source)
                    continue
                destination = streams[source]
                view = memoryview(data)
                while view:
                    view = view[os.write(destination, view):]
        return proc.returncode
    finally:
        signal.signal(signal.SIGTERM, previous)
        cleanup(root, name)
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


def main():
    def terminate(_signum, _frame):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, terminate)
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--state', type=Path, default=STATE)
    p.add_argument('command', choices=['prepare', 'pull', 'check', 'serve', 'list-tools', 'call'])
    p.add_argument('--tool')
    group = p.add_mutually_exclusive_group()
    group.add_argument('--arguments')
    group.add_argument('--arguments-file', type=Path)
    a = p.parse_args()
    try:
        root = prepare(a.state)
        if a.command == 'serve':
            return serve(root)
        if a.command == 'prepare':
            result = {'root': str(root), **verify(root)}
        elif a.command in ('pull', 'check'):
            result = globals()[a.command](root)
        else:
            image_info(root)
            client = Client(root)
            try:
                client.initialize()
                if a.command == 'list-tools':
                    result = client.request('tools/list')
                else:
                    if not a.tool or a.tool.startswith('n8n_'):
                        raise ValueError('Select a docs-only tool, not workflow API management')
                    raw = a.arguments_file.read_text() if a.arguments_file else a.arguments or '{}'
                    if len(raw) > 4 * 1024 ** 2:
                        raise ValueError('Tool arguments exceed bounded size')
                    result = client.request('tools/call', {'name': a.tool, 'arguments': json.loads(raw)})
            finally:
                client.close()
        # Raw upstream JSON-RPC response is printed for list-tools/call. No
        # fabricated schema, renamed tools, or rewritten content is introduced.
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, subprocess.TimeoutExpired, KeyboardInterrupt) as e:
        p.exit(2, str(e) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
