"""P283 source-preserving game methods with closed support and native callbacks."""
import hashlib
import json
import os
import pathlib
import re

P=pathlib.Path
REPOSITORY='Donchitos/Claude-Code-Game-Studios'
REVISION='05ad7c8a5b8aa2aa86bbd3439ae7cf7295cac418'
ROLES=('art-director','technical-artist','ux-designer','creative-director')
SUPPORT=tuple('.claude/agents/'+name+'.md' for name in ROLES)+(
 '.claude/docs/technical-preferences.md','.claude/docs/templates/art-bible.md',
 '.claude/docs/director-gates/ad-art-bible.md','.claude/docs/director-gates/cd-playtest.md')
FRAMEWORK=tuple('.claude/docs/'+name+'.md' for name in
 ('director-gates','automation-modes','config-resolution','workflow-modes','effects-map'))
COMMANDS={
 'art-bible':'game-art-bible','asset-spec':'game-asset-spec','playtest-report':'game-playtest-report',
 'brainstorm':'establish the game concept from the current brief',
 'map-systems':'map the concept into the requested game systems',
 'setup-engine':'inspect the selected engine and its actual project constraints',
 'design-system':'document the requested game system',
 'review-all-gdds':'cross-check existing game-design documents',
 'consistency-check':'check existing designs against the art bible',
 'create-architecture':'document the requested architecture',
 'create-stories':'derive scoped implementation stories',
 'dev-story':'implement the already authorized story',
 'ux-design':'design the requested screen interaction',
 'asset-audit':'compare delivered assets against their specifications',
 'propagate-design-change':'trace the affected design references before changing them',
 'balance-check':'check the system balance with its actual rules and evidence',
 'bug-report':'record the reproducible defect in the existing issue/task record',
 'design-review':'review the changed design against the concept and constraints',
 'bug-triage':'reprioritize verified defects in the existing task record',
}

def change(text,old,new):
 if text.count(old)!=1:raise ValueError('Pinned game method anchor changed: '+old[:100])
 return text.replace(old,new)

def section(text,start,end,replacement):
 if text.count(start)!=1 or text.count(end)!=1:raise ValueError('Pinned game section changed: '+start)
 a=text.index(start);b=text.index(end,a+len(start));return text[:a]+replacement.rstrip()+'\n\n'+text[b:]

def body(text):
 return text.split('\n---\n',1)[1].lstrip() if text.startswith('---\n') else text

def native_scope():
 return '''## Native execution and inputs

Read [the native callbacks and support map](../../docs/native-execution.md) before applying this method. Named departments below are expertise packets, not registered agents. Read their retained role methods for the relevant stage; execute directly or use supported bounded native delegation only when useful and available. Keep the user's model, effort, authority and current project workflow. No fixed studio roster or fanout is installed.

The questions/options below are the source's collaborative decision packets. Resolve them from the user's brief and existing project evidence; ask only for a material missing fact or consequential creative choice. Existing artifact authority covers ordinary drafting, creation and revision, without repeated per-section/file-write confirmations. Record actual review coverage; direct work is not an independent review. No source gate, automatic framework stage, config hook or follow-up command grants additional authority.

Paths under design/, production/ and project.yaml describe the owning game's inputs or requested outputs, not files that should exist in this skill bundle. Reuse the game's equivalent documents or the supplied brief. Do not scaffold a studio project, copy its configs or create missing context as if it were observed. An absent art bible, concept, engine budget or actual playtest notes remains a specific input/coverage gap. This integration provides methods/templates, not an engine or player observations.

'''

