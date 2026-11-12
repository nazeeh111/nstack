#!/usr/bin/env python3
"""Small OpenCode V2 adapter. Reuse nstack files without copying host secrets."""
import argparse, hashlib, json, os, pathlib, re, shlex, subprocess, sys
P = pathlib.Path
ROOT = P(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'lib'))
from transaction import Transaction, atomic_json, copy, fingerprint, same
import install as profile_install



def knowledge_permissions(config, home, vault, write=None):
    """Share the explicit vault without weakening native read-only roles."""
    if write not in (None, 'ask', 'allow'):
        raise ValueError('Vault writes must preserve current policy, ask, or allow')
    home, vault = P(home).resolve(), P(vault).absolute()
    forbidden = {'.ssh', '.aws', '.codex', '.config', '.local', '.kube', '.gnupg',
                 '.azure', '.docker', 'keychains', 'credentials', 'secrets', 'passwords'}
    if (vault.resolve() != vault or not vault.is_dir() or vault in (P('/'), home)
            or forbidden.intersection(part.casefold() for part in vault.parts)):
        raise ValueError('Select a real, unlinked knowledge vault outside credential/configuration stores')
    pattern, example = str(vault) + '/*', str(vault / 'Home.md')
    def expanded(value):
        for prefix in ('~/', '$HOME/', '${HOME}/'):
            if value.startswith(prefix):
                return str(home) + '/' + value[len(prefix):]
        return value
    def matches(value, pattern):
        # Match native whole values: only * and ? are wildcards, not [] classes.
        return re.fullmatch(re.escape(pattern).replace(r'\*','.*').replace(r'\?','.'), value) is not None
    def denied(rows):
        return any(rule.get('effect') == 'deny'
                   and any(matches(action, rule.get('action','')) for action in ('external_directory','read','edit'))
                   and matches(example, expanded(rule.get('resource', ''))) for rule in rows)
    rows = list(config.get('permissions', []))
    if denied(rows):
        raise ValueError('Existing knowledge denial preserved; resolve vault access explicitly')
    grant = {'action': 'external_directory', 'resource': pattern, 'effect': 'allow'}
    rows = [rule for rule in rows if not (rule.get('action') == 'external_directory' and expanded(rule.get('resource','')) == pattern)]
    index = next((i for i, rule in enumerate(rows) if matches('external_directory',rule.get('action',''))
                  and expanded(rule.get('resource','')).startswith(str(vault) + '/')), len(rows))
    if any(matches('external_directory',rule.get('action','')) and rule.get('resource') == '*' for rule in rows[index:]):
        raise ValueError('Ambiguous existing permission order preserved')
    rows[index:index] = [grant]
    agents = {key: dict(value) for key,value in config.get('agents',{}).items()}
    # Agent rules run after global rules. Keep global edit denials behind the
    # scoped choice, with existing narrower agent rules as the final authority.
    global_edit_denials = []
    for rule in rows:
        if (rule.get('effect') == 'deny' and matches('edit', rule.get('action', ''))
                and rule not in global_edit_denials):
            global_edit_denials.append(rule)
    for name in ('build', 'general'):
        current = dict(agents.get(name, {})); rules = list(current.get('permissions', []))
        if denied(rules):
            raise ValueError('Existing agent knowledge denial preserved')
        existing = [rule['effect'] for rule in rules if rule.get('action') == 'edit'
                    and expanded(rule.get('resource', '')) == pattern]
        effect = write if write is not None else existing[-1] if existing else 'ask'
        rules = [rule for rule in rules if not (rule.get('action') == 'edit' and expanded(rule.get('resource','')) == pattern)]
        preserved = [rule for rule in global_edit_denials if rule not in rules]
        rules = [{'action':'edit','resource':pattern,'effect':effect}, *preserved, *rules]
        current['permissions'] = rules; agents[name] = current
    return {**config, 'permissions': rows, 'agents': agents}


