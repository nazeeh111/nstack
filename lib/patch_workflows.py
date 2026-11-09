"""Exact source-anchored workflow and knowledge leaf ports."""
import pathlib,re,shutil
P=pathlib.Path

def change(text,old,new):
 if old not in text:raise ValueError('Reviewed source anchor missing: '+old[:100])
 return text.replace(old,new)

def propose(text):
 text=re.sub(r'\*\*Planning boundary\*\*:.*?(?=\n\n)', '**Authorization boundary**: Create planning artifacts first. Preserve the user\'s requested scope. A plan-only request stops after planning. When the user has explicitly authorized building or fixing this change, hand off to the selected apply workflow after the required artifacts are ready and continue implementation and verification in the same authorized task. Ask only for material missing information or an action outside that authority.',text,flags=re.S)
 text=change(text,'When the user is ready to implement, they must start the apply workflow explicitly.','When build authorization already exists, continue with the selected apply workflow. Otherwise present the planning artifacts and await implementation authority.')
 text=re.sub(r'(?m)^- Prompt:.*$', '- Handoff: for existing explicit build authorization, continue with the selected apply workflow and preserve the change name/store. For a plan-only request, present artifacts and stop.',text)
 text=re.sub(r'(?m)^- The request that invoked this workflow authorizes planning only\..*$', '- Planning and implementation are separate stages, but existing explicit build authority persists across them. A plan-only request stops here; a build request proceeds through apply and verification. Record skipped checks and bind spec scenarios to actual execution evidence.',text)
 return text

def patch(id,name,source,out):
 p=out/'SKILL.md';text=p.read_text()
 if id=='P008':
  text=propose(text)
  src=source/'src/core/templates/workflows/propose.ts';target=out/'templates/propose.ts';target.parent.mkdir();target.write_text(propose(src.read_text()))
  text+='\n\nThe pinned CLI workflow template has the same authorization patch in `templates/propose.ts`. Apply this file as an explicit source overlay when building the reviewed OpenSpec CLI; do not modify the immutable source cache. Keep apply/verify workflows intact. A file-existence or keyword traceability check is not proof of behavior.\n'
 elif id=='P011' and name=='json-canvas':
  text=change(text,'Unique 16-char hex identifier','Unique string identifier; preserve existing valid non-hex IDs')
  text=change(text,'Generate 16-character lowercase hexadecimal strings (64-bit random value):','For new objects, generate a unique string ID; 16-character lowercase hexadecimal strings are one convention. Preserve every existing valid string ID, including non-hex strings, and all edge endpoints. Never normalize IDs during an edit:')
  text=change(text,'2. Generate unique 16-character hex IDs for each node (e.g., `"6f0ad84f44ce9c17"`)','2. Generate unique string IDs for new nodes (for example, `"6f0ad84f44ce9c17"`); preserve existing valid IDs, including non-hex strings')
 elif id=='P011' and name=='obsidian-cli':
  text=change(text,'Without either, the active file is used.','The upstream default uses the active file; nstack requires an explicit target file/path for file operations. Do not depend on focus.')
  text=change(text,'Commands target the most recently focused vault by default. Use `vault=<name>` as the first parameter to target a specific vault:','The upstream default targets the most recently focused vault. Do not use that default: specify the user-authorized vault with `vault=<name>` as the first parameter:')
  text=change(text,'## Plugin development','## Plugin development\n\nDeveloper JS, eval, DOM, debugger and CDP commands are available only for an explicit plugin-debugging job. Ordinary note work uses file operations. Inspect the exact plugin and target first; a note request does not authorize app-context JavaScript.')
  # Make executable examples agree with the explicit-scope contract.
  text=re.sub(r'(?m)^obsidian (?!vault=|help)(.*)$',r'obsidian vault="My Vault" \1',text)
  text=change(text,'obsidian vault="My Vault" daily:read','obsidian vault="My Vault" read path="Daily/2026-01-01.md"')
  text=change(text,'obsidian vault="My Vault" daily:append content="- [ ] New task"','obsidian vault="My Vault" append path="Daily/2026-01-01.md" content="- [ ] New task"')
 elif id=='P013':
  text=change(text,'4. For production decks, run `pptx-reference-deck-analysis/scripts/validate_package.py` and save the JSON report.','4. Run the read-only `scripts/validate_package.py` with defusedxml for the applicable package checks; save its JSON report. It does not establish rendered quality.')
  text=change(text,'6. When a compatible renderer is already available, inspect previews for clipping, font fallback, contrast, crop, and hierarchy. Do not add a renderer dependency.','6. For a visual artifact, render the current successful PPTX and inspect every slide for clipping, font fallback, contrast, crop and hierarchy. Use an available free renderer or acquire a suitable free dependency within authority. If rendering is unavailable, report the visual gate as untested and do not claim visual acceptance. Scale the audit to the brief.')
  text=change(text,'Keep the spec, PPTX, build record, geometry audit, accessibility audit, package report, and source manifest together.','Keep the requested PPTX and the proportionate source, build and check evidence together. For production handoffs, use the pinned slide-specification reference; distinguish required audits from irrelevant checks.')
  scripts=out/'scripts';scripts.mkdir(exist_ok=True);shutil.copy2(source/'plugins/pptx-deck-creation/skills/pptx-reference-deck-analysis/scripts/validate_package.py',scripts/'validate_package.py')
  ref=out/'references/slide-specification';shutil.copytree(source/'plugins/pptx-deck-creation/skills/pptx-slide-specification',ref)
  # Reference material is not a second discoverable entry.
  (ref/'SKILL.md').rename(ref/'REFERENCE.md')
  text+='\nFor production slide handoffs, consult [the selected specification reference](references/slide-specification/REFERENCE.md).\n'
 else:raise ValueError('Unsupported workflow patch')
 p.write_text(text)