def adapt_skill(text,name):
 # Remove the foreign host's executable config interpolation, not method prose.
 text=re.sub(r'(?m)^!`bash[^\n]+`\n\n','',body(text))
 text=re.sub(r'Resolved above — use as-is;.*?(?=\n# )','',text,flags=re.S)
 text=re.sub(r'See `\.claude/docs/director-gates\.md` for the full check pattern\..*?do not read it in the parent session\.','Read the applicable retained art-bible or player-experience review checklist when that review is in scope. Either the parent or a native reviewer can read it; no director controller or mandatory gate is required.',text,flags=re.S)
 text=re.sub(r'Every `AskUserQuestion` call follows `\.claude/docs/automation-modes\.md`\n\(collaborative asks always · guided major-only · autonomous logs and proceeds;\n`automation_always_ask` categories always prompt\)\.', 'Use native input only for material missing information or a consequential choice; reuse existing authority for routine creative and file operations.',text)
 if name=='art-bible':
  text=change(text,'Present the session context and ask two questions before authoring anything:','Resolve the following two framing questions from the brief; ask only for an answer that is materially missing:')
  text=change(text,'Use `AskUserQuestion` with two tabs:','The source decision packet has two parts:')
  text=change(text,'  This is the single biggest cost lever in this skill: every authored section\n  carries a specialist spawn, so authoring 9 sections where the tier requires 4\n  more than doubles the run for artifacts nothing downstream will check.','  Scope determines how much content is needed. Author only the requested sections; apply their complete domain methods without assuming a separate specialist call for each section.')
  text=section(text,"If the file does not exist, this is a fresh authoring session.", 'Extract performance budgets and the engine', '''If the file does not exist and this artifact is requested, create it from the retained art-bible template, preserving the nine numbered headings. Fill each completed section incrementally; reuse the existing task authority rather than asking for each write. For retrofit work, preserve complete sections and revise only the requested/incomplete ones.

''')
  text=change(text,'> "No game concept found. Run `/brainstorm` first — the art bible is authored after the game concept is approved."','> "No game concept or equivalent brief is available. Obtain the material player fantasy, intended experience and constraints before inventing a visual identity; do not install or invoke a missing studio command."')
  text=section(text,'> **Spawn policy for this phase.**','### Section 1: Visual Identity Statement', '''> **Review packet grouping.** Keep Section 1 foundational. Sections 2–4 share the same visual identity/pillars and should be reasoned about together, with three separately labeled outputs. This grouping does not require a fixed agent roster; apply the retained art-director method and record whether the work was direct or independently reviewed.

''')
  text=section(text,'**Review mode check** — apply before spawning AD-ART-BIBLE:','Pass: the art bible path', '''Choose actual review coverage from the user's requested depth and available native capabilities. Read the retained art-bible review checklist for completeness, internal consistency and production readiness. Apply it directly or give the unchanged review questions and actual artifact/context to a fresh native reviewer when independence is useful. If no independent review ran, say so; a skipped review is not a sign-off. No mandatory studio gate is installed.

''')
  text=change(text,'Handle verdict per standard rules in `director-gates.md`.','Record the actual review result and evidence using the native review mapping. Missing inputs are NOT ASSESSED, not approval.')
  text=section(text,'## Collaborative Protocol','## Recommended Next Steps', '''## Collaborative Protocol

Resolve the source's question/option packets from the brief, draft with the retained relevant expertise, check it, then write within existing authority. Preserve the incremental section structure and substantive disagreements. Resolve a hard engine constraint from actual evidence; ask only when a consequential product preference remains unresolved. Direct drafting is allowed and must not be presented as independent specialist review.

The art bible is a constraint document: it restricts future decisions in exchange for visual coherence. Every section should feel like it narrows the solution space productively.

---

''')
  text=text.replace('> **Always include** (`standard`/`full` only) `/create-architecture` and Stop here as options — these are always valid next steps once the art bible is complete.','Offer next actions only when they serve the actual requested scope; do not start architecture or another production phase automatically.')
 elif name=='asset-spec':
  text=section(text,'The effective mode is the one already resolved','**Mode behavior:**', '''Use an explicitly requested review depth or the owning project's existing setting. Otherwise choose proportionate coverage from actual complexity and constraints; no config resolver or framework default is required. `full`, `lean` and `solo` below describe available coverage, not a fixed team or model selection.

''')
  text=change(text,'Do NOT proceed to Phase 3 without user confirmation of the asset list.','Proceed when the requested scope and source-backed asset list are sufficient; ask only about a material unresolved list choice.')
  text=change(text,'Spawn specialist agents based on review mode. **Issue all `Agent` calls simultaneously — do not wait for one before starting the next.**','Read the retained art-director and technical-artist methods needed for the actual asset set. Use direct execution or bounded native workers for independent questions when useful; do not create a fixed parallel team.')
  text=section(text,'## Collaborative Protocol','## Recommended Next Steps', '''## Collaborative Protocol

Identify assets, resolve material choices, generate source-anchored specs, review actual constraints and persist within existing authority. Always anchor specs to the art bible. Preserve disagreements and their evidence; resolve known hard limits and ask only about consequential remaining product choices. Preserve stable IDs and update the owning manifest when the spec changes. No repeated file-write approval is required.

---

''')
 else:
  text=section(text,'**Review mode check** — apply before spawning CD-PLAYTEST:','Pass: the structured report content', '''Read the retained creative-director method and player-experience checklist when this review is useful. Apply the questions directly or send the actual report, hypothesis and design context to an available fresh native reviewer. Record actual coverage; do not fabricate an independent review or require a studio gate/model tier. A missing input is NOT ASSESSED.

''')
  text=change(text,'Ask: "May I write this playtest report to `production/qa/playtests/playtest-[date]-[tester].md`?"\n\nIf yes, write the file, creating the directory if needed.','Save the requested report to the owning project\'s chosen location within existing authority; `production/qa/playtests/playtest-[date]-[tester].md` is the source convention. Preserve any existing file and use the real session/build/tester identity.')
 # Explicit native callback vocabulary. The full prompts/fields remain intact.
 text=text.replace('**Agent delegation (MANDATORY)**','**Art-direction review packet**')
 text=text.replace('**Agent delegation**','**Review packet**')
 text=text.replace('Spawn `art-director` via `Agent`','Apply the `art-director` review packet')
 text=text.replace('spawn `art-director` via `Agent`','apply the `art-director` review packet')
 text=text.replace('spawn `creative-director` via `Agent`','apply the `creative-director` review packet')
 text=text.replace('Spawn\n`art-director` via `Agent`','Apply the `art-director` review packet')
 text=text.replace('Spawn `art-director` once','Apply the `art-director` method once')
 text=text.replace('Spawn in parallel:','Use these complementary review packets when needed:')
 text=text.replace('Full mode — spawn in parallel:','Full coverage — artistic and technical methods:')
 text=text.replace('Lean mode — spawn art-director only (skip technical-artist).','Lean coverage — apply art direction; disclose an unvalidated technical pass.')
 text=text.replace('Solo mode — skip both.','Direct coverage — no independent reviewer.')
 text=text.replace('via `Agent`','through the native execution mapping')
 text=text.replace('Use `AskUserQuestion`','Use the following optional native decision packet')
 text=text.replace('use `AskUserQuestion`','use native input for a material unresolved choice')
 text=text.replace('`AskUserQuestion`','native input for a material unresolved choice')
 text=text.replace('Write the approved section','Write the completed section')
 text=text.replace('After approval, ask: "May I write the spec to `design/assets/specs/[target-name]-assets.md`?"','Write the requested spec to the owning project\'s chosen file within existing authority; the source convention is `design/assets/specs/[target-name]-assets.md`.')
 text=text.replace('Ask: "May I update `design/assets/asset-manifest.md`?"','Update the owning asset manifest within existing scope, preserving unrelated rows.')
 text=text.replace('After user approval, ask: "May I write the entity inventory to `design/assets/entity-inventory.md`?"','Persist the resolved inventory to the owning project\'s chosen file within existing artifact authority; the source convention is `design/assets/entity-inventory.md`.')
 text=text.replace('next project-wide IDs. Show what changes, then ask "May I update\n`design/assets/specs/[target-name]-assets.md`?" instead of "May I write".','next project-wide IDs. Show what changes and apply only the scoped update within existing authority.')
 text=text.replace('- `full`: spawn both `art-director` and `technical-artist` in parallel','- `full`: apply both artistic and technical review methods; use bounded native workers when independent review is useful and available')
 text=text.replace('- `lean`: spawn `art-director` only — faster, skips technical constraint pass','- `lean`: apply the art-direction method and disclose the unvalidated technical pass')
 text=text.replace('Prompt: "Asset specs for **[target]** — [N] assets. Review complete?"','Prompt if a consequential choice remains: "Asset specs for **[target]** — [N] assets. Review complete?"')
 return text

