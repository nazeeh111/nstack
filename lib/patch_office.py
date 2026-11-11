"""Retain OfficeCLI's format methods; port only runtime and verified correctness conflicts."""
import difflib, hashlib, json, pathlib, re, shutil
P = pathlib.Path

NATIVE = '''## Native runtime

Use this fallback only when the native artifact workflow lacks the requested operation. Resolve the recorded OfficeCLI1.0.160 binary, verify its hash/version and use its absolute path; `officecli` below denotes that binary. Do not install or register another runtime. Read version-matched help when a property is uncertain.

Work on a copy, preserve originals, use one writer and argv/JSON for user content. Set OUTPUT_DIR to a task-owned writable output directory before screenshot examples. Set `OFFICECLI_NO_AUTO_RESIDENT=1` for batch jobs; resident mode is optional, and requires explicit save/close before external readers. Styles, palettes, sizes and layouts below are upstream starting points, subordinate to the actual brief, brand and existing artifact. Apply the relevant checks; reuse valid evidence and recheck changed behavior without a fixed iteration count.

`validate` checks OpenXML schema. HTML/screenshots from it are previews. Render the actual artifact with the recorded compatible LibreOffice26.8.2/fonts and inspect PDF pages with Poppler; report any unavailable check. Exact Office-only behavior, VBA and PowerQuery require the licensed target Office environment. Keep the previous valid render until its replacement succeeds.

'''
RECALC = 'Recalculate with the recorded LibreOffice UNO calculateAll and storeAsURL to a new XLSX. Inspect formulas and independently reconciled cached values against source numbers, including cross-sheet formulas written before inputs. Retouching formulas, plausible manually set caches, a five-second save sweep or an empty verified-cache allowlist does not establish recalculation.'

def section(text, heading, replacement):
    start = text.index(heading)
    following = re.search(r'(?m)^## ', text[start + len(heading):])
    end = start + len(heading) + following.start() if following else len(text)
    return text[:start] + replacement.rstrip() + '\n\n' + text[end:]

