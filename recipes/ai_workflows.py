#!/usr/bin/env python3
"""Locked, offline application runtime for explicitly commissioned AI workflow projects."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
import time
import uuid
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'integrations/ai-workflows'
STATE = Path(os.environ.get('NSTACK_STATE', Path.home() / 'Library/Application Support/nstack'))
BASE = 'docker.io/library/python@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b'
OWNER = 'ai-workflows'
INPUTS = ('Dockerfile', 'requirements.lock', 'smoke.py', 'SOURCE.json')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.tmp-' + uuid.uuid4().hex)
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    temporary.chmod(0o600)
    os.replace(temporary, path)


def identity():
    rows = {name: digest(TEMPLATE / name) for name in INPUTS}
    source = json.loads((TEMPLATE / 'SOURCE.json').read_text())
    if source['lock_sha256'] != rows['requirements.lock']:
        raise ValueError('Published dependency lock differs from source provenance')
    fingerprint = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    return fingerprint, rows


def safe_directory(path):
    path = Path(path).absolute()
    if path.resolve() != path:
        raise ValueError('Linked runtime path preserved')
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not path.is_dir() or path.is_symlink():
        raise ValueError('Expected owned directory')
    return path


class Runtime:
    def __init__(self, state=STATE, docker_host=None):
        self.state = Path(state).absolute()
        self.parent = safe_directory(self.state / 'native-tools/ai-workflows')
        self.fingerprint, self.inputs = identity()
        self.root = self.parent / self.fingerprint
        self.docker = shutil.which('docker')
        if not self.docker:
            raise ValueError('Existing Docker CLI required; no automatic daemon installation')
        if docker_host is None:
            candidates = [Path.home() / '.docker/run/docker.sock', Path('/var/run/docker.sock')]
            available = [p for p in candidates if p.exists() and stat.S_ISSOCK(p.stat().st_mode)]
            if not available:
                raise ValueError('No existing local Docker socket; select --docker-host unix:///absolute/socket')
            docker_host = 'unix://' + str(available[0])
        if not re.fullmatch(r'unix:///[^\n\r]+', docker_host):
            raise ValueError('Only an existing local unix Docker endpoint is supported')
        endpoint = Path(docker_host[7:])
        if not endpoint.exists() or not stat.S_ISSOCK(endpoint.stat().st_mode):
            raise ValueError('Docker endpoint is not an existing local socket')
        home = safe_directory(self.parent / 'client-home')
        # Docker buildx writes its own metadata. A fresh empty directory per
        # invocation avoids reading either host credentials or old client state.
        config = safe_directory(self.parent / 'client-configs' / uuid.uuid4().hex)
        self.env = {'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': str(home), 'DOCKER_CONFIG': str(config),
                    'DOCKER_HOST': docker_host, 'LANG': 'C.UTF-8'}
        self.image = 'nstack-ai-workflows:' + self.fingerprint

    def call(self, args, log=None, check=True, timeout=600):
        result = subprocess.run([self.docker, *map(str, args)], env=self.env, capture_output=True,
                                text=True, timeout=timeout)
        if log is not None:
            Path(str(log) + '.stdout.log').write_text(result.stdout)
            Path(str(log) + '.stderr.log').write_text(result.stderr)
        if check and result.returncode:
            raise ValueError('Docker operation failed (exit %s); inspect task-owned logs' % result.returncode)
        return result

    @contextmanager
    def lock(self):
        with (self.parent / '.writer.lock').open('a') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            yield

    def image_info(self):
        info = json.loads(self.call(['image', 'inspect', self.image]).stdout)[0]
        labels = info['Config'].get('Labels') or {}
        if labels.get('org.nstack.owner') != OWNER or labels.get('org.nstack.fingerprint') != self.fingerprint:
            raise ValueError('Unowned or changed image preserved')
        if info.get('Architecture') != 'arm64' or info.get('Os') != 'linux':
            raise ValueError('This wheel lock is Linux arm64 only')
        return info

    def verify(self):
        if self.root.resolve() != self.root or (self.root / 'SOURCE.json').is_symlink() or not (self.root / 'SOURCE.json').is_file():
            raise ValueError('No owned commissioned runtime')
        receipt = json.loads((self.root / 'SOURCE.json').read_text())
        if receipt.get('inputs') != self.inputs or receipt.get('fingerprint') != self.fingerprint:
            raise ValueError('Runtime source identity changed; preserved')
        for name in INPUTS:
            path = self.root / 'context' / name
            if path.resolve() != path or digest(path) != self.inputs[name]:
                raise ValueError('Runtime input changed; preserved')
        source = json.loads((TEMPLATE / 'SOURCE.json').read_text())
        expected_wheels = {unquote(Path(urlparse(row['url']).path).name): row['sha256'] for row in source['wheels']}
        if receipt['wheels'] != expected_wheels or {p.name for p in (self.root / 'context/wheelhouse').iterdir()} != set(expected_wheels):
            raise ValueError('Wheel inventory differs from published provenance')
        for name, expected in expected_wheels.items():
            path = self.root / 'context/wheelhouse' / name
            if Path(name).name != name or not name.endswith('.whl') or path.resolve() != path or digest(path) != expected:
                raise ValueError('Runtime wheel changed; preserved')
        archive = self.root / 'runtime-image.tar'
        if archive.resolve() != archive or digest(archive) != receipt['image_archive_sha256']:
            raise ValueError('Durable private image archive changed; preserved')
        info = self.image_info()
        if info['Id'] != receipt['image_id']:
            raise ValueError('Runtime image identity changed; preserved')
        return receipt

    def install(self):
        with self.lock():
            if self.root.exists() or self.root.is_symlink():
                return self.verify()
            info = json.loads(self.call(['info', '--format', '{{json .}}']).stdout)
            if info['Architecture'] not in ('aarch64', 'arm64') or info['OSType'] != 'linux':
                raise ValueError('Current lock requires an existing Linux arm64 daemon')
            # Failed preparation bytes/logs stay private for diagnosis. Only a
            # complete validated build is renamed into the versioned runtime.
            temporary = tempfile.mkdtemp(prefix='.prepare-', dir=self.parent)
            stage = Path(temporary)
            context = stage / 'context'
            context.mkdir()
            for name in INPUTS:
                shutil.copy2(TEMPLATE / name, context / name)
            wheels = context / 'wheelhouse'
            wheels.mkdir()
            self.call(['pull', BASE], stage / 'pull')
            self.call(['run', '--rm', '--name', 'nstack-ai-download-' + uuid.uuid4().hex,
                       '--label', 'org.nstack.owner=' + OWNER, '--read-only', '--memory', '1g', '--cpus', '1',
                       '--pids-limit', '128', '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                       '--user', f'{os.getuid()}:{os.getgid()}', '--tmpfs', '/tmp:rw,nosuid,nodev,size=256m',
                       '--mount', f'type=bind,source={context},target=/work', BASE,
                       'python', '-m', 'pip', 'download', '--no-cache-dir', '--disable-pip-version-check',
                       '--index-url', 'https://pypi.org/simple', '--only-binary=:all:', '--no-deps',
                       '--require-hashes', '--dest', '/work/wheelhouse', '-r', '/work/requirements.lock'], stage / 'download')
            self.call(['build', '--network', 'none', '--pull=false', '--label', 'org.nstack.owner=' + OWNER,
                       '--label', 'org.nstack.fingerprint=' + self.fingerprint, '--tag', self.image, context], stage / 'build')
            built = self.image_info()
            self.call(['image', 'save', '--output', stage / 'runtime-image.tar', built['Id']], stage / 'save-image')
            (stage / 'runtime-image.tar').chmod(0o600)
            receipt = {'fingerprint': self.fingerprint, 'inputs': self.inputs, 'image_id': built['Id'],
                       'base': BASE, 'platform': 'linux/arm64', 'python': '3.12.16',
                       'wheels': {p.name: digest(p) for p in wheels.iterdir()},
                       'state': 'built; synthetic acceptance required', 'provider_extras': False,
                       'runtime_egress': 'none', 'created_unix': time.time()}
            receipt['image_archive_sha256'] = digest(stage / 'runtime-image.tar')
            dump(stage / 'SOURCE.json', receipt)
            # Rename only a fresh complete version, preserving any prior valid runtime.
            os.rename(stage, self.root)
            return self.verify()

    def execute(self, arguments, out, project=None):
        receipt = self.verify()
        out = Path(out).absolute()
        if out.resolve() != out or not out.is_dir() or out.parent != self.root / 'runs' or not re.fullmatch('[0-9a-f]{32}', out.name):
            raise ValueError('A real owned output directory is required')
        name = 'nstack-ai-run-' + uuid.uuid4().hex
        args = ['create', '--name', name, '--label', 'org.nstack.owner=' + OWNER,
                '--label', 'org.nstack.fingerprint=' + self.fingerprint, '--network', 'none',
                '--read-only', '--memory', '1g', '--cpus', '1', '--pids-limit', '128',
                '--cap-drop', 'ALL', '--security-opt', 'no-new-privileges',
                '--user', f'{os.getuid()}:{os.getgid()}', '--tmpfs', '/tmp:rw,nosuid,nodev,noexec,size=64m',
                '--mount', f'type=bind,source={out},target=/work', '--env', 'LANGSMITH_TRACING=false',
                '--env', 'LANGCHAIN_TRACING_V2=false']
        if project is not None:
            project = self.bounded_project(project)
            args += ['--mount', f'type=bind,source={project},target=/project,readonly']
        args += [receipt['image_id'], *arguments]
        self.call(args)
        try:
            inspection = json.loads(self.call(['inspect', name]).stdout)[0]
            validate_container(inspection, out, project, self.fingerprint, receipt['image_id'])
            result = self.call(['start', '--attach', name], check=False, timeout=120)
            final = json.loads(self.call(['inspect', name]).stdout)[0]
            if final['State']['Running'] or final['State'].get('OOMKilled'):
                raise ValueError('Container did not complete within resource bounds')
            return {'exit_code': final['State']['ExitCode'], 'stdout': result.stdout, 'stderr': result.stderr,
                    'inspection': inspection, 'final_state': final['State'], 'executor_sha256': digest(__file__)}
        finally:
            # Only remove the exact owned name/label; no daemon-wide cleanup.
            current = json.loads(self.call(['inspect', name]).stdout)[0]
            if (current['Config'].get('Labels') or {}).get('org.nstack.owner') == OWNER:
                self.call(['rm', '--force', name])

    def bounded_project(self, project):
        raw = Path(project).absolute()
        project = raw.resolve(strict=True)
        if raw != project or not project.is_dir() or project in (Path('/'), Path.home().resolve()):
            raise ValueError('A bounded real project directory is required')
        private = [self.state.resolve(), Path.home() / '.codex', Path.home() / '.docker',
                   Path.home() / '.config', Path.home() / '.agents', Path.home() / '.local',
                   Path.home() / '.ssh', Path.home() / '.aws', Path.home() / '.gnupg',
                   Path.home() / 'Library', Path.home() / 'Knowledge']
        if any(project == p or project.is_relative_to(p) or p.is_relative_to(project) for p in private):
            raise ValueError('Host settings, vault and runtime roots cannot be project mounts')
        if ',' in str(project):
            raise ValueError('Comma in mount path is unsupported')
        return project

    def check(self):
        self.verify()
        runs = safe_directory(self.root / 'runs')
        out = runs / uuid.uuid4().hex
        out.mkdir(mode=0o700)
        report = {'status': 'incomplete', 'fingerprint': self.fingerprint, 'phases': []}
        dump(out / 'run.json', report)
        try:
            for phase, expected in [('pause', 0), ('crash', 23), ('resume', 0), ('wrong-result', 1)]:
                result = self.execute(['/opt/smoke.py', phase], out)
                dump(out / (phase + '.json'), result)
                if result['exit_code'] != expected:
                    raise ValueError('Unexpected synthetic phase exit: ' + phase)
                if expected == 0:
                    parsed = json.loads(result['stdout'].strip())
                    if not parsed.get('network_denied') or parsed.get('tool_result') != 12:
                        raise ValueError('Missing offline/tool evidence')
                    report['phases'].append(parsed)
                else:
                    report['phases'].append({'phase': phase, 'expected_exit': expected, 'actual_exit': result['exit_code']})
            report.update(status='passed', checks=['offline_tool', 'typed_tool_negative', 'persisted_interrupt',
                          'fresh_container_resume', 'crash_after_effect', 'exactly_one_effect', 'wrong_answer_negative',
                          'container_scope'], artifacts={p.name: digest(p) for p in out.iterdir() if p.name != 'run.json'})
        finally:
            dump(out / 'run.json', report)
        return {'output': str(out), **report}


def validate_container(info, out, project, fingerprint, image_id):
    host = info['HostConfig']
    labels = info['Config'].get('Labels') or {}
    if labels.get('org.nstack.owner') != OWNER or labels.get('org.nstack.fingerprint') != fingerprint or info['Image'] != image_id:
        raise ValueError('Container ownership/image differs')
    if host['NetworkMode'] != 'none' or not host['ReadonlyRootfs'] or host.get('Privileged'):
        raise ValueError('Container isolation differs')
    if host.get('PortBindings') or host.get('RestartPolicy', {}).get('Name') not in ('no', ''):
        raise ValueError('Unexpected published port or persistent restart')
    if host.get('Memory') != 1073741824 or host.get('NanoCpus') != 1000000000 or host.get('PidsLimit') != 128:
        raise ValueError('Container resource bounds differ')
    if host.get('CapAdd') or host.get('CapDrop') != ['ALL'] or 'no-new-privileges' not in ' '.join(host.get('SecurityOpt') or []):
        raise ValueError('Container privilege policy differs')
    wanted = {'/work': (str(out), True)}
    if project is not None:
        wanted['/project'] = (str(project), False)
    actual = {m['Destination']: (m['Source'], m['RW']) for m in info['Mounts'] if m['Type'] == 'bind'}
    if actual != wanted or any(m['Type'] not in ('bind', 'tmpfs') for m in info['Mounts']):
        raise ValueError('Container mounts differ')
    env = dict(x.split('=', 1) for x in info['Config']['Env'] if '=' in x)
    if env.get('LANGSMITH_TRACING') != 'false' or env.get('LANGCHAIN_TRACING_V2') != 'false':
        raise ValueError('Tracing is not disabled')
    if any(k.endswith(('API_KEY', 'TOKEN')) or k in {'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY'} for k in env):
        raise ValueError('Unexpected credential environment')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', default=str(STATE))
    parser.add_argument('--docker-host')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('install')
    sub.add_parser('verify')
    sub.add_parser('check')
    run = sub.add_parser('run')
    run.add_argument('--project', required=True)
    run.add_argument('--script', required=True, help='Relative Python script within the explicitly mounted project')
    args = parser.parse_args()
    runtime = Runtime(args.state, args.docker_host)
    if args.command == 'run':
        project = runtime.bounded_project(args.project)
        script = Path(args.script)
        if script.is_absolute() or '..' in script.parts or script.suffix != '.py' or not (project / script).is_file() or (project / script).resolve() != project / script:
            raise ValueError('Provide an existing unlinked relative project Python script')
        runtime.verify()
        runs = safe_directory(runtime.root / 'runs')
        out = runs / uuid.uuid4().hex
        out.mkdir(mode=0o700)
        result = runtime.execute(['/project/' + str(script)], out, project)
        dump(out / 'run.json', result)
        print(json.dumps({'output': str(out), 'exit_code': result['exit_code']}))
        raise SystemExit(result['exit_code'])
    print(json.dumps(getattr(runtime, args.command)(), indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