def adapt_role(text):
 text=body(text)
 text=text.replace('Before proposing any design:','Before proposing design, resolve these questions from the brief and ask only for materially missing answers:')
 # Preserve the strategic/craft methods and examples; only the host write gate changes.
 text=re.sub(r'(?ms)^\d+\. \*\*Get approval before writing files:\*\*.*?(?=^#### |^### )','Write only within existing task authority, preserving current artifacts. Ask only for a material missing decision; no per-write approval ritual or orchestrator exception is needed.\n\n',text)
 text=text.replace('Update `production/session-state/active.md` after each section with:', 'Update the existing owning task record when a durable handoff needs:')
 text=text.replace('Ask "May I create [filepath] with the section skeleton?" (step 4\'s orchestrated-run exception applies) and, on "yes", create the target file with a skeleton (all section headers)','Create the requested target skeleton within existing authority, preserving any existing artifact (all section headers)')
 text=re.sub(r'Once decided, document the decision \(ADR, pillar update, vision doc\) — ask\n\s+"May I write this to \[filepath\]\?",.*?(?=\n   - Cascade the decision)', 'Once decided, document the scoped decision in the owning project\'s existing record within actual authority; preserve current artifacts.',text,flags=re.S)
 text=text.replace('`AskUserQuestion` is not in your `tools:` grant, so whoever called you presents\nyour decisions.','Use the supported native input interface only for a material unresolved decision.')
 if '## Gate Verdict Format' in text:
  end='### What This Agent Must NOT Do' if text.index('## Gate Verdict Format')<text.index('### What This Agent Must NOT Do') else '### Output Format'
  text=section(text,'## Gate Verdict Format',end,'''## Review result

Use the applicable retained review checklist and report the actual result with rationale and specific evidence. APPROVE/CONCERNS/REJECT describe artistic findings, not user authorization or an automatic framework gate. Missing or unreadable required context is NOT ASSESSED; identify it. An artifact that should exist for the requested scope but is missing is a finding. Do not require artifacts the brief does not call for, invent review coverage or choose a different model.

''')
 return '## Native role method\n\nThis is retained expertise, not a registered agent, memory hook or model/tool grant. Read the relevant responsibilities and craft/technical method below; use direct work or supported bounded native review within the owning task. Other department names describe responsibility boundaries, not installed dispatch targets.\n\n'+text

