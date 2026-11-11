"""One source-preserving prerequisite correction for the pinned DevTools leaf."""
import difflib
import hashlib
import json

REVISION = '0877ee00d2e43c1c04bba275e7d08cc1033e36e9'
OLD = 'First check if these tools are available; if not, try to read the MCP configuration file to check if `--memoryDebugging` is enabled.'
NEW = ('**nstack prerequisite adaptation:** First check the names of tools exposed by the native connected-tool interface and any non-secret capability/status metadata it provides. '
       'If the memory tools are absent, report that capability gap; do not open MCP configuration files, configuration values or credential stores. '
       'Enabling `--memoryDebugging` or changing the server configuration requires the task\'s specific existing authority through the supported host interface.')


def patch(out):
    entry = out / 'SKILL.md'
    original = entry.read_bytes()
    text = original.decode()
    if text.count(OLD) != 1:
        raise ValueError('Pinned DevTools prerequisite anchor changed')
    final = text.replace(OLD, NEW).encode()
    archive = out / 'upstream-original' / 'SKILL.md.txt'
    archive.parent.mkdir(exist_ok=True)
    archive.write_bytes(original)
    entry.write_bytes(final)
    (out / 'ADAPTATION.patch').write_text(''.join(difflib.unified_diff(
        text.splitlines(keepends=True), final.decode().splitlines(keepends=True),
        fromfile='upstream/skills/memory-leak-debugging/SKILL.md', tofile='native/SKILL.md')))
    (out / 'NATIVE-ADAPTATION.json').write_text(json.dumps({
        'repository': 'ChromeDevTools/chrome-devtools-mcp', 'revision': REVISION,
        'source_path': 'skills/memory-leak-debugging/SKILL.md',
        'source_sha256': hashlib.sha256(original).hexdigest(),
        'native_sha256': hashlib.sha256(final).hexdigest(),
        'archival_original': 'upstream-original/SKILL.md.txt',
        'change': 'Replace the missing-tool configuration-read fallback with native tool names/non-secret status and a truthful capability gap. All memory investigation methods remain unchanged.',
        'boundary': 'Instructional admission rule; no OS sandbox or runtime enforcement is claimed.'
    }, indent=2) + '\n')
