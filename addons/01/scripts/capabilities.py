#!/usr/bin/env python3
"""Bounded discovery from nstack indexes and current user/project skill metadata."""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import stat

MAX_FRONTMATTER = 16384
MAX_PATHS = 8192
MAX_DEPTH = 6
SKIP = {'.git', 'node_modules', '__pycache__', '.cache', 'cache', 'caches', '.venv'}
PRIVATE = {'.ssh', '.aws', '.gnupg', '.azure', '.kube', 'keychains',
           'credentials', 'secrets', 'passwords'}


def safe(path):
    """Inspect paths, never account/provider stores or plugin cache trees."""
    parts = [p.casefold() for p in path.parts]
    return not (PRIVATE.intersection(parts) or SKIP.intersection(parts)
                or any(a == 'plugins' and b == 'cache' for a, b in zip(parts, parts[1:])))


@contextmanager
def directory_fd(path):
    """Walk a validated absolute path without following any component symlink."""
    required = ('O_DIRECTORY', 'O_NOFOLLOW', 'O_NONBLOCK')
    if (os.open not in os.supports_dir_fd or any(not hasattr(os, key) for key in required)
            or not path.is_absolute() or '..' in path.parts or not safe(path)):
        raise ValueError('Safe descriptor-relative discovery is unavailable for this path')
    descriptor = None
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, 'O_CLOEXEC', 0)
    try:
        descriptor = os.open(path.anchor, flags)
        for component in path.parts[1:]:
            following = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = following
        yield descriptor
    finally:
        if descriptor is not None:
            os.close(descriptor)


@contextmanager
def regular_file(path):
    """Nonblocking/no-follow open plus fstat before any content is read."""
    descriptor = None
    with directory_fd(path.parent) as parent:
        try:
            descriptor = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
                                 | getattr(os, 'O_CLOEXEC', 0), dir_fd=parent)
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise ValueError('Discovery input is not a regular file')
            stream = os.fdopen(descriptor, 'rb')
            descriptor = None
            with stream:
                yield stream
        finally:
            if descriptor is not None:
                os.close(descriptor)


def frontmatter(entry):
    """Read only the bounded YAML header. No YAML tags or code are evaluated."""
    with regular_file(entry) as stream:
        first = stream.readline(MAX_FRONTMATTER + 1)
        if first.removeprefix(b'\xef\xbb\xbf').rstrip(b'\r\n') != b'---':
            return {}, b''
        raw = first
        while len(raw) <= MAX_FRONTMATTER:
            line = stream.readline(MAX_FRONTMATTER - len(raw) + 1)
            if not line:
                break
            raw += line
            if line.rstrip(b'\r\n') == b'---':
                if len(raw) > MAX_FRONTMATTER:
                    break
                lines = raw.decode('utf-8').splitlines()[1:-1]
                values = {}
                for i, line in enumerate(lines):
                    match = re.match(r'^(name|description|disable-model-invocation):\s*(.*)$', line)
                    if not match:
                        continue
                    key, value = match.groups()
                    if re.fullmatch(r'[>|][1-9]?[+-]?(?:\s+#.*)?', value):
                        block = []
                        for following in lines[i + 1:]:
                            if following.strip() and not following[0].isspace():
                                break
                            block.append(following)
                        indent = min((len(v) - len(v.lstrip()) for v in block if v.strip()), default=0)
                        block = [v[indent:] if v.strip() else '' for v in block]
                        value = '\n'.join(block)
                        if value is not None and match.group(2).startswith('>'):
                            value = re.sub(r'(?<=\S)\n(?=\S)', ' ', value)
                        value = value.strip()
                    elif value.startswith('"'):
                        try:
                            value, _ = json.JSONDecoder().raw_decode(value)
                        except ValueError:
                            value = value.strip('"')
                    elif value.startswith("'"):
                        quoted = re.match(r"^'((?:[^']|'')*)'(?:\s+#.*)?$", value)
                        value = quoted.group(1).replace("''", "'") if quoted else value.strip("'")
                    else:
                        value = re.split(r'\s+#', value, maxsplit=1)[0].strip()
                    if isinstance(value, str):
                        values[key] = value
                return values, raw
    raise ValueError('Skill frontmatter exceeds the bound or has no closing delimiter')


def skill_record(entry, name, deployment, metadata=None):
    record = {'kind': 'skill', 'name': name, 'path': str(entry),
              'instructions_present': metadata is not None, 'deployment': deployment}
    if metadata is not None:
        values, raw = metadata
        record['description'] = values.get('description', '')
        record['metadata_sha256'] = hashlib.sha256(raw).hexdigest()
        record['hash_scope'] = 'SKILL.md frontmatter only'
        if values.get('disable-model-invocation', '').casefold() == 'true':
            record['manual_only'] = True
    return record


