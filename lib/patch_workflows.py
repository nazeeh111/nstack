"""Exact source-anchored workflow and knowledge leaf ports."""
import pathlib,re,shutil
P=pathlib.Path

def change(text,old,new):
 if old not in text:raise ValueError('Reviewed source anchor missing: '+old[:100])
 return text.replace(old,new)

def patch(id,name,source,out):
 p=out/'SKILL.md';text=p.read_text()
 if id=='P008':
  src=source/'src/core/templates/workflows/propose.ts';target=out/'templates/propose.ts';target.parent.mkdir();target.write_bytes(src.read_bytes())
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
  scripts=out/'scripts';scripts.mkdir(exist_ok=True);shutil.copy2(source/'plugins/pptx-deck-creation/skills/pptx-reference-deck-analysis/scripts/validate_package.py',scripts/'validate_package.py')
  ref=out/'references/slide-specification';shutil.copytree(source/'plugins/pptx-deck-creation/skills/pptx-slide-specification',ref)
  # Reference material is not a second discoverable entry.
  (ref/'SKILL.md').rename(ref/'REFERENCE.md')
  text+='\nFor production slide handoffs, consult [the selected specification reference](references/slide-specification/REFERENCE.md).\n'
 else:raise ValueError('Unsupported workflow patch')
 p.write_text(text)
