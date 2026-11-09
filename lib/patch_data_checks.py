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
  # Workflows may still instruct asking for a DB; apply the same selection gate there.
  for f in (out/'workflows').glob('*.md'):
   t=f.read_text();t='> Select/rebuild by exact current source, language and build fingerprint. Ask only for a genuinely ambiguous target; use the patched finalized extraction guard.\n\n'+t;t=t.replace('{baseDir}/','../');f.write_text(t)
 else:raise ValueError('Unimplemented data-check leaf')
 p.write_text(s)
