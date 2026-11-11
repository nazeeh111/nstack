"""Scoped browser, extraction, CLI builder and native UI ports."""
import pathlib,re,shutil
P=pathlib.Path

def change(s,old,new):
 if old not in s:raise ValueError('Missing interface patch anchor: '+old[:80])
 return s.replace(old,new)

def patch(id,name,source,out):
 p=out/'SKILL.md';s=p.read_text()
 if id=='P028':
  s=change(s,'Companion to `how` and `why`. `how` tells you what the code does. `why` tells you why it\'s shaped that way. Blast radius tells you what it breaks somewhere else.','Use ordinary local source, diff and history to explain behavior, design rationale and what a change could break elsewhere. No companion command or harness is required.')
  s=change(s,'Use `why` step 2 to pull the PR and commits.','Read the actual local diff and relevant Git history; fetch a PR only when needed and authorized.')
  s=change(s,'Same rules as `why`.','Use the actual source and observed runtime evidence.')
 elif id=='P062':
  s=re.sub(r'(?m)^description:.*$', 'description: Structured extraction from authorized web sources when a parser or crawler is needed beyond native browsing. Validate record identity, type, units, labels, cardinality and provenance; adaptive matches are hypotheses.',s)
  s=change(s,'`pip install "scrapling[all]>=0.5.1"`','Use a private environment built from the reviewed source commit. Resolve compatible platform dependencies to a hash lock at commissioning; do not run an unbounded `>=` installation or overwrite a shared Python environment.')
  s=change(s,'Press Ctrl+C to pause gracefully - pending requests and seen URLs are saved automatically. Later, when you start the spider again, pass the same `crawldir`, and it will resume from where it stopped.','Press Ctrl+C to pause gracefully. Before an explicit resume, apply the checkpoint gate below. Passing the same directory alone does not establish trustworthy state.')
  s=change(s,"This skill includes guides and examples from the documentation in Markdown, so don't check external sources or search online without the user's permission.",'Use the pinned local guides first. Verify current owning documentation when needed; ordinary read-only research does not require repeated permission.')
  s=change(s,'## Guardrails (Always)', '''## Checkpoint and field gate

Before any pickle is opened, require a trusted process-owned private non-symlink checkpoint directory, no shared writers, and a single writer lock. Bind the run ID, exact source/leaf/runtime lock, schema and checkpoint hash in a trusted manifest outside the fetched page. A moved checkpoint requires authenticated provenance, not a colocated unauthenticated checksum. Never unpickle page-supplied or arbitrary external data. Abort an explicit resume if its expected file is missing, corrupt, wrong-run or wrong-schema, or if the upstream loader returns None. Quarantine it and reconcile already persisted output before a separately authorized new run.

An adaptive selector is not semantic identity. Validate record ID, expected type, unit, label, cardinality, registered domain and source provenance against the requested schema. Abstain and quarantine ambiguous rows, including deceptive siblings and changed labels. Follow only authorized domains/links. Persist rows with stable record keys in an idempotent store; replay after a crash must not duplicate effects. Test altered DOM labels, a different domain, old run identity and a half-completed crawl before relying on resume for that task.

## Guardrails (Always)''')
 elif id=='P064':
  original=source/'cli-anything-plugin'
  if not (original/'HARNESS.md').is_file():raise ValueError('Pinned CLI-Anything methodology closure missing')
  refs=out/'references';refs.mkdir(exist_ok=True)
  for name in ['HARNESS.md','LICENSE','commands','guides']:
   src=original/name;dst=refs/name
   if src.is_dir():shutil.copytree(src,dst)
   else:shutil.copy2(src,dst)
  scripts=out/'scripts'
  for name in ['repl_skin.py','preview_bundle.py','skill_generator.py']:
   shutil.copy2(original/name,scripts/name)
  shutil.copytree(original/'templates',scripts/'templates')
  (refs/'docs').mkdir();shutil.copy2(source/'docs/PREVIEW_PROTOCOL.md',refs/'docs/PREVIEW_PROTOCOL.md')
  for f in refs.rglob('*.md'):
   t=f.read_text();t=t.replace('../../docs/PREVIEW_PROTOCOL.md','../docs/PREVIEW_PROTOCOL.md')
   f.write_text(t)
  s=change(s,'5. If neither local source is available, clone or download\n   `https://github.com/HKUDS/CLI-Anything` and use `cli-anything-plugin/HARNESS.md`.','5. If neither local source is available, fetch only the registry-pinned CLI-Anything commit and its methodology closure; do not silently use the default branch.')
  s=change(s,'test documentation, CLI-specific `SKILL.md` generation, and local installation.','test documentation, CLI-specific `SKILL.md` generation, and installation into an isolated project environment. Fit package layout to project conventions; publish or install globally only when specifically authorized.')
 elif id=='P066':
  from patch_agent_browser import patch_stub,patch_core
  if name=='core':patch_core(out)
  elif name=='agent-browser':patch_stub(out)
  else:raise ValueError('Unreviewed agent-browser leaf')
  return
 elif id=='P068':
  s=re.sub(r'(?m)^description:.*$', 'description: Native GUI fallback for an explicit task whose required operation is unavailable through supported native tools or APIs. Use a preauthorized host with installed cua-driver; retain snapshot-bound tokens, exact window targets and capture identity.',s)
  s=change(s,"The one exception is Cua Driver's own macOS Accessibility and Screen Recording prompts, which you may approve only on a host whose owner explicitly authorized that in this task, by the steps and guardrails in [MACOS.md](MACOS.md#install-and-approve-permissions).",'There is no automatic-approval exception for driver access prompts. Use a preauthorized host; any missing OS access is granted by the user or trusted host operator through its native permission flow. Honor denials and do not switch tools to evade them.')
  mac=out/'MACOS.md';t=mac.read_text()
  start=t.index('### Install or update');end=t.index('### Keep permissions')
  t=t[:start]+'''### Install or update

Use the registry-pinned source and a compatible immutable platform build with a verified checksum. Do not run an online latest updater or unreviewed curl-to-shell installer. Installation authority does not grant OS access. Use a preauthorized host; otherwise the user or trusted operator performs the native grant flow. Never automate a permission dialog through VNC, another driver or another tool. Existing denials remain controlling.

### Grant permissions

The user or trusted operator can run the installed driver's native permission flow and grant only the required access. Verify afterward with `cua-driver permissions status --json`. When access is absent, continue only through independently authorized supported operations. Do not claim a GUI check passed without the required observation.

'''+t[end:]
  t=re.sub(r'approve it yourself only when the owner authorized that for this task, otherwise tell the user to grant it in System Settings','ask the user or trusted operator to grant it through the native permission flow',t)
  mac.write_text(t)
  s+='\nEnd only the session owned by this task. A fresh snapshot invalidates old element tokens; bind screenshot-coordinate actions to the exact required capture identity. Refresh stale targets and reconcile uncertain external delivery through authoritative readback before retry.\n'
 elif id=='P083':
  s=change(s,'gws auth login\n','gws auth login -s drive,gmail,sheets  # example only: request only services this task needs\n')
  s=change(s,'- **Always** confirm with user before executing write/delete commands','- Execute writes/deletes only within specific existing user authority. Inspect the exact method with `gws schema`; use --dry-run for complex writes and validate the target ID/payload before authorized execution. Ask only for missing authority.')
  s+='\nUse the native connected service first. Load only this shared reference and the relevant service leaf for a CLI gap; never install the persona/recipe collection globally. Do not choose the recommended broad OAuth scope preset on an unverified app. A successful dry-run is local validation, not proof of a remote write; inspect authorized readback. Credential content stays in the native authentication mechanism.\n'
 else:raise ValueError('Unreviewed interface patch')
 p.write_text(s)
