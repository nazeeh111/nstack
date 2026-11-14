#!/usr/bin/env python3
"""Install host-specific Claude Code skill entries from verified nstack bundles."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'lib'))
import native_setup as native
import install as profile_install
from native_copy import copy_generated_tree
from transaction import Transaction, atomic_json, copy, fingerprint, same

ADDONS = {
    'agent-reach': ('agent-reach',), 'repository-docs': ('repository-docs',),
    'unslop': ('unslop',), 'maps-scraper': ('google-maps-scraper',),
    'untangle-codebase': ('untangle-codebase',), 'adaptive-routing': ('01',),
    'raea': ('raea',), 'llm-council': ('llm-council',),
    'craft-anything': ('craft-anything',),
    'cloudflare-security-audit': ('cloudflare-security-audit',),
    'strix': ('strix-security-testing',), 'skillspector': ('skillspector',),
    'roast-room': ('roast-room',),
    'council-of-high-intelligence': ('council-of-high-intelligence',),
}
# Preserve methods, not automatic permission grants, model changes or hooks.
DROP = {'allowed-tools', 'model', 'hooks', 'context', 'agent', 'shell'}
BEGIN, END = '<!-- nstack:start -->', '<!-- nstack:end -->'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def selected(args):
    chosen = native.selection()
    if args.only:
        wanted = set(args.only)
        if wanted - {name for name, _ in chosen}:
            raise ValueError('Unknown or non-installable selected skill name')
        chosen = [(name, spec) for name, spec in chosen if name in wanted]
    addons = [name for flag, names in ADDONS.items()
              if getattr(args, flag.replace('-', '_'), False) for name in names]
    if getattr(args, 'academic_research', False):
        import academic_addon
        addons.extend(academic_addon.DESCRIPTIONS)
    if getattr(args, 'ecc', False):
        import ecc_addon
        addons.extend(ecc_addon.DESCRIPTIONS)
    if set(addons) & {name for name, _ in chosen}:
        raise ValueError('Addon name collides with selected skill')
    return chosen, addons


def adapt_entry(raw, name):
    """Filter complete top-level YAML fields, leaving body/support bytes intact."""
    text = raw.decode('utf-8')
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip('\r\n') != '---':
        raise ValueError('Claude entry requires first-line YAML frontmatter: ' + name)
    closing = next((i for i in range(1, len(lines)) if lines[i].rstrip('\r\n') == '---'), None)
    if closing is None or sum(len(line) for line in lines[:closing + 1]) > 16384:
        raise ValueError('Missing or oversized skill frontmatter: ' + name)
    fields, key = {}, None
    for line in lines[1:closing]:
        match = re.match(r'^([a-zA-Z][\w/-]*):(?:\s|$)', line)
        if match:
            key = match.group(1)
            if key in fields:
                raise ValueError('Duplicate skill metadata field: ' + name + '/' + key)
            fields[key] = [line]
        elif not line.strip() or line.lstrip().startswith('#') or line[0].isspace():
            if key is not None:
                fields[key].append(line)
        else:
            raise ValueError('Unsupported skill metadata syntax: ' + name)
    if 'description' not in fields:
        raise ValueError('Skill description missing: ' + name)
    manual = name == '01'
    if 'disable-model-invocation' in fields:
        value = fields['disable-model-invocation'][0].split(':', 1)[1].split('#', 1)[0].strip().casefold()
        if value not in ('true', 'false', 'yes', 'no', 'on', 'off', '1', '0'):
            raise ValueError('Unsupported invocation policy: ' + name)
        manual |= value in ('true', 'yes', 'on', '1')
    body = ''.join(lines[closing + 1:])
    # Claude preprocesses these forms as shell execution before showing content.
    # The reviewed collection has none. Future additions require a scoped port.
    if re.search(r'(^|\s)!`|^\s*`{3,}!', body, re.MULTILINE):
        raise ValueError('Dynamic skill shell injection requires a reviewed Claude port: ' + name)
    kept = ''.join(''.join(value) for key, value in fields.items()
                   if key not in DROP | {'name', 'disable-model-invocation'})
    result = '---\nname: ' + json.dumps(name) + '\n' + kept
    if manual:
        result += 'disable-model-invocation: true\n'
    result += '---\n' + body
    return result.encode(), sorted(DROP.intersection(fields)), manual


def prepare(state, chosen, addons):
    """Derive and verify an immutable Claude view; never modify native bundles."""
    source, rows = native.prepare(state, chosen, addons)
    expected = {'bundles': {'directory': True, 'mode': 0o555},
                'originals': {'directory': True, 'mode': 0o555}}
    payloads, entries = {}, []
    for row in rows:
        name = row['name']
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', name) or name in ('synced', 'anthropic-skills'):
            raise ValueError('Unsupported Claude skill name: ' + name)
        entry = Path(row['skill_path'])
        bundle = source / 'bundles' / name
        if not entry.is_relative_to(bundle) or entry.name != 'SKILL.md':
            raise ValueError('Selected entry escapes its verified bundle')
        if (entry.parent / '.claude-plugin').exists():
            raise ValueError('Skill-directory plugin requires separate review: ' + name)
        raw = entry.read_bytes()
        adapted, removed, manual = adapt_entry(raw, name)
        rel = entry.relative_to(source)
        for path in [bundle, *sorted(bundle.rglob('*'))]:
            relative = str(path.relative_to(source))
            if path.is_symlink():
                raise ValueError('Linked support is not admitted in a Claude bundle')
            if path.is_dir():
                expected[relative] = {'directory': True, 'mode': 0o555}
            elif path.is_file():
                data = adapted if path == entry else path.read_bytes()
                mode = 0o555 if path.stat().st_mode & 0o111 else 0o444
                payloads[relative] = (path, data if path == entry else None, mode)
                expected[relative] = {'sha256': digest(data), 'mode': mode}
            else:
                raise ValueError('Nonregular support object in Claude bundle')
        original = 'originals/' + name + '/SKILL.md'
        expected['originals/' + name] = {'directory': True, 'mode': 0o555}
        expected[original] = {'sha256': digest(raw), 'mode': 0o444}
        payloads[original] = (entry, raw, 0o444)
        entries.append({**row, 'native_skill_path': str(entry), 'relative_entry': str(rel),
                        'removed_host_fields': removed, 'manual_only': manual})
    inputs = {'native_release': str(source), 'native_manifest_sha256': digest((source / 'NATIVE-MANIFEST.json').read_bytes()),
              'adapter_sha256': digest(Path(__file__).read_bytes()), 'adaptation': 'claude-entry-v1'}
    identity = digest(json.dumps({'inputs': inputs, 'files': expected}, sort_keys=True).encode())
    release = state / 'claude-releases' / identity
    index = [{**row, 'skill_path': str(release / row['relative_entry'])} for row in entries]
    index_raw = (json.dumps(index, sort_keys=True, indent=2) + '\n').encode()
    expected['index.json'] = {'sha256': digest(index_raw), 'mode': 0o444}
    if release.exists() or release.is_symlink():
        seal = release / 'NATIVE-MANIFEST.json'
        if release.is_symlink() or seal.is_symlink():
            raise ValueError('Linked Claude release or manifest')
        saved = json.loads(seal.read_text())
        if (saved != {'inputs': inputs, 'files': expected} or native.tree(release) != expected
                or release.stat().st_mode & 0o777 != 0o555 or seal.stat().st_mode & 0o777 != 0o444):
            raise ValueError('Claude release changed; preserve and reconcile')
        return release, index
    release.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.claude-', dir=release.parent) as temporary:
        out = Path(temporary) / 'release'
        # Clone complete bundles to keep every relative support path intact.
        out.mkdir()
        (out / 'bundles').mkdir()
        (out / 'originals').mkdir()
        for row in rows:
            copy_generated_tree(source / 'bundles' / row['name'], out / 'bundles' / row['name'])
        for relative, (_, data, mode) in payloads.items():
            dest = out / relative
            if data is not None:
                dest.parent.chmod(0o755) if dest.parent.exists() else dest.parent.mkdir(parents=True)
                if dest.exists():
                    dest.chmod(0o600)
                dest.write_bytes(data)
            dest.chmod(mode)
        (out / 'index.json').write_bytes(index_raw)
        for path in out.rglob('*'):
            if path.is_dir():
                path.chmod(0o555)
        (out / 'index.json').chmod(0o444)
        if native.tree(out) != expected:
            raise ValueError('Claude payload differs from verified inputs')
        atomic_json(out / 'NATIVE-MANIFEST.json', {'inputs': inputs, 'files': expected})
        (out / 'NATIVE-MANIFEST.json').chmod(0o444)
        os.rename(out, release)
        release.chmod(0o555)
    return release, index


def claude_directory(home, override=None):
    configured = override
    if configured is None and home == Path.home().resolve():
        configured = os.environ.get('CLAUDE_CONFIG_DIR')
    return Path(configured).expanduser().absolute() if configured else home / '.claude'


def block(state, vault, claude_home):
    knowledge = native.knowledge_guidance(vault) + '\n\n' + native.KNOWLEDGE_ROUTINE
    return f'''{BEGIN}
## nstack for Claude Code

Skills are installed as individual links in {claude_home / 'skills'}. Start adaptive session routing with /01; it remains explicit. Consider relevant skills by their methods and the current bottleneck. Preserve native manual-only invocation boundaries. If metadata is insufficient, inspect the current skill files and {state / 'claude-skill-index.json'}.

Use Claude Code's available native tools and connected MCPs. Codex tool names and account plugins are not automatically available here. Preserve the selected model, effort, permissions and existing account choices; do not install hooks, switch hosts or acquire provider access incidentally. Match a method to an actually callable host capability, verify its output, and report a missing route honestly. A skill is guidance, not permission for spending, credentials, messages, publishing, deployment, commits or pushes.

Installed specialist runtimes, when separately commissioned, are recorded in {state / 'native-tools/index.json'}. Recipes and source bundles alone do not prove installation or readiness. Heavy, hardware, trial and provider routes retain their individual prerequisites; use on demand.

{knowledge}
{END}'''


def instruction_block(text):
    if text.count(BEGIN) != text.count(END) or text.count(BEGIN) > 1:
        raise ValueError('Ambiguous nstack CLAUDE.md block')
    if BEGIN not in text:
        return None
    start, end = text.index(BEGIN), text.index(END) + len(END)
    if end < start:
        raise ValueError('Reversed nstack CLAUDE.md markers')
    return text[start:end]


def plan(home, state, release, index, vault, claude_home=None):
    claude_home = claude_home or home / '.claude'
    target = claude_home / 'skills'
    agents = claude_home / 'CLAUDE.md'
    profile, index_path = state / 'claude-profile.json', state / 'claude-skill-index.json'
    if target.is_symlink() or (target.exists() and not target.is_dir()):
        raise ValueError('Existing Claude skill root must be an unlinked directory; preserved')
    for path in (agents, profile, index_path):
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ValueError('Claude profile target must be a regular file: ' + str(path))
        native.check_parent(path)
    old = json.loads(profile.read_text()) if profile.exists() else None
    if old is not None and (old.get('home') != str(home) or not isinstance(old.get('links'), dict)):
        raise ValueError('Claude state belongs to another home or has an invalid profile')
    if old and old.get('claude_home', str(home / '.claude')) != str(claude_home):
        raise ValueError('Claude state targets another configuration directory; reconcile or use separate state')
    links = {row['name']: str(Path(row['skill_path']).parent) for row in index}
    previous = old['links'] if old else {}
    for name, destination in previous.items():
        if (not re.fullmatch(r'[a-z0-9][a-z0-9-]*', name) or not isinstance(destination, str)
                or not Path(destination).is_relative_to(state / 'claude-releases')):
            raise ValueError('Invalid owned Claude skill coordinate')
        path = target / name
        if not path.is_symlink() or os.readlink(path) != destination:
            raise ValueError('Owned Claude skill changed; preserve and reconcile: ' + name)
    for name in links.keys() - previous.keys():
        path = target / name
        if path.exists() or path.is_symlink():
            raise ValueError('Unowned Claude skill collision; preserved: ' + name)
    text = agents.read_text() if agents.exists() else ''
    existing = instruction_block(text)
    if (old and existing != old.get('block')) or (not old and existing is not None):
        raise ValueError('Unowned or changed nstack CLAUDE.md block; preserved')
    generated = block(state, vault, claude_home)
    content = text.replace(existing, generated, 1) if existing is not None else text + ('\n\n' if text else '') + generated + '\n'
    new_profile = {'home': str(home), 'claude_home': str(claude_home), 'release': str(release), 'links': links, 'block': generated}
    files = {agents: content.encode(), index_path: (json.dumps(index, sort_keys=True, indent=2) + '\n').encode(),
             profile: (json.dumps(new_profile, sort_keys=True, indent=2) + '\n').encode()}
    link_paths = {target / name: Path(destination) for name, destination in links.items()}
    retired = [target / name for name in sorted(previous.keys() - links.keys())]
    allowed = {path: {'absent', 'file'} for path in files} | {path: {'absent', 'link'} for path in [*link_paths, *retired]}
    native.preflight(allowed, state)
    before = {path: fingerprint(path) for path in allowed}
    return files, link_paths, retired, before


def apply(args):
    home, state = Path(args.home).expanduser().resolve(), Path(args.state).expanduser().resolve()
    claude_home = claude_directory(home, getattr(args, 'claude_home', None))
    if any(state.is_relative_to(root.resolve()) for root in (home / '.claude', claude_home)):
        raise ValueError('Private nstack state must remain outside Claude discovery/configuration')
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    native.nstack.STATE = state
    chosen, addons = selected(args)
    release, index = prepare(state, chosen, addons)
    files, links, retired, before = plan(home, state, release, index, args.vault, claude_home)
    if (not retired and all(before[path]['kind'] == 'file' and path.read_bytes() == data for path, data in files.items())
            and all(path.is_symlink() and os.readlink(path) == str(dest) for path, dest in links.items())):
        return {'changed': False, 'skills': len(index), 'release': str(release), 'claude_home': str(claude_home)}
    key = digest(json.dumps({'files': {str(p): digest(data) for p, data in files.items()},
                             'links': {str(p): str(t) for p, t in links.items()},
                             'before': {str(p): fp for p, fp in before.items()}}, sort_keys=True).encode())[:20]
    code = profile_install.stage(state)
    run = state / 'runs' / ('claude-' + key)
    tx = Transaction(run)
    with tx.lock():
        if plan(home, state, release, index, args.vault, claude_home) != (files, links, retired, before):
            raise ValueError('Concurrent Claude profile change; preserved')
        for number, (path, old) in enumerate(before.items()):
            if old['kind'] != 'absent':
                backup, rehearsal = run / 'snapshot' / str(number), run / 'rehearsal' / str(number)
                copy(path, backup)
                same(backup, old)
                copy(backup, rehearsal)
                same(rehearsal, old)
                same(path, old)
        pointer, helper = state / 'rollback.sh', run / 'rollback-claude.sh'
        if pointer.exists() and not pointer.is_symlink():
            raise ValueError('Unowned nstack rollback command; preserved')
        previous = str(pointer.resolve(strict=True)) if pointer.is_symlink() else None
        if previous and not Path(previous).is_relative_to(state / 'runs'):
            raise ValueError('Unowned rollback parent; preserved')
        atomic_json(run / 'parent.json', {'state': str(state), 'previous': previous})
        helper.write_text('#!/bin/sh\nset -eu\nexec ' + shlex.quote(sys.executable) + ' ' +
                          shlex.quote(str(code / 'claude_setup.py')) + ' rollback ' + shlex.quote(str(run)) + ' --chain\n')
        helper.chmod(0o700)
        nxt = state / '.claude-rollback-next'
        if nxt.exists() or nxt.is_symlink():
            raise ValueError('Unexpected pending Claude rollback pointer; preserved')
        nxt.symlink_to(helper)
        os.replace(nxt, pointer)  # Recovery exists before the first profile mutation.
        for path in retired:
            tx.retire(path, expected=before[path])
        for path, destination in links.items():
            tx.link(path, destination, expected=before[path])
        for path, data in files.items():
            mode = before[path].get('metadata', {}).get('mode', 0o600)
            tx.replace_file(path, data, mode, expected=before[path])
    return {'changed': True, 'skills': len(index), 'release': str(release), 'claude_home': str(claude_home),
            'run': str(run), 'rollback': str(pointer)}


def rollback(run, chain=False):
    run = Path(run).absolute()
    tx = Transaction(run)
    parent = json.loads((run / 'parent.json').read_text())
    with tx.lock():
        # Check the complete rollback before restoring any entry.
        for row in tx.rows:
            if row['phase'] == 'rolled-back':
                continue
            current = fingerprint(Path(row['path']))
            if current not in (row['before'], row['after'], row.get('rollback_result')):
                raise ValueError('Claude rollback conflict; current changes preserved: ' + row['path'])
            if row['before']['kind'] != 'absent':
                same(Path(row['backup']), row['before'])
        tx.rollback()
        pointer = Path(parent['state']) / 'rollback.sh'
        if pointer.is_symlink() and pointer.resolve() == run / 'rollback-claude.sh':
            if parent['previous']:
                nxt = pointer.with_name('.claude-rollback-previous')
                if nxt.is_symlink() and os.readlink(nxt) == parent['previous']:
                    pass
                elif nxt.exists() or nxt.is_symlink():
                    raise ValueError('Unexpected previous rollback pointer; preserved')
                else:
                    nxt.symlink_to(parent['previous'])
                os.replace(nxt, pointer)
            else:
                pointer.unlink()
    if chain and parent['previous']:
        subprocess.run([parent['previous']], check=True)
    return {'rolled_back': str(run)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    install = sub.add_parser('install')
    install.add_argument('--home', default=str(Path.home()))
    install.add_argument('--claude-home', help='Claude configuration directory; defaults to CLAUDE_CONFIG_DIR for the current user, otherwise HOME/.claude')
    install.add_argument('--state', default=str(native.nstack.STATE))
    install.add_argument('--only', action='append', help='Exact natural base-skill name; otherwise include the full reviewed base')
    install.add_argument('--vault', help='Existing explicitly authorized vault; does not change Claude file permissions')
    for flag in [*ADDONS, 'academic-research', 'ecc']:
        install.add_argument('--' + flag, action='store_true', help='Include the same reviewed selection as native_setup.py')
    undo = sub.add_parser('rollback')
    undo.add_argument('run')
    undo.add_argument('--chain', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(apply(args) if args.command == 'install' else rollback(args.run, args.chain), indent=2))
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()
