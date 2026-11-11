#!/usr/bin/env python3
"""Fetch pinned static source privately. Never installs or executes upstream code."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
from urllib.request import Request, urlopen


def fetch(destination, manifest_path, source_dir=None):
    manifest = json.loads(Path(manifest_path).read_text())
    repository, revision = manifest['repository'], manifest['revision']
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('invalid pinned repository')
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('invalid immutable revision')
    files = manifest['files']
    if not files:
        raise ValueError('empty source closure')
    for name, digest in files.items():
        path = PurePosixPath(name)
        if path.is_absolute() or '..' in path.parts or str(path) != name or not re.fullmatch(r'[0-9a-f]{64}', digest):
            raise ValueError('invalid source path or hash')
    destination = Path(destination).expanduser().absolute()
    # Refuse existing targets, including links. Never replace a prior source pack.
    destination.mkdir(mode=0o700, parents=False, exist_ok=False)
    try:
        for name, expected in files.items():
            if source_dir is not None:
                source = Path(source_dir).resolve() / name
                if source.is_symlink() or not source.resolve().is_relative_to(Path(source_dir).resolve()):
                    raise ValueError('source must remain inside the selected cache')
                data = source.read_bytes()
            else:
                url = f'https://raw.githubusercontent.com/{repository}/{revision}/{name}'
                with urlopen(Request(url, headers={'User-Agent': 'nstack-static-source-fetch'}), timeout=20) as response:
                    if not response.geturl().startswith('https://raw.githubusercontent.com/'):
                        raise ValueError('unexpected source redirect')
                    data = response.read(2 * 1024 * 1024 + 1)
            if len(data) > 2 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != expected:
                raise ValueError(f'source hash/size mismatch: {name}')
            target = destination / name
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with target.open('xb') as output:
                output.write(data)
            target.chmod(0o600)
        receipt = {'repository': repository, 'revision': revision, 'files': files,
                   'source_only': True, 'upstream_code_executed': False}
        target = destination / 'NSTACK_SOURCE.json'
        with target.open('x') as output:
            json.dump(receipt, output, indent=2)
            output.write('\n')
        target.chmod(0o600)
    except BaseException:
        # This directory was exclusively created above and contains only this attempt.
        shutil.rmtree(destination)
        raise
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path, help='new private directory; its parent must exist')
    parser.add_argument('--source-dir', type=Path, help='replay hashes from an existing original repository without network')
    args = parser.parse_args()
    manifest = Path(__file__).resolve().parents[1] / 'private-source.json'
    try:
        result = fetch(args.destination, manifest, args.source_dir)
    except (ValueError, OSError) as error:
        parser.exit(2, f'{error}\n')
    print(json.dumps({'destination': str(args.destination.expanduser().absolute()),
                      'revision': result['revision'], 'files': len(result['files']), 'source_only': True}))


if __name__ == '__main__':
    main()
