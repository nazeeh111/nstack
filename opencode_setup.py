#!/usr/bin/env python3
"""Small OpenCode V2 adapter. Reuse nstack files without copying host secrets."""
import argparse, hashlib, json, os, pathlib, shlex, subprocess, sys
P = pathlib.Path
ROOT = P(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'lib'))
from transaction import Transaction, atomic_json, copy, fingerprint, same
import install as profile_install


def plan(home, state, cli):
    home, state, cli = P(home).resolve(), P(state).resolve(), P(cli).absolute()
    agents = home / '.codex/AGENTS.md'
    skills = home / '.agents/skills'
    if not agents.is_file() or agents.is_symlink() or not skills.is_dir():
        raise ValueError('Install the native nstack collection and user instructions first')
    if not cli.is_file() or not os.access(cli, os.X_OK):
        raise ValueError('An existing executable OpenCode V2 CLI is required')
    version = subprocess.run([str(cli), '--version'], check=True, text=True, capture_output=True).stdout.strip()
    if not version.startswith('opencode v2.'):
        raise ValueError('This adapter requires OpenCode V2; no automatic upgrade')
    config = {'$schema': 'https://opencode.ai/config.json', 'warming': False,
              'mcp': {'servers': {
                  'context7': {'type': 'remote', 'url': 'https://mcp.context7.com/mcp', 'oauth': False},
                  'gitmcp': {'type': 'remote', 'url': 'https://gitmcp.io/docs', 'oauth': False}}}}
    files = {}
    serena = state / 'native-tools/serena'
    command = serena / 'venv/bin/serena'
    if command.is_file():
        context = serena / 'opencode.yml'
        prompts = serena / 'opencode-home/prompt_templates/system_prompt.yml'
        files[context] = (ROOT / 'templates/serena/codex.yml').read_bytes().replace(b'for Codex', b'for coding agents')
        files[prompts] = (ROOT / 'templates/serena/system_prompt.yml').read_bytes()
        config['mcp']['servers']['serena'] = {
            'type': 'local', 'command': [str(command), 'start-mcp-server', '--context', str(context),
                '--mode', 'no-memories', '--agent-interface', 'tools', '--enable-web-dashboard', 'false',
                '--enable-gui-log-window', 'false', '--open-web-dashboard', 'false'],
            'environment': {'SERENA_HOME': str(serena / 'opencode-home')},
            'timeout': {'startup': 120000, 'execution': 120000}}
    directory = home / '.config/opencode'
    config_path = directory / 'opencode.json'
    files[config_path] = (json.dumps(config, indent=2) + '\n').encode()
    links = {directory / 'AGENTS.md': agents, home / '.local/bin/opencode': cli}
    # Do not parse provider configuration, credential stores or alternate JSONC.
    if (directory / 'opencode.jsonc').exists() or (directory / 'opencode.jsonc').is_symlink():
        raise ValueError('Existing OpenCode JSONC is preserved; merge this adapter manually after review')
    for path, data in files.items():
        if path.is_symlink() or (path.exists() and (not path.is_file() or path.read_bytes() != data)):
            raise ValueError('Existing configuration is preserved; review before replacing: ' + str(path))
    for path, target in links.items():
        if (path.exists() or path.is_symlink()) and not (path.is_symlink() and os.readlink(path) == str(target)):
            raise ValueError('Existing entry is preserved: ' + str(path))
    for path in [*files, *links]:
        ancestor = path.parent
        while not ancestor.exists():
            ancestor = ancestor.parent
        if ancestor.resolve() != ancestor or not ancestor.is_dir():
            raise ValueError('Linked or invalid target parent: ' + str(path))
    return files, links, version


def apply(home, state, cli):
    home, state = P(home).resolve(), P(state).resolve()
    files, links, version = plan(home, state, cli)
    if all(p.is_file() and p.read_bytes() == d for p, d in files.items()) and all(
            p.is_symlink() and os.readlink(p) == str(t) for p, t in links.items()):
        return {'changed': False, 'version': version, 'shared_skills': str(home / '.agents/skills')}
    key = hashlib.sha256(json.dumps({str(p): hashlib.sha256(d).hexdigest() for p, d in files.items()} |
            {str(p): str(t) for p, t in links.items()}, sort_keys=True).encode()).hexdigest()[:16]
    code = profile_install.stage(state)
    run = state / 'runs' / ('opencode-' + key)
    tx = Transaction(run)
    with tx.lock():
        # Revalidate after acquiring the shared profile writer lock.
        plan(home, state, cli)
        before = {p: fingerprint(p) for p in [*files, *links]}
        for index, (path, old) in enumerate(before.items()):
            if old['kind'] != 'absent':
                backup, rehearsal = run / 'snapshot' / str(index), run / 'rehearsal' / str(index)
                if not backup.exists() and not backup.is_symlink(): copy(path, backup)
                same(backup, old)
                if not rehearsal.exists() and not rehearsal.is_symlink(): copy(backup, rehearsal)
                same(rehearsal, old)
        pointer, helper = state / 'rollback.sh', run / 'rollback-opencode.sh'
        parent = run / 'parent.json'
        if not (pointer.is_symlink() and pointer.resolve() == helper):
            if pointer.exists() and not pointer.is_symlink(): raise ValueError('Unowned rollback command')
            previous = str(pointer.resolve(strict=True)) if pointer.is_symlink() else None
            if previous and not P(previous).is_relative_to(state / 'runs'): raise ValueError('Unowned rollback parent')
            atomic_json(parent, {'state': str(state), 'previous': previous})
        helper.write_text('#!/bin/sh\nset -eu\nexec ' + shlex.quote(sys.executable) + ' ' +
            shlex.quote(str(code / 'opencode_setup.py')) + ' rollback ' + shlex.quote(str(run)) + ' --chain\n')
        helper.chmod(0o700)
        nxt = state / '.opencode-rollback-next'
        if nxt.is_symlink(): nxt.unlink()
        nxt.symlink_to(helper); os.replace(nxt, pointer)
        for path, data in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            tx.replace_file(path, data, 0o600, expected=before[path])
        for path, target in links.items(): tx.link(path, target, expected=before[path])
    return {'changed': True, 'version': version, 'run': str(run), 'shared_skills': str(home / '.agents/skills')}


def rollback(run, chain=False):
    run = P(run).resolve(); tx = Transaction(run)
    with tx.lock():
        tx.rollback()
        parent = json.loads((run / 'parent.json').read_text())
        pointer = P(parent['state']) / 'rollback.sh'
        if pointer.is_symlink() and pointer.resolve() == run / 'rollback-opencode.sh':
            if parent['previous']:
                nxt = pointer.with_name('.opencode-rollback-previous')
                if nxt.is_symlink(): nxt.unlink()
                nxt.symlink_to(parent['previous']); os.replace(nxt, pointer)
            else: pointer.unlink()
    if chain and parent['previous']:
        subprocess.run([parent['previous']], check=True)
    return {'rolled_back': str(run)}


def main():
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest='command', required=True)
    install = sub.add_parser('install'); install.add_argument('--home', default=str(P.home()))
    install.add_argument('--state', default=str(P.home() / 'Library/Application Support/nstack'))
    install.add_argument('--cli', default='/Applications/OpenCode.app/Contents/Resources/opencode-cli')
    undo = sub.add_parser('rollback'); undo.add_argument('run'); undo.add_argument('--chain', action='store_true')
    args = parser.parse_args()
    result = apply(args.home, args.state, args.cli) if args.command == 'install' else rollback(args.run, args.chain)
    print(json.dumps(result, indent=2))

if __name__ == '__main__': main()