def inventory(state, skill_roots=None):
    state = Path(state).expanduser().resolve()
    records, sources, seen = [], [], set()
    for filename, kind in (("native-skill-index.json", "skill"),
                           ("native-tools/index.json", "runtime")):
        source = state / filename
        resolved = source.resolve()
        if source.is_symlink() or resolved != source or not safe(resolved) or not resolved.is_relative_to(state):
            raise ValueError('Index must be a regular in-state path without redirects or private/cache trees')
        if not source.is_file():
            continue
        with regular_file(resolved) as stream:
            raw = stream.read()
        rows = json.loads(raw)
        if not isinstance(rows, list):
            raise ValueError("Expected an array in " + filename)
        sources.append({"file": str(source), "sha256": hashlib.sha256(raw).hexdigest()})
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("name"), str):
                continue
            if kind == 'skill':
                entry = Path(row.get('skill_path', ''))
                try:
                    resolved = entry.resolve()
                    if (entry.name != 'SKILL.md' or resolved.name != 'SKILL.md'
                            or not safe(resolved)
                            or not resolved.is_relative_to((state / 'native-releases').resolve())):
                        continue
                    if resolved in seen:
                        continue
                    metadata = frontmatter(resolved) if resolved.is_file() else None
                    record = skill_record(entry, row['name'], row.get('deployment', 'recorded'), metadata)
                    seen.add(resolved)
                except (OSError, ValueError, RuntimeError):
                    continue
            else:
                record = {'kind': 'runtime', 'name': row['name']}
                for key in ('version', 'source_revision', 'native_mcp', 'binary', 'python', 'node', 'entrypoint'):
                    if isinstance(row.get(key), str):
                        record[key] = row[key]
                if isinstance(row.get('checks'), str):
                    record['recorded_checks'] = row['checks']
            records.append(record)
    roots = [Path(p).expanduser().absolute() for p in (skill_roots or [])]
    allowed = [(state / 'native-releases').resolve()]
    for root in roots:
        try:
            if safe(root) and safe(root.resolve()):
                allowed.append(root.resolve())
        except (OSError, RuntimeError):
            pass
    remaining = MAX_PATHS
    for root in roots:
        pairs, visited, skipped = [], set(), 0
        pending = [(root, 0)]
        while pending and remaining:
            path, depth = pending.pop()
            remaining -= 1
            try:
                resolved = path.resolve()
                if (not safe(path) or not safe(resolved) or resolved in visited
                        or not any(resolved.is_relative_to(base) for base in allowed)):
                    skipped += 1
                    continue
                visited.add(resolved)
                if not resolved.is_dir():
                    continue
                entry = path / 'SKILL.md'
                if entry.exists() or entry.is_symlink():
                    target = entry.resolve()
                    if (target.name != 'SKILL.md' or not safe(target)
                            or not any(target.is_relative_to(base) for base in allowed)):
                        skipped += 1
                        continue
                    values, raw = frontmatter(target)
                    pairs.append((str(target), hashlib.sha256(raw).hexdigest()))
                    if target not in seen:
                        record = skill_record(entry, values.get('name') or path.name,
                                              'current file; host enablement not established', (values, raw))
                        records.append(record)
                        seen.add(target)
                    continue  # Support directories never become extra skills.
                if depth < MAX_DEPTH:
                    # A shared path budget also bounds directory enumeration.
                    children = []
                    if os.scandir not in os.supports_fd:
                        raise ValueError('Descriptor-relative directory enumeration is unavailable')
                    with directory_fd(resolved) as descriptor, os.scandir(descriptor) as entries:
                        for item in entries:
                            remaining -= 1
                            if remaining < 0:
                                remaining = 0
                                break
                            try:
                                if item.name.casefold() not in SKIP and (item.is_dir(follow_symlinks=False) or item.is_symlink()):
                                    children.append(path / item.name)
                            except OSError:
                                skipped += 1
                    pending.extend((child, depth + 1) for child in sorted(children, reverse=True))
            except (OSError, ValueError, RuntimeError):
                skipped += 1
        sources.append({'root': str(root), 'sha256': hashlib.sha256(json.dumps(sorted(pairs)).encode()).hexdigest(),
                        'hash_scope': 'resolved SKILL paths and frontmatter hashes', 'skills': len(pairs),
                        'skipped': skipped, 'path_budget_exhausted': remaining == 0,
                        'max_depth': MAX_DEPTH})
    return records, sources


def search(state, terms, limit=8, skill_roots=None):
    records, sources = inventory(Path(state), skill_roots=skill_roots)
    words = [word.casefold() for word in terms if word.strip()]
    ranked = []
    for record in records:
        text = ' '.join(str(record.get(key, '')) for key in
                        ('name', 'description', 'native_mcp', 'recorded_checks')).casefold()
        score = sum(word in text for word in words)
        if score:
            ranked.append((score, record))
    ranked.sort(key=lambda item: (-item[0], item[1]['kind'], item[1]['name']))
    return {'matches': [row for _, row in ranked[:limit]], 'total_matches': len(ranked),
            'sources': sources,
            'scope': 'Fresh local metadata discovery only. A record or current file does not prove host '
                     'enablement, callability, authorization or successful execution. '
                     'Connected host tools and plugins require native discovery separately.'}


def default_skill_roots(home=None, cwd=None):
    home, cwd = Path(home or Path.home()), Path(cwd or Path.cwd())
    roots = [home / '.agents/skills', home / '.codex/skills', home / '.config/opencode/skills']
    for folder in [cwd, *cwd.parents]:
        roots.extend((folder / '.agents/skills', folder / '.opencode/skills'))
        if (folder / '.git').exists() or folder == home:
            break
    return list(dict.fromkeys(roots))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('terms', nargs='+')
    parser.add_argument('--state', type=Path, help='Isolated index lookup unless --skills-root is also supplied')
    parser.add_argument('--skills-root', type=Path, action='append', help='Also enumerate this skill root; repeatable')
    parser.add_argument('--limit', type=int, default=8)
    args = parser.parse_args()
    if not 1 <= args.limit <= 30:
        parser.error('--limit must be between 1 and 30')
    roots = args.skills_root if args.skills_root is not None else (None if args.state is not None else default_skill_roots())
    state = args.state or Path(os.environ.get('NSTACK_STATE', Path.home() / 'Library/Application Support/nstack'))
    try:
        print(json.dumps(search(state, args.terms, args.limit, skill_roots=roots), indent=2))
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(2, str(error) + '\n')


if __name__ == '__main__':
    main()
