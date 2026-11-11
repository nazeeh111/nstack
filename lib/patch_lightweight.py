"""Source-anchored bounded Codex ports for selected lightweight procedures."""
import hashlib,json,pathlib,re,shutil
P=pathlib.Path

def replace(text,old,new):
 if old not in text:raise ValueError('Reviewed patch anchor missing: '+old[:80])
 return text.replace(old,new)

def patch(id,name,source,out):
 p=out/'SKILL.md';text=p.read_text()
 if id=='P007':
  text=replace(text,'Two complementary approaches — use both:', 'Choose measurements appropriate to the available target and claim. Use both approaches where field data is available and in scope:')
  text=replace(text,'Real user data in real conditions. Required to validate that a fix actually improved user experience.', 'Real user data in real conditions, when available and appropriate. Lab measurements support a lab-only claim; do not deploy telemetry merely to complete this task.')
  text=replace(text,'Profile first, identify the actual bottleneck, fix it, measure again.', 'Use profiling to identify the bottleneck, then time matched baseline and candidate runs without the profiler attached. Fix it and measure again under the same conditions.')
  text=replace(text,'Use two complementary layers when the surface is user-facing:', 'For a user-facing surface, use the applicable existing guards; field monitoring is conditional on available authorized data:')
  text=replace(text,'- **Field monitoring:** Alert on a meaningful p75 movement in RUM data. Use', '- **Field monitoring, when available and in scope:** Alert on a meaningful p75 movement in RUM data. Use')
  shared=source/'references/performance-checklist.md';target=out/'references/performance-checklist.md';shutil.copy2(shared,target)
  check=target.read_text();check=replace(check,'**Field data first** — check [CrUX Vis](https://developer.chrome.com/docs/crux/vis) or your RUM tool for real-user INP before optimising', '**Field data when available** — use existing authorized CrUX/RUM evidence for real-user claims. A lab-only target can be optimized and reported as a lab result; no new telemetry deployment is required.')
  target.write_text(check);text=text.replace('../../references/performance-checklist.md','references/performance-checklist.md')
 elif id=='P016':
  original=text
  marker=text.index('\n---\n',4)+5
  text=text[:marker]+'\n> Native acquisition binding: read [NATIVE-BINDINGS.md](NATIVE-BINDINGS.md).\n\n'+text[marker:]
  (out/'UPSTREAM_SKILL.md').write_text(original)
  (out/'NATIVE-BINDINGS.md').write_text("""# Native acquisition binding

Use this upstream discovery/install method for a concrete capability gap after
checking the native inventory. Keep its search terms, comparisons and fallback
methods. Before acquiring a result, review its actual source, pin, dependencies
and rights. Use the existing verified CLI or native source installer, not a
mutable bootstrap. Select the needed leaf and current host; a source example
with -g/-y does not override the user's installation scope or native permissions.
Report a failed search as failed, and carry an authorized acquisition through its
real representative task. Never install rejected/reference-only components or
activate a trial/substitute without its required evidence.
""")
 elif id=='P037':
  text=re.sub(r'(?m)^description:.*$', 'description: "Postgres-specific query, migration, row-security and performance guidance for a concrete database requirement or failure. Start routine changes with the project\'s existing checks; load only the rules relevant to this task."',text)
  folder=out/'references'
  changes={}
  for name in ('query-missing-indexes.md','security-rls-basics.md','monitor-explain-analyze.md'):
   q=folder/name;raw=q.read_bytes();t=raw.decode()
   if name=='query-missing-indexes.md':
    t=replace(t,'impactDescription: 100-1000x faster queries on large tables','impactDescription: Workload-dependent; compare actual plans and matched timings')
    t=replace(t,'Queries filtering or joining on unindexed columns cause full table scans, which become exponentially slower as tables grow.','An unindexed filter or join can require a sequential scan. Its cost depends on table size, selectivity and the actual plan; a sequential scan can be appropriate for small tables or queries returning much of a table.')
    t=replace(t,'**Incorrect (sequential scan on large table):**','**Before indexing (inspect the actual plan):**')
    t=replace(t,'**Correct (index scan):**','**Candidate index for a selective lookup:**')
    t=replace(t,'For JOIN columns, always index the foreign key side:','For JOIN columns, test an index on the referencing side when the actual join/delete/update workload benefits:')
    t=replace(t,'-- EXPLAIN shows:','-- Illustrative EXPLAIN output; verify on the target:')
    t+='\nCompare matched inputs, application role, cache state, row counts and latency before/after. Include index storage, write amplification and maintenance cost; the example plan costs are not measured speedups.\n'
   elif name=='security-rls-basics.md':
    t=replace(t,'Row Level Security (RLS) enforces data access at the database level, ensuring users only see their own data.','Row Level Security (RLS) enforces row policies at the database level. Correct identity, grants, policy combinations and role behavior determine whether users can see or change only their own rows.')
    start=t.index('**Correct (database-enforced RLS):**');end=t.index('Reference:',start)
    t=t[:start]+'''**Supabase example with a trusted authenticated identity:**

The gateway must validate the JWT issuer, audience, signature and expiry, and control the database role and claim settings. `auth.uid()` below is not authentication for arbitrary raw SQL callers. A client allowed to choose `app.current_user_id` or JWT claim settings can impersonate another identity; do not use a caller-issued `SET` as the authentication step.

```sql
-- Enable RLS on the table
alter table orders enable row level security;

-- The trusted gateway supplies auth.uid(); user_id is a UUID in this example.
create policy orders_user_policy on orders
  for all
  to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

-- Subject table owners to policies too; superusers/BYPASSRLS still bypass them.
alter table orders force row level security;

-- Run through the authenticated application entry point, not as a bypass role.
select * from orders;
```

For direct Postgres SQL access, use a trusted role/identity mapping that the caller cannot forge. Test the real application role and grants: own-row SELECT/INSERT/UPDATE/DELETE, another tenant's rows, attempted user_id changes, unauthenticated requests and bypass-role behavior. `USING` controls visible/existing rows; `WITH CHECK` controls new row values where applicable. Keep a caller-chosen-identity attempt as a negative test. Enabling or forcing RLS alone is not evidence that isolation passed.

'''+t[end:]
   else:
    t=replace(t,'EXPLAIN ANALYZE executes the query and shows actual timings, revealing the true performance bottlenecks.','Start with plain EXPLAIN to inspect the proposed plan. EXPLAIN ANALYZE executes the query and its functions and reports actual timings. Run mutating statements only in a disposable database or explicitly authorized target with suitable recovery; rollback does not undo every external effect or sequence increment.')
    t=replace(t,'**Correct (use EXPLAIN ANALYZE):**','''**Inspect the plan before executing the measurement:**

```sql
explain (format text)
select * from orders where customer_id = 123 and status = 'pending';
```

**For an eligible measurement, use EXPLAIN ANALYZE:**''')
    t=replace(t,'-- Output reveals the issue:','-- Illustrative output; inspect the actual target plan and timings:')
    t=replace(t,'-- Seq Scan on large tables = missing index','-- Seq Scan: inspect size, selectivity and alternatives; not proof of a missing index')
    t=replace(t,'-- Rows Removed by Filter = poor selectivity or missing index','-- Rows Removed by Filter: compare examined/returned rows and predicates with the workload')
    t=replace(t,'-- Buffers: read >> hit = data not cached, needs more memory','-- Buffers read >> hit: inspect I/O and cache/working-set conditions; not an automatic memory prescription')
    t=replace(t,'-- Nested Loop with high loops = consider different join strategy','-- Nested Loop with high loops: inspect actual/estimated cardinality and inner access path')
    t=replace(t,'-- Sort Method: external merge = work_mem too low','-- Sort Method: external merge indicates a spill; evaluate work_mem with concurrency and total memory')
    t+='\nCompare matched baseline/candidate inputs, application role, cache state, correctness and data distribution. Retain actual versus estimated rows, loops, buffers, elapsed time and repeated-run variance.\n'
   q.write_text(t)
   archive=out/'upstream/references'/(name+'.reference.txt');archive.parent.mkdir(parents=True,exist_ok=True);archive.write_bytes(raw)
   changes['references/'+name]={'source_sha256':hashlib.sha256(raw).hexdigest(),'adapted_sha256':hashlib.sha256(q.read_bytes()).hexdigest(),'archival_original':str(archive.relative_to(out))}
  (out/'NATIVE-ADAPTATION.json').write_text(json.dumps({'repository':'supabase/agent-skills','revision':'c9be0e931b7930f7d02126d04774d904c381e7d7','adaptation':'source-preserving-sql-method-v1','port_sha256':hashlib.sha256(P(__file__).read_bytes()).hexdigest(),'modifications':changes},sort_keys=True,indent=2)+'\n')
 elif id=='L010' and name=='frontend-design':
  start=text.index('Approach this as the design lead');end=text.index('\n## Ground',start)
  text=text[:start]+"Follow the actual brief, references, product identity and existing design system first. Choose intentional subject-specific art direction, typography and layout where the brief leaves a choice. No previous rejection, client history or commercial relationship is assumed.\n"+text[end:]
  start=text.index('If the brief does not identify');end=text.index('\n## Design principles',start)
  text=text[:start]+"If the subject is unspecified, infer a feasible subject, audience and primary job from the available context. Ask only when the missing purpose materially changes the result, while continuing independent work. Use supported preferences as context and build with real subject-specific content.\n"+text[end:]
  text=replace(text,'Avoid these default typographic treatments; they are the commonest tells of a generated page:', 'Treat these typographic treatments as choices to justify against the brief, not universal bans:')
  text=replace(text,"Where it leaves an axis free, don't spend that freedom on one of these defaults.", "Where it leaves an axis free, choose a direction that serves this subject. The examples are neither a required house style nor a prohibited palette or layout.")
 elif id=='L010' and name=='mcp-builder':
  text=text.replace('Use WebFetch to load','Use native documentation retrieval to fetch').replace('Use web search and WebFetch as needed.','Use native primary-source documentation retrieval as needed.')
  text=text.replace('the current stable release. Use it for new servers.','a versioned example family. Verify the actual target SDK release, schema and compatibility before choosing it for a new server.')
  start=text.index('If the project already uses v1, tell the user once,');end=text.index("\nDon't mix the two",start)
  text=text[:start]+"Respect the project's locked SDK and transport. A documentation example does not authorize a migration or an `@latest` codemod. Verify current official docs and choose a migration only for a separately requested or demonstrably required change.\n"+text[end:]
 else:raise ValueError('No reviewed lightweight patch for '+id+'/'+name)
 p.write_text(text)
