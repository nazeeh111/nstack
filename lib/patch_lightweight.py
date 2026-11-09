"""Source-anchored bounded Codex ports for selected lightweight procedures."""
import pathlib,re,shutil
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
  text='''---
name: find-skills
description: Recover a missing specialist name or capability after native tools and the reviewed nstack inventory give a weak hit. Uses read-only keyword/owner/source discovery and evidence comparison; does not install or update globally.
---
# Capability discovery after a name gap

Start with the requested artifact, operation, physical quantity and failure condition. Search admitted components with `nstack search TERMS`. On a weak hit, split the objective into quantity, deliverable and effect; try ordinary words and domain equivalents, normalize spaces/hyphens/underscores, then use `nstack search --all TERMS`. Search original descriptions, acceptance checks and exact leaf names, not just component titles. Rejoin each hit by ID to its deployment decision: a term match can be excluded, consult-only, trial or substitute.

Compare the best eligible route with native/project tools and the strongest incumbent before adding anything. Inspect the exact leaf and its owning repository, stable commit, license, required references/helpers, activation/non-use rule and a representative acceptance test. Install counts, stars, leaderboard position and publisher fame do not establish fit or quality.

If the reviewed inventory cannot meet the concrete objective, use read-only keyword or owner search at https://skills.sh/ or https://agenticskills.io/ and open the original public source. Record the actual response state. A successful empty response concerns that query; an HTTP/transport failure is an outage, not proof that no skill exists. Direct public source inspection is a valid fallback. If an optional pinned search CLI is separately used, set `DO_NOT_TRACK=1`; no CLI installer is needed for this procedure.

Record a scoped proposal containing exact source/leaf, rights, pin, incumbent comparison, representative task, negative control, target environment and removal/rollback path. A project-specific addition needs source review and the user's existing authority. It does not rewrite the immutable release registry, install a whole collection, enable itself globally or update other installed skills. During initial nstack installation, the supplied selections remain authoritative. There is no global `-g -y` install or update-all step.

If no eligible route exists, report the actual evidence gap and continue useful native work that remains within scope. Preserve a reusable source-backed correction with its boundary and source locator when it improves future discovery.
'''
 elif id=='P037':
  text=re.sub(r'(?m)^description:.*$', 'description: "Postgres-specific query, migration, row-security and performance guidance for a concrete database requirement or failure. Start routine changes with the project\'s existing checks; load only the rules relevant to this task."',text)
  folder=out/'references'
  q=folder/'query-missing-indexes.md';q.write_text('''---
title: Evaluate indexes against the actual query and workload
impact: Workload-dependent
impactDescription: Requires actual plans, selectivity, write cost and matched timings
---
# Index decisions from evidence

A sequential scan can be appropriate for a small table or a low-selectivity filter. Missing indexes do not imply exponential growth or a universal speed multiplier. Inspect a plain EXPLAIN plan, predicates, joins, cardinality estimates, selectivity, stable ordering, table size, cache state and existing indexes before changing the schema.

For a demonstrated selective lookup, test an index in a disposable or authorized environment, compare actual plans and matched latency, and include write amplification, storage and maintenance cost. Foreign-key-side indexes can help particular joins, deletes or updates; they are not universally mandatory. Keep an index only where the workload evidence and correctness justify it. Use bound parameters and the actual application role when verifying results.
''')
  q=folder/'security-rls-basics.md';q.write_text('''---
title: Row security depends on authenticated identity and trusted connection roles
impact: CRITICAL
impactDescription: Verify actual application-role read/write isolation
---
# Authenticated identity before row policy

RLS complements permissions; it does not authenticate an arbitrary caller. A raw SQL client with SET privileges can choose its custom `app.current_user_id` or claim settings. Never treat a client-chosen tenant value as authenticated identity. Identify who validates issuer, audience, signature and expiry, who owns the connection role, and whether clients can run arbitrary SQL or alter settings.

Behind a trusted gateway that validates JWTs and controls SQL/settings, the provider's authenticated user identity can supply a policy. Direct SQL requires a trusted role/identity mapping or another mechanism clients cannot forge. A service role, table owner, superuser or BYPASSRLS identity is not a representative application user. Enabling or forcing RLS is not proof of isolation.

On the actual target, apply both `USING` and `WITH CHECK` where the command and policy require them. Verify own-row SELECT/INSERT/UPDATE/DELETE, foreign-tenant denial, attempted tenant/owner changes, unauthenticated access and bypass-role behavior. Exercise the real public entry point with issuer-validated identities. Check grants, policy combinations and SECURITY DEFINER/search_path behavior. Keep the untrusted-SET counterexample as a failing control; never reproduce it as a secure authentication recipe.
''')
  q=folder/'monitor-explain-analyze.md';q.write_text('''---
title: Inspect plain EXPLAIN before execution measurements
impact: Workload-dependent
impactDescription: ANALYZE executes the statement, including mutations
---
# Plans and actual execution

Start with plain `EXPLAIN` to inspect the proposed plan. `EXPLAIN ANALYZE` executes the statement and its functions. Measure mutating statements only in a disposable database or an explicitly authorized target with suitable recovery. A transaction rollback does not undo every external effect, trigger action or sequence increment.

For an eligible read-only measurement, compare matched baseline/candidate inputs, role, cache state, data distribution, concurrency and correctness. Record actual rows versus estimates, loops, buffers, elapsed time and variance. A sequential scan is not automatically a missing index; high buffer reads are not automatically a need for more memory. Preserve the plan and actual application-role results, and validate any proposed change against the relevant workload.
''')
 elif id=='L010' and name=='frontend-design':
  start=text.index('Approach this as the design lead');end=text.index('\n## Ground',start)
  text=text[:start]+"Follow the actual brief, references, product identity and existing design system first. Choose intentional subject-specific art direction, typography and layout where the brief leaves a choice. No previous rejection, client history or commercial relationship is assumed.\n"+text[end:]
  start=text.index('If the brief does not identify');end=text.index('\n## Design principles',start)
  text=text[:start]+"If the subject is unspecified, infer a feasible subject, audience and primary job from the available context. Ask only when the missing purpose materially changes the result, while continuing independent work. Use supported preferences as context and build with real subject-specific content.\n"+text[end:]
  text=replace(text,'Avoid these default typographic treatments; they are the commonest tells of a generated page:', 'Treat these typographic treatments as choices to justify against the brief, not universal bans:')
  text=replace(text,"Where it leaves an axis free, don't spend that freedom on one of these defaults.", "Where it leaves an axis free, choose a direction that serves this subject. The examples are neither a required house style nor a prohibited palette or layout.")
 elif id=='L010' and name=='mcp-builder':
  text=text.replace('Use WebFetch to load','Use native documentation retrieval to fetch').replace('Use web search and WebFetch as needed.','Use native primary-source documentation retrieval as needed.')
  text=text.replace('When uncertain, prioritize comprehensive API coverage.','Choose the least set of operations that serves the concrete workflow; expand API coverage only where it earns its complexity and access scope.').replace('Prioritize comprehensive API coverage. List endpoints to implement, starting with the most common operations.','Choose the operations and minimum read/write scopes for the concrete objective, with explicit authorization and error cases.')
  text=text.replace('the current stable release. Use it for new servers.','a versioned example family. Verify the actual target SDK release, schema and compatibility before choosing it for a new server.')
  start=text.index('If the project already uses v1, tell the user once,');end=text.index("\nDon't mix the two",start)
  text=text[:start]+"Respect the project's locked SDK and transport. A documentation example does not authorize a migration or an `@latest` codemod. Verify current official docs and choose a migration only for a separately requested or demonstrably required change.\n"+text[end:]
  text=text.replace('#### 4.2 Create 10 Evaluation Questions','#### 4.2 Choose discriminating evaluation questions').replace('create comprehensive evaluations to test its effectiveness.','choose evaluations proportionate to the server\'s behavior and access risks.')
  text += '\n\n## Target protocol acceptance\n\nPin the SDK and transport to the actual target. Exercise initialize, tools/list and tools/call through a real client/transport, including valid authentication, missing/invalid/expired identity, authorization denial, malformed input, actionable errors and pagination. Read-only/destructive annotations describe intent and are not enforcement. Keep write credentials out of read-only workers. A compile, schema or inventory listing alone does not establish protocol or authorization behavior.\n'
 else:raise ValueError('No reviewed lightweight patch for '+id+'/'+name)
 p.write_text(text)
