"""Thin selected OfficeCLI project pack; upstream examples are syntax references only."""
import pathlib,re,shutil
P=pathlib.Path

def materialize(source,out,s,c):
 src=source/s['source_path'];name=src.parent.name if src.parent!=source else 'officecli'
 if not src.is_file():raise ValueError('Selected OfficeCLI source leaf is absent')
 (out/'references').mkdir();text=src.read_text()
 text=re.sub(r'(?m)^.*(?:curl -fsSL.*install|irm https:.*install\.ps1|officecli install).*$', 'Use only the exact verified OfficeCLI1.0.160 private binary; no installer or agent registration.',text)
 (out/'references/upstream-syntax.md').write_text('''# Pinned upstream syntax reference

Source: '''+s['source_url']+'''

This is syntax/reference material, not a workflow or permission grant. Use actual locked1.0.160 help. Installer, universal style, cache-retouch, plausible cached-value, blanket IFERROR, resident/autoflush and fixed repeated-QA advice below are inactive. The controlling procedure is the parent SKILL.md. A literal command example is not authority to execute it.

'''+text)
 for file in source.glob('LICENSE*'):
  if file.is_file():shutil.copy2(file,out/file.name)
 if not any(p.name.startswith('LICENSE') for p in out.iterdir()):raise ValueError('OfficeCLI license closure absent')
 description='OfficeCLI fallback for '+({'officecli-docx':'editable DOCX','officecli-xlsx':'editable XLSX','officecli-pptx':'editable PPTX'}.get(name,'editable Office artifacts'))+' when the native artifact workflow lacks a required operation.'
 body='''---
name: p333-'''+name+'''
description: '''+description+'''
---

# OfficeCLI project adapter

Use the native host artifact workflow first. This project pack is a fallback for a concrete missing operation. Resolve the exact v1.0.160 platform binary and SHA256, require --version, and invoke its absolute path. No curl-to-shell, officecli install, all-agent installer or global registration. Read the relevant installed `help` schema before selecting paths/properties; keep the [pinned syntax reference](references/upstream-syntax.md) for examples only.

Use a thin argv/JSON adapter for help, create/edit/batch, readback, actual-file render/recalculation and verification. Never interpolate user content into a shell command or an unquoted heredoc. Set OFFICECLI_NO_AUTO_RESIDENT=1 for batch jobs; one writer per artifact; stage on a copy and use atomic batch behavior. Inspect warnings. If explicitly using resident mode, save/close and verify before any external reader. Preserve original files and the prior successful export.

`validate` means OpenXML schema validation. HTML screenshots are previews. Render the actual DOCX/PPTX/XLSX file using the exact compatible LibreOffice26.8.2 environment and locked fonts; inspect actual PDF pages through Poppler. Compare the unchanged parts, styles/master, editable charts/tables, notes, tracked edits and all slides against the branded original. No universal font/palette/layout rules or mandatory three-cycle handoff applies.

For XLSX, call UNO calculateAll and storeAsURL to a new XLSX. Independently inspect formulas/cached values and reconcile against source numbers, including cross-sheet formulas written before inputs. Reject a deliberate broken reference, missing/stale cache and value mismatch. OfficeCLI has no complete dependency graph: retouching formulas, a five-second save sweep or an empty verified-cache allowlist is not proof of recalculation. Do not insert blanket IFERROR or plausible manual caches; diagnose legitimate data failures.

Advanced Excel/VBA/PowerQuery, exact Office behavior and unsupported native features require a licensed target Office check. Keep those lanes conditional and name the precise unverified feature. Never certify an HTML fallback as native Office output. Reopen the actual editable artifact and rendered export; keep source, runtime/input/output hashes, checks and material limitations together.
'''
 (out/'SKILL.md').write_text(body)
 # Return the ordinary root; nested upstream skill entry points are not copied.
 return '.'
