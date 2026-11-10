"""Dormant self-optimization and exact Eve project instruction ports."""
import pathlib,re,json
P=pathlib.Path

def patch(id,out):
 p=out/'SKILL.md';s=p.read_text()
 if id=='X-AUTO-EVE':
  bootstrap = ('If `eve` is not installed yet, install it (`npm install eve`) or scaffold a new\n'
               'agent with `npx eve init <agent-name>`, then read the bundled docs.')
  if s.count(bootstrap) != 1 or s.count('## Source of truth\n') != 1:
   raise ValueError('Pinned Eve bootstrap/source-of-truth shape changed')
  s, count = re.subn(r'(?m)^description:.*$', 'description: Develop an existing Eve product project or a requested always-on user-facing agent needing durable sessions, channels and suspendable human/tool interactions. Not a Codex/OpenCode workflow router.', s, count=1)
  if count != 1:
   raise ValueError('Pinned Eve skill description is missing')
  s=s.replace('## Source of truth\n', '''## Activation and project scope

This globally discoverable entry does not activate a runtime. Keep Eve
dependencies, project guidance and version-matched docs inside the owning
project. Do not overlay Eve on Codex, OpenCode or 01.

## Source of truth
''')
  s=s.replace(bootstrap, '''## Project commissioning

Inspect the owning project's Eve version, lock and Node runtime. Treat a
different version as a migration. If absent, commission the selected runtime
there or in disposable staging under the artifact/dependency-lock gate below.
An exact direct version is not a full lock.

Install from the reviewed lock and use the verified local CLI. Its `init`
installs dependencies and may modify a containing workspace; inspect that scope
and review resulting locks. Reconcile generated guidance with the selected
version and existing authority.''')
  s+='''\n## Immutable world and effect ownership

The reviewed source declares eve1.0.0-rc.4 and Node>=24. Commission a compatible exact artifact/dependency integrity lock and verify its installed version/docs before invoking it; no @latest or mutable scaffold. Use one locked runtime per self-hosted world and a durable local volume for one instance, or a supported Postgres world for replicas. Keep provider/API or service access conditional on an already authorized free/subscription route; this skill grants no paid API, cloud service or new credentials.

Coordinate version upgrades and drain/run handoffs, preserving rollback and accepted sessions before retiring the old world. Key inbound event deliveries separately from external business effects. Bind callback origin/audience and account/payload authorization; protocol3 keyed follow-ups and protocol2 guarantees differ. An unreadable accepted receipt is unknown: reconcile authoritative remote state before retry. Keep project-specific Eve guidance local to its owning project; the global entry remains a discovery adapter. Do not start a service merely because the source was staged.
'''
 elif id=='L036':
  s=re.sub(r'(?m)^description:.*$', 'description: Explicit bounded SkillOpt-Sleep trial on disposable Codex transcripts and an absolute selected skill target. Stages a proposal only; no global memory evolution, auto-adoption or automatic schedule.',s)
  s=s.replace('explicit adoption or a user-requested `--auto-adopt`','explicit reviewed adoption after independently rerun acceptance; auto-adopt stays off')
  s=s.replace('7. **Adopt** - explicitly, or through user-requested auto-adopt, copy staged','7. **Adopt** - only after independent representative regressions, explicitly copy staged')
  s=s.replace('TARGET_SKILL=.agents/skills/example/SKILL.md','TARGET_SKILL="$PWD/.agents/skills/example/SKILL.md"  # absolute disposable target')
  s=s.replace('| `--auto-adopt` | Auto-adopt if the gate passes (default: stage only) |','| `--auto-adopt` | Disabled for this trial; stage only |')
  s=re.sub(r'(?m)^.*if `--auto-adopt` was explicitly supplied.*$', '   Keep auto-adopt off and report a staged proposal; independent representative regressions are required before any separate adoption.',s)
  s+='''\n## Mandatory trial boundary

This is conditional, not a foundation workflow. Set transcript_source=codex, an explicit absolute target_skill_path, evolve_memory=false, gate_mode=on, gate_metric=hard and gate_no_regression=true; auto_adopt=false. Use the isolated trial runner's explicit configuration overrides, never change the real user's ~/.skillopt-sleep configuration as incidental setup. Do not harvest private native transcripts merely to prove installation; synthetic task fixtures are sufficient for plumbing.

Run in a disposable OS-sandboxed checkout. Keep evaluator/oracle and credentials outside every writable surface; enforce external time/token/process caps. Verify the boundary with a negative write attempt before a real trial. A mock dry-run proves plumbing only. A staged proposal becomes eligible for explicit adoption only after independently rerunning representative regressions and no-regression checks. Preserve the exact baseline and rollback; no scheduler or background job is installed by this leaf.
'''
  (out/'nstack-required-config.json').write_text(json.dumps({'transcript_source':'codex','target_skill_path':'REQUIRED_ABSOLUTE_DISPOSABLE_TARGET','evolve_memory':False,'gate_mode':'on','gate_metric':'hard','gate_no_regression':True,'auto_adopt':False},indent=2)+'\n')
 else:raise ValueError('Conditional leaf is not mapped')
 p.write_text(s)
