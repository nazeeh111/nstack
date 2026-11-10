"""Narrow dependency and evidence-checking ports."""
import pathlib,re
P=pathlib.Path

def change(text,old,new):
 if old not in text:raise ValueError('Missing data-check patch anchor: '+old[:70])
 return text.replace(old,new)

def patch(id,name,source,out):
 p=out/'SKILL.md';s=p.read_text()
 if id=='P183':
  s=re.sub(r'(?m)^description:.*$', 'description: Incrementally maintain a changing derived index with CocoIndex when insert/update/delete, transformation versions and durable ownership justify it. Use one explicit index target; ordinary parsing or one-off ETL stays native.',s)
  s=s.replace('cocoindex>=1.0.0','cocoindex @ git+https://github.com/cocoindex-io/cocoindex@d8e125a1787154fcaaab4680696d2ddc51d56ebb')
  s=change(s,'### Run the Pipeline','''### Ownership and runtime lock

Before running, resolve the pinned v1 source and its compatible connector dependencies to a hash lock in the project environment. Bind a durable private database path, the target table/index, stable record keys and a single publishing owner. Do not run against a shared table whose rows or deletion range belong to another writer. A relative ./cocoindex.db is illustrative; choose durable state before an ephemeral job. Test full rebuild versus incremental insert/update/delete, no-op refresh, crash/restart and transformation-version migration by stable key and digest on the actual target. Preserve the documented API and patterns references.

### Run the Pipeline''')
 elif id=='P195' and name=='property-based-testing':
  s=re.sub(r'(?m)^effort:.*\n','',s)
  s=change(s,'adding one is a dependency decision that belongs to the user — offer it once with the\nspecific property you would write, and take the answer either way.','follow the existing task authorization and project dependency policy. Reuse the current toolchain when adequate. Add a free dependency only when the specific property justifies it and authority permits; ask only if authority or a consequential dependency choice is missing.')
 elif id=='P195' and name=='fp-check':
  s=s.replace('a TRUE POSITIVE or FALSE POSITIVE verdict','a TRUE POSITIVE, FALSE POSITIVE or INCONCLUSIVE verdict')
  s=change(s,'1. **Counts**: X TRUE POSITIVES, Y FALSE POSITIVES','1. **Counts**: X TRUE POSITIVES, Y FALSE POSITIVES, Z INCONCLUSIVE')
  s=change(s,'3. **FALSE POSITIVE list**: Each with brief reason for rejection','3. **FALSE POSITIVE list**: Each with evidence that disproves the claim\n4. **INCONCLUSIVE list**: Missing execution, inaccessible specification, unknown trust boundary or insufficient provenance. State what would resolve it; do not force a binary verdict.')
  gate=out/'references/gate-reviews.md';g=gate.read_text();g=change(g,'- **FALSE POSITIVE**: Any gate review fails', '- **FALSE POSITIVE**: Evidence disproves a required exploitation condition')
  g=change(g,'If any phase fails verification, document the failure with evidence and continue all remaining phases. Issue the FALSE POSITIVE verdict only after all phases are complete.','If execution or specification is inaccessible or a gate remains unknown, return INCONCLUSIVE with the missing evidence. A tool failure or absent access is not a FALSE POSITIVE. Complete unaffected review and record material limits.');g+='\n- **INCONCLUSIVE**: A required fact remains unknown; identify the missing evidence and the smallest resolving check.\n';gate.write_text(g)
  for f in out.rglob('*.md'):
   t=f.read_text();prefix='./' if f.parent==out else '../';t=t.replace('{baseDir}/',prefix);f.write_text(t)
  s=s.replace('{baseDir}/','./')
 elif id=='P195' and name=='codeql':
  s=re.sub(r'(?m)^allowed-tools:.*\n','',s)
  s=s.replace('produce it, use the sarif-parsing skill.', 'produce it, use the bundled references/sarif-processing.md with native JSON tools.')
  file=out/'scripts/check_db_quality.py';t=file.read_text();t=change(t,'    loc = baseline_lines_of_code(database)','    if not is_finalised(database):\n        raise QualityFailure("Database is not explicitly finalised; incomplete extraction cannot be accepted.")\n\n    loc = baseline_lines_of_code(database)');file.write_text(t)
  start=s.index('**When multiple databases are found:**');end=s.index('\n',start)
  s=s[:start]+'''**Database identity gate:** Reuse only an exact current-source database matched by repository revision, language, build command/toolchain and extraction fingerprint, and passing finalized/source-file/LoC and nonempty suite checks. Rebuild when that identity is absent or stale. Do not select by recency alone. An unambiguous matching database or a clearly required rebuild does not need a user question. Ask only for a material unresolved target choice.'''+s[end:]
  s=re.sub(r'(?m)^.*\| One database found \|.*$', '| One database found | Verify exact source/build identity; reuse if matched, otherwise rebuild |',s)
  s=re.sub(r'(?m)^.*\| Multiple databases found \|.*$', '| Multiple databases found | Select the exact matching fingerprint; rebuild if none matches; ask only for genuinely ambiguous targets |',s)
  s=re.sub(r'(?m)^- \*\*"Just use the first database I find".*$', '- **Do not choose by order or age.** Verify exact revision/language/build fingerprint and extraction quality.',s)
  s=re.sub(r'(?m)^- \*\*"The user said.*$', '- **Existing scan authority persists.** Make unambiguous technical choices within scope; ask only for material missing target information.',s)
  start=s.index('### Database Selection Prompt');end=s.index('\n### ',start+5)
  s=s[:start]+'''### Database Selection

Use the identity gate above. An explicit caller target still requires source/build verification. Keep all valid extraction, data extension and explicit query-suite checks. For ambiguous targets, present only the decision that cannot be inferred from the source and request.
'''+s[end:]
  s=s.replace('{baseDir}/','./')
  start=s.index('### Building unattended');end=s.index('### Auto-Detection Logic',start)
  s=s[:start]+'''### Native build execution

Execute [build-database.md](workflows/build-database.md) with the actual CodeQL CLI and bundled scripts. Resolve resource paths against this skill directory, not the target repository or a previous shell. Use native task tracking when useful; no plugin slash command or named task tool is required. Preserve the build-method ladder, finalized/source-coverage quality guard, logs and supported failure states. Report missing tools or unresolved build constraints honestly; a failed build is not a clean scan.

'''+s[end:]
  # Workflows may still instruct asking for a DB; apply the same selection gate there.
  for f in (out/'workflows').glob('*.md'):
   t=f.read_text();t='> Select/rebuild by exact current source, language and build fingerprint. Ask only for a genuinely ambiguous target; use the patched finalized extraction guard.\n\n'+t;t=t.replace('{baseDir}/','../');f.write_text(t)
  # Port active support too: an adapted entry cannot repair a later foreign-tool gate.
  for f in out.rglob('*.md'):
   t=s if f==p else f.read_text()
   t=t.replace('AskUserQuestion','native user input for a material unresolved choice')
   if f.name=='run-analysis.md':
    t=t.replace('### Step 3: Confirm the Plan','### Step 3: Record the Scoped Plan')
    t=t.replace('**Exit:** User confirmed; flag arrays built', '**Exit:** Existing authority and scoped plan recorded; flag arrays built')
    t=t.replace('Present the whole plan in one `native user input for a material unresolved choice`, defaults filled in, and let the user\nchange any part before proceeding:', 'Record the plan using the stated target and exclusions. Resolve unambiguous settings from the source and task; ask through native user input only for a material choice that remains unresolved:')
    t=t.replace('Change anything, or say proceed.', 'Record any explicit user overrides; existing scan authority persists.')
    t=t.replace('Build the flags from the answer as arrays:', 'Build the flags from the resolved scope as arrays:')
   if f.name=='create-data-extensions.md':
    start=t.index('Present findings and use `native user input');end=t.index('\n---\n',start)
    t=t[:start]+'''Report source-backed model gaps. Within an authorized full-analysis or modeling task, create the required extension artifacts in the scoped output directory and preserve existing project models. Ask through native user input only when the modeling choice or authority is materially unresolved. Unknown API semantics remain unknown; do not invent a source/sink classification to complete the phase.
'''+t[end:]
    t=t.replace('Step 3 identified gaps and user confirmed which to model', 'Step 3 identified source-backed gaps within the resolved task scope')
    t=t.replace('the gaps confirmed by the user.', 'the source-backed gaps selected within the authorized scope.')
   if f==p:s=t
   else:f.write_text(t)
  from codeql_scope_port import patch as local_models
  local_models(out)
 else:raise ValueError('Unimplemented data-check leaf')
 p.write_text(s)
