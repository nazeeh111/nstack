"""Dormant self-optimization and exact Eve project instruction ports."""
import pathlib,re,json
P=pathlib.Path

def patch(id,out):
 p=out/'SKILL.md';s=p.read_text()
 if id=='X-AUTO-EVE':
  s=s.replace('npm install eve','npm install --save-exact eve@1.0.0-rc.4').replace('npx eve init','npx --yes eve@1.0.0-rc.4 init')
  s+='''\n## Immutable world and effect ownership

The reviewed source declares eve1.0.0-rc.4 and Node>=24. Commission a compatible exact artifact/dependency integrity lock and verify its installed version/docs before invoking it; no @latest or mutable scaffold. Use one locked runtime per self-hosted world and a durable local volume for one instance, or a supported Postgres world for replicas. Keep provider/API or service access conditional on an already authorized free/subscription route; this skill grants no paid API, cloud service or new credentials.

Coordinate version upgrades and drain/run handoffs, preserving rollback and accepted sessions before retiring the old world. Key inbound event deliveries separately from external business effects. Bind callback origin/audience and account/payload authorization; protocol3 keyed follow-ups and protocol2 guarantees differ. An unreadable accepted receipt is unknown: reconcile authoritative remote state before retry. Keep this leaf local to the owning Eve project, and do not start a service merely because the source was staged.
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