def materialize(source,out,s,c):
 source,out=P(source),P(out);receipt=json.loads((source/'.nstack-source.json').read_text())
 if receipt.get('repository')!=REPOSITORY or receipt.get('revision')!=REVISION or s['revision']!=REVISION:raise ValueError('Wrong pinned game source')
 entry=s['source_path'];name=P(entry).parent.name
 if name not in ('art-bible','asset-spec','playtest-report'):raise ValueError('Unreviewed game skill')
 files=[entry,*SUPPORT,*FRAMEWORK,'LICENSE'];raw={}
 for rel in files:
  p=source/rel
  if p.is_symlink() or not p.is_file():raise ValueError('Missing or linked game support: '+rel)
  data=p.read_bytes()
  if hashlib.sha256(data).hexdigest()!=receipt['files'].get(rel):raise ValueError('Pinned game support changed: '+rel)
  raw[rel]=data
 root=out/'source';native=root/'.claude/docs/native-execution.md';native.parent.mkdir(parents=True,exist_ok=True)
 active={}
 for rel in [entry,*SUPPORT]:
  text=raw[rel].decode()
  if rel==entry:
   text=adapt_skill(text,name)
   title_end=text.index('\n\n')+2;text=text[:title_end]+native_scope()+text[title_end:]
   description=re.search(r'(?m)^description:\s*(.+)$',raw[rel].decode())[1].strip().strip('"')
   description=description.replace(' Run before /map-systems.','')
   text='---\nname: '+s['native_name']+'\ndescription: '+json.dumps(description)+'\n---\n\n'+text
  elif rel.startswith('.claude/agents/'):text=adapt_role(text)
  elif '/director-gates/' in rel:
   text=re.sub(r'^> Gate definition\.[^\n]*\n\n','',text)
   text=re.sub(r'(?m)^Agent:.*$', 'Apply the retained role expertise with the actual native host/model. This is a review checklist, not an installed director gate.',text)
  text=text.replace('AD-ART-BIBLE','Art review').replace('CD-PLAYTEST','Player experience review')
  text=text.replace('/ux-design accessibility','establish the requested accessibility criteria')
  for command,replacement in COMMANDS.items():text=re.sub(r'(?<![\w/])/'+re.escape(command)+r'\b',lambda _:replacement,text)
  active[rel]=text
 # Replace source-support locators with real relative links; framework controls
 # route to native callbacks, while their exact originals remain archival.
 for rel,text in active.items():
  path=root/rel;path.parent.mkdir(parents=True,exist_ok=True)
  for ref in sorted(SUPPORT+FRAMEWORK,key=len,reverse=True):
   target=root/ref if ref in SUPPORT else native
   label=ref if ref in SUPPORT else 'native execution mapping'
   link='['+label+']('+os.path.relpath(target,path.parent)+')'
   text=text.replace('`'+ref+'`',link)
  text=text.replace('`director-gates.md`','[native review mapping]('+os.path.relpath(native,path.parent)+'#reviews)')
  text=text.replace('`technical-preferences.md`','[technical preference template]('+os.path.relpath(root/'.claude/docs/technical-preferences.md',path.parent)+')')
  path.write_text(text)
 native.write_text('''# Native game workflow mapping

## Configuration

Use the owning game's existing brief, art bible, engine/version, actual performance limits and selected review depth. project.yaml and design/production paths in the source are project conventions, not prerequisites to install a studio framework. Never execute the source's YAML helper, read another host's settings or populate defaults as if they were project facts. The retained technical-preference file is a blank template; unknown budgets remain unknown until the actual target supplies evidence.

Source full/standard/minimal and docs.density describe optional content/depth choices. Respect existing project choices; otherwise select the sections needed for the requested artifact. No framework mode or approval policy overrides the user's task authority.

## Reviews

Read the relevant retained art-director, technical-artist, UX or creative-director method for each needed packet. Use native direct work or bounded delegation when useful and available, with the user's model and effort. A source role name is not a callable agent ID. Independent review, direct application and unrun coverage must be labeled accurately. The art-bible and player-experience checklists retain the full source review questions and input requirements. APPROVE, CONCERNS, REJECT and NOT ASSESSED are findings, not authorization gates. Missing context is never fabricated approval.

## Host callback bindings

Source Read/Grep/Glob examples describe file operations, not unavailable tool APIs: use the current host's explicit file reads, `rg -n` for content and headings, and `rg --files -g` for scoped file discovery. Read(offset, limit) means inspect the needed line range. Use supported native editing/patch operations for Write/Edit while preserving existing bytes. Agent packets mean the retained role method plus actual supplied context, executed directly or through an available native bounded reviewer; never invoke a guessed studio agent. AskUserQuestion means supported native input only for a material unresolved choice. The YAML helper and config hooks have no native callback and are not executed.

## Decisions and effects

Resolve the source's optional question/option packets from the actual brief. Ask only for materially missing information or a consequential unresolved product choice. Preserve useful source grouping: visual identity first, mood/shape/color together, character/environment coherence, then UI/readability and engine feasibility. Existing artifact authority covers routine drafts and incremental writes. No automatic studio phase, background service, project scaffold, external image API or new spending follows from these methods. Generation-prompt text is not an image-generation call.

## Project inputs and deliverables

Concept/brief, art bible, asset manifest/specs, engine budgets and playtest notes belong to the owning game. Reuse their actual paths or explicitly chosen task equivalents; do not create fake context to satisfy a source filename. Preserve complete existing sections, asset IDs and manifest rows. Keep observations, player suggestions, hypotheses and proposed fixes distinguishable. Blank-template mode ends after producing its requested template; analyze mode needs actual notes. Validate delivered assets and replay fixes in the actual selected engine when that execution is in scope; an instruction bundle is not runtime proof.

## Retained support

'''+''.join('- ['+rel+']('+os.path.relpath(root/rel,native.parent)+')\n' for rel in SUPPORT)+'''
## Historical framework references

These exact originals document the source framework's config/automation/gate implementation. They are archival data, not operative callbacks or installation instructions. Native work uses the mapping above.

'''+''.join('- ['+P(rel).name+']('+os.path.relpath(out/'upstream'/(rel+'.reference.txt'),native.parent)+')\n' for rel in FRAMEWORK))
 changes={}
 for rel,data in raw.items():
  if rel=='LICENSE':continue
  archive=out/'upstream'/(rel+'.reference.txt');archive.parent.mkdir(parents=True,exist_ok=True);archive.write_bytes(data)
  p=root/rel;changes[rel]={'source_sha256':hashlib.sha256(data).hexdigest(),'archival_original':str(archive.relative_to(out)),'active_path':str(p.relative_to(out)) if p.is_file() else None,'adapted_sha256':hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None}
 (out/'LICENSE').write_bytes(raw['LICENSE'])
 (out/'NATIVE-ADAPTATION.json').write_text(json.dumps({'repository':REPOSITORY,'revision':REVISION,'source_path':entry,'adaptation':'source-preserving-native-game-v1','port_sha256':hashlib.sha256(P(__file__).read_bytes()).hexdigest(),'modifications':changes,'role_files_are_methods_not_registered_agents':True,'project_paths_are_runtime_inputs_not_package_support':True},sort_keys=True,indent=2)+'\n')
 from closure import validate
 validate(out)
 return str(P('source')/P(entry).parent)