def port(text, name):
    text = re.sub(r'(?m)^name:.*$', 'name: p333-' + name, text, count=1)
    description = 'OfficeCLI fallback for ' + {'officecli-docx':'editable DOCX', 'officecli-xlsx':'editable XLSX', 'officecli-pptx':'editable PPTX'}.get(name, 'editable Office artifacts') + ' when the native artifact workflow lacks a required operation.'
    text = re.sub(r'(?m)^description:.*$', 'description: ' + description, text, count=1)
    text = section(text, '## Install' if name == 'officecli' else '## Setup', '')
    if name == 'officecli':
        text = text.replace('**Every command auto-starts a resident on first access** (60s idle timeout) — file-lock conflicts are automatically avoided. Explicit `open`/`close` is still recommended for longer sessions (12min idle):', '**Optional resident mode.** The examples below apply only when deliberately using resident mode; batch jobs keep automatic resident startup disabled. Save/close and verify before external readers:')
        text = section(text, '## Specialized Skills', '''## Selected format methods

Use the selected officecli-docx, officecli-xlsx or officecli-pptx specialist for its format. Other upstream specialist names do not imply an installed skill or authority to install one.''')
    text = re.sub(r'(?m)^.*Before doc work, check Specialized Skills.*$', 'For format-specific work, read the selected native officecli-docx, officecli-xlsx or officecli-pptx entry when relevant. Runtime load_skill output is not an admitted specialist or installation authority.', text)
    text = re.sub(r'(?m)^.*`officecli load_skill <name>`.*$', 'Selected methods are the four reviewed native OfficeCLI entries; consult version-matched help for command schemas.', text)
    text = re.sub(r'(?m)^Example:.*officecli load_skill.*$', '', text)
    text = re.sub(r'(?m)^1\. \*\*Open/save lifecycle\.\*\*.*$', '1. **Choose lifecycle.** Nonresident edits are the batch default. If deliberately using resident mode, open the owned copy, then explicitly save/close and verify before an external reader. Use batch for repetitive operations and inspect each result.', text)
    text = re.sub(r'(?m)^\*\*Open/save lifecycle:\*\*.*$', '**Lifecycle:** Use nonresident batch edits by default. Only deliberately chosen resident mode needs open followed by explicit save/close before external readers. Use batch for repeated paragraph operations; inspect actual results.', text)
    text = re.sub(r'(?m)^1\. \*\*Open the file\.\*\*.*$', '1. **Create or inspect the owned copy.** Use create for a new file or view outline for an existing file. Open is optional resident mode, not a prerequisite.', text)
    text = re.sub(r'(?m)^officecli open ([^\n]+)$', r'# Optional resident mode only: officecli open \1', text)
    # Correct the particular cache guidance, not the surrounding editing method.
    if name == 'officecli-xlsx':
        replacements = {
            '**Zero formula errors.': '**Formula errors.** Diagnose unexpected errors; retain legitimate missing-data/error semantics rather than inserting blanket IFERROR.',
            '5. **Save, then reckon with the cache.': '5. **Save and independently recalculate.** ' + RECALC,
            '- [ ] **Cached value sanity on every summary cell.': '- [ ] **Cached value sanity on every summary cell.** ' + RECALC,
            '- [ ] Every `/` denominator is guarded': '- [ ] Check denominator/domain failures against the intended model; handle expected conditions explicitly without masking other errors.',
        }
        for prefix, replacement in replacements.items():
            pattern = r'(?m)^' + re.escape(prefix) + r'.*$'
            text, count = re.subn(pattern, lambda _: replacement, text)
            if count != 1: raise ValueError('OfficeCLI source correction anchor changed: ' + prefix)
        text = text.replace('"validate pass" is not delivery; "the preview looks like a real workbook" is delivery.', 'Use that preview to locate issues; verify the actual-file render and recalculated workbook before delivery.')
    text = re.sub(r'\*\*Fix-verify \(mandatory, max 3 cycles\)\.\*\*[^\n]+', '**Fix-verify.** Correct observed issues, rerun affected checks and inspect the actual-file render. Reconsider the cause if fixes fail to converge; report material unresolved limitations.', text)
    text = text.replace('Both are always safe (never error or lose work).', 'Check the actual save/close result before external readers.')
    text = text.replace('Always safe: never errors or loses work.', 'Check the actual save/close result.')
    text = text.replace('(Idle sessions auto-flush within seconds; `OFFICECLI_RESIDENT_FLUSH=each` makes every mutation flush before returning.)', 'Do not rely on idle autoflush as a delivery receipt; verify the on-disk artifact.')
    text = text.replace('zero issues on first inspection means you weren\'t looking hard enough.', 'report the actual issues found, including none.')
    text = text.replace('If you found zero issues on first inspection, you were not looking hard enough.', 'Report the actual issues found, including none.')
    # A fixed global temporary screenshot must not overwrite unrelated work.
    text = text.replace('/tmp/sheet.png', '"$OUTPUT_DIR/sheet.png"')
    start = text.index('\n# ')
    return text[:start] + '\n' + NATIVE + text[start:]

def materialize(source, out, s, c):
    src = source / s['source_path']; name = src.parent.name if src.parent != source else 'officecli'
    if not src.is_file(): raise ValueError('Selected OfficeCLI source leaf is absent')
    raw = src.read_bytes(); adapted = port(raw.decode(), name)
    archive = out / 'upstream' / 'SKILL.reference.txt'; archive.parent.mkdir(parents=True)
    archive.write_bytes(raw); (out/'SKILL.md').write_text(adapted)
    notices = []
    for parent in (src.parent, *src.parent.parents):
        if not parent.is_relative_to(source): break
        for pattern in ('LICENSE*', 'NOTICE*', 'COPYING*', 'THIRD-PARTY*', 'THIRD_PARTY*'):
            for file in parent.glob(pattern):
                if file.is_file() and file.name not in notices:
                    shutil.copy2(file, out/file.name); notices.append(file.name)
        if parent == source: break
    if not any(n.upper().startswith('LICENSE') for n in notices): raise ValueError('OfficeCLI license closure absent')
    diff = ''.join(difflib.unified_diff(raw.decode().splitlines(True), adapted.splitlines(True), fromfile=s['source_path'], tofile='SKILL.md'))
    (out/'ADAPTATION.patch').write_text(diff)
    (out/'SOURCE-ADAPTATION.json').write_text(json.dumps({'repository':s['source_repository'],'revision':s['revision'],'source_path':s['source_path'],'source_sha256':hashlib.sha256(raw).hexdigest(),'archive':'upstream/SKILL.reference.txt','active_path':'SKILL.md','active_sha256':hashlib.sha256(adapted.encode()).hexdigest(),'changes':'Native-first pinned runtime; no installer; source style defaults subordinate to brief; actual-file render/recalculation; specific unsafe cache/error guidance corrected. Domain methods retained.','diff':'ADAPTATION.patch'},sort_keys=True,indent=2)+'\n')
    return '.'