def plan(home, state, cli, codex=None, vault=None, vault_write=None):
    if vault_write is not None and vault is None:
        raise ValueError('An explicit vault is required for its write policy')
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
    previous_config = (json.dumps(config, indent=2) + '\n').encode()
    if codex is not None:
        codex = P(codex).absolute()
        if version != 'opencode v2.2.6':
            raise ValueError('The optional Codex terminal launcher is checked against OpenCode 2.2.6')
        if not codex.is_file() or not os.access(codex, os.X_OK):
            raise ValueError('An existing executable native Codex CLI is required')
        native_version = subprocess.run([str(codex), '--version'], check=True, text=True, capture_output=True).stdout.strip()
        if not native_version.startswith('codex-cli '):
            raise ValueError('Expected a native Codex CLI executable')
        plugin = directory / 'plugins/nstack-codex'
        for name in ('package.json', 'gui-experimental.cjs'):
            files[plugin / name] = (ROOT / 'integrations/opencode-codex' / name).read_bytes()
        config['plugins'] = [{'package': str(plugin), 'options': {'codex': str(codex)}}]
    configured = (json.dumps(config, indent=2) + '\n').encode()
    existing_config = None
    # Keep explicit user security policy without adopting provider configuration.
    # All adapter-owned fields must still match this or the pre-launcher adapter.
    if config_path.is_file() and not config_path.is_symlink():
        raw = config_path.read_bytes()
        existing_config = raw
        try:
            current = json.loads(raw)
        except (ValueError, UnicodeError):
            raise ValueError('Existing configuration is preserved; review before replacing: ' + str(config_path)) from None
        allowed = set(config) | {'permissions', 'policies', 'agents'}
        if not isinstance(current, dict) or set(current) - allowed:
            raise ValueError('Existing configuration is preserved; review before replacing: ' + str(config_path))
        extra = {k: current[k] for k in ('permissions', 'policies', 'agents') if k in current}
        owned = {k: v for k, v in current.items() if k not in extra}
        if (any(not isinstance(v, list) for k,v in extra.items() if k != 'agents')
                or ('agents' in extra and (not isinstance(extra['agents'],dict)
                    or any(not isinstance(v,dict) or set(v)-{'permissions'} or not isinstance(v.get('permissions',[]),list) for v in extra['agents'].values())))):
            raise ValueError('Existing configuration is preserved; review before replacing: ' + str(config_path))
        if owned == config:
            configured = raw
        elif codex is not None and owned == json.loads(previous_config):
            configured = (json.dumps({**config, **extra}, indent=2) + '\n').encode()
        else:
            raise ValueError('Existing configuration is preserved; review before replacing: ' + str(config_path))
    if vault is not None:
        value = json.loads(configured)
        updated = knowledge_permissions(value, home, vault, vault_write)
        if updated != value:
            configured = (json.dumps(updated, indent=2) + '\n').encode()
    files[config_path] = configured
    links = {directory / 'AGENTS.md': agents, home / '.local/bin/opencode': cli}
    # Do not parse provider configuration, credential stores or alternate JSONC.
    if (directory / 'opencode.jsonc').exists() or (directory / 'opencode.jsonc').is_symlink():
        raise ValueError('Existing OpenCode JSONC is preserved; merge this adapter manually after review')
    for path, data in files.items():
        accepted = (data, existing_config) if path == config_path and existing_config is not None else (data,)
        if path.is_symlink() or (path.exists() and (not path.is_file() or path.read_bytes() not in accepted)):
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


def apply(home, state, cli, codex=None, vault=None, vault_write=None):
    home, state = P(home).resolve(), P(state).resolve()
    files, links, version = plan(home, state, cli, codex, vault, vault_write)
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
        checked_files, checked_links, checked_version = plan(home, state, cli, codex, vault, vault_write)
        if checked_files != files or checked_links != links or checked_version != version:
            raise ValueError('OpenCode configuration changed during preparation; preserved for review')
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
    install.add_argument('--codex-harness', metavar='EXECUTABLE', help='Add an explicit native Codex terminal command in OpenCode Desktop 2.2.6')
    install.add_argument('--vault', metavar='DIRECTORY', help='Share the explicit vault directory; preserve its write choice, initially ask')
    install.add_argument('--vault-write', choices=('ask', 'allow'), help='Explicit vault edit choice for build/general only; otherwise preserve its current policy')
    undo = sub.add_parser('rollback'); undo.add_argument('run'); undo.add_argument('--chain', action='store_true')
    args = parser.parse_args()
    result = apply(args.home, args.state, args.cli, args.codex_harness, args.vault, args.vault_write) if args.command == 'install' else rollback(args.run, args.chain)
    print(json.dumps(result, indent=2))

if __name__ == '__main__': main()
