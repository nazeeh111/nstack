"""Native ports for the explicit 3.4 selections; retain substantive source bodies."""
import hashlib,json,os,pathlib,re,shutil
P=pathlib.Path
FULL={'P006','P021','P028','P032','P056','P111','P121','P283','P335','L013','P224','P092','P401'}
INSTALLABLE={'intact upstream leaf','narrow-patched leaf','native runtime/method adapter'}
def adapter(s):return s['delivery'] in INSTALLABLE and P(s['source_path']).name!='SKILL.md'
def handles(s):return s['candidate_id'] in FULL or adapter(s)
def entry(s):
 return str(P('native')/s['native_name']) if adapter(s) else str(P('source')/P(s['source_path']).parent)
def front(text,name,description=None):
 descriptions={
  'p092-trigger-authoring-tasks':'Author Trigger.dev TypeScript background jobs with durable waits, bounded retries, queues, idempotency and cancellation when an application needs that runtime.',
  'p092-trigger-cost-savings':'Audit Trigger.dev background-job costs, machine sizing, retries, concurrency and schedules from source and already authorized run data.',
  'l013-finance-comps-analysis':'Build comparable-company valuation spreadsheets with justified peer selection, consistent financial periods, valuation multiples and audited formulas.',
 }
 description=descriptions.get(name,description)
 body=text
 if text.startswith('---\n') and '\n---\n' in text[4:]:
  metadata,body=text[4:].split('\n---\n',1)
  if re.search(r'(?m)^name:',metadata):metadata=re.sub(r'(?m)^name:.*$', 'name: '+name,metadata,count=1)
  else:metadata='name: '+name+'\n'+metadata
  if description is not None:
   # Change only an explicitly supplied description, including its folded YAML
   # continuation. Retain every other upstream metadata field verbatim.
   lines=metadata.splitlines(keepends=True);start=next((i for i,line in enumerate(lines)if line.startswith('description:')),None)
   replacement='description: '+json.dumps(description,ensure_ascii=False)+'\n'
   if start is None:metadata=metadata.rstrip('\n')+'\n'+replacement.rstrip('\n')
   else:
    end=start+1
    while end<len(lines)and(lines[end][:1].isspace()or not lines[end].strip()):end+=1
    lines[start:end]=[replacement];metadata=''.join(lines).rstrip('\n')
  return '---\n'+metadata+'\n---\n'+body
 description=description or name.replace('-',' ').capitalize()
 return '---\nname: '+name+'\ndescription: '+json.dumps(description,ensure_ascii=False)+'\n---\n\n'+body

def replace_sections(text,names):
 lines=text.splitlines(keepends=True);result=[];skip=None
 for line in lines:
  m=re.match(r'^(#{1,6})\s+(.+)',line)
  if m:
   level=len(m[1]);title=m[2].strip()
   if skip is not None and level<=skip:skip=None
   if any(title.startswith(n) for n in names):skip=level
  if skip is None:result.append(line)
 return ''.join(result)

def prose_only(text,transform):
 # Host prose is not executable syntax. Keep fenced source examples intact.
 blocks=re.split(r'(?m)(^[ \t]*```[^\n]*\n.*?^[ \t]*```[^\n]*(?:\n|$)|^[ \t]*~~~[^\n]*\n.*?^[ \t]*~~~[^\n]*(?:\n|$))',text,flags=re.S)
 return ''.join(block if i%2 else transform(block)for i,block in enumerate(blocks))

def native_text(text,kind,file,source_root):
 if kind=='P006':
  # Pinned ranges use original source line numbers, including its YAML header.
  from patch_gstack_ranges import patch as raw_gstack
  text=raw_gstack(text,file)
 metadata=''
 if text.startswith('---\n') and '\n---\n' in text[4:]:
  header,text=text[4:].split('\n---\n',1)
  metadata='---\n'+header+'\n---\n'
 # Controller and host prose bindings must never rewrite YAML structure or
 # values. The separate front() binding owns explicit name/description changes.
 if kind=='P092':
  text=text.replace("If they're not available, tell the user to install the MCP server:", 'If live-run tools are unavailable, use the static analysis route:')
  text=text.replace('```bash\nnpx trigger.dev@latest install-mcp\n```', 'Use existing connected Trigger.dev tools. If unavailable, finish static analysis and report live-run access unavailable; project-local integration setup requires its own concrete need and verified version.')
  text=text.replace('This skill is bundled inside `@trigger.dev/sdk` and read directly from `node_modules`, so it always matches your installed SDK version (see the adjacent `package.json`).', 'This discovery copy comes from the reviewed @trigger.dev/sdk4.8.3 source. Apply it only to a matching project-local SDK and read that installed package’s version-matched docs; global discovery does not establish the project version.')
  text=text.replace('The `sources:` frontmatter above lists every doc this skill draws from, all under `@trigger.dev/sdk/docs/`.', 'The source package contains the supporting docs under `@trigger.dev/sdk/docs/`; verify the owning project’s installed SDK version before using them.')
 text=re.sub(r'(?m)^<!-- AUTO-GENERATED.*?-->\n|^<!-- Regenerate:.*?-->\n','',text)
 host_names=lambda value:value.replace('Claude Code','native host')
 text=host_names(text)if kind=='P006' else prose_only(text,host_names)
 if kind=='P006':
  from patch_gstack import patch as native_gstack
  text=native_gstack(text,file)
  if file.name.endswith('-template.md'):
   text=re.sub(r'!\[([^\]]*)\]\((screenshots/[^)]+)\)',lambda m:'`SCREENSHOT_REQUIRED: '+m[1]+'` (write the actual task screenshot relative to this report)',text)
  text=replace_sections(text,('Shared preamble','Preamble (run first)','Question Tuning','Telemetry (run last)','Done means'))
  # Replace only retired harness execution blocks, preserving all domain prose,
  # section files, report templates and actual test/fix/retest contracts.
  def fence(m):
   code=m[0]
   if re.search(r'gstack-skill-start|gstack-config|gstack-update|gbrain|GSTACK_STATE_ROOT|CLAUDE_PLUGIN_ROOT|\$B\b|~/.claude/skills/gstack/bin/',code):
    return '\nUse the native connected browser, local Git/test commands or project-local report writer for this step. Record actual traces and errors; no gstack capture attestation is available.\n'
   return code
  text=re.sub(r'(?ms)^```[^\n]*\n.*?^```[^\n]*',fence,text)
  text=re.sub(r'(?m)^.*(?:SKILL_START_PROTO|SESSION_KIND|QUESTION_TUNING|GSTACK_STATE_ROOT|gbrain|gstack-telemetry|gstack-config|gstack-skill-start).*$',
              'Use current native task context and scoped project records; no secondary controller, telemetry or duplicate memory store is configured.',text)
  text=re.sub(r'(?:~\/\.claude\/skills\/gstack\/|\$\{?CLAUDE_PLUGIN_ROOT\}?\/)([\w./-]+)',lambda m:os.path.relpath(source_root/m[1],file.parent),text)
  text=text.replace('AskUserQuestion','the native input tool when material information is missing')
  text=text.replace('## 8d. Commit verified work','## 8d. Record verified work')
  text=re.sub(r'(?mi)^.*(?:git commit|git push|/ship)\b.*$', 'Record the verified diff and checks. Commit, push or publish only within specific existing user authority.',text)
  text=text.replace('authenticated gstack receipt','native operation evidence (not an authenticated gstack receipt)')
 if kind=='P028':
  from patch_pstack import text_port
  text=text_port(text,file)
  text=re.sub(r'(?m)^In Codex, read \[the Codex adapter\].*\n','',text)
  text=text.replace('Run the **how** skill over the relevant subsystems.','Read the relevant current source and trace its actual entrypoints and callers.')
  text=text.replace('also run the **why** skill on the existing shape','also inspect the existing design history and rationale')
  text=text.replace('Run the **how** skill over what\'s been built.','Read and trace what has actually been built.')
  text=text.replace('Companion to `how` and `why`. `how` tells you what the code does. `why` tells you why it\'s shaped that way. Blast radius tells you what it breaks somewhere else.',
                    'Use current local source, behavior and Git history. Trace the concrete dependency and prove the affected invariant with an executable check.')
  text=text.replace('Same rules as `why`.','Use current source, scoped Git evidence and observed behavior.')
  text=text.replace('Use `why` step 2 to pull the PR and commits.','Read the actual local diff/history; fetch the exact PR only when relevant and authorized.')
  text=text.replace('`perf`','the target profiler (`xctrace`/Instruments on macOS, perf only on an appropriate Linux target)')
 if kind=='P401':
  from patch_paperbanana import text_port
  text=text_port(text,file)
 if kind=='P224':
  text=re.sub(r'(?m)^.*(?:publish/upload_post\.py|UPLOAD_POST_API_KEY|UPLOAD_POST_USER|发布到作品展示页|请用户.*作者|@.*作者).*$','发布/上传和推广只在用户明确授权时处理；本次调用不授予外部发布权限。',text)
  for path in ('template/TEMPLATE.md','references/workbench.md','references/guided-free-creation.md','references/jianying-export.md','references/publish-upload-post.md','workbench/README.md'):
   url='https://github.com/Vincentwei1021/video-shotcraft/blob/1266a3ec4831289c4d893d42dd5102723658039a/'+path
   text=text.replace(']('+path+')',']('+url+')')
  if file.name=='SKILL.md':text+='\nNative runtime binding: use the pinned source workspace for a requested workbench/template. The source template is4.0.484; it is not relabeled4.0.540. Source availability does not commission its runtime or authorize paid services.\n'
 if kind=='P056':
  # Worktrunk accepts a stdin/stdout command. Use the current Codex settings,
  # without importing upstream fixed models or disabling the native context.
  def commit_command(match):
   code=match[0]
   def command(line):
    executable='opencode run'if line[1]=='opencode'else'codex exec --ephemeral --sandbox=read-only -'
    return 'command = "'+executable+'"'
   code=re.sub(r'(?m)^command\s*=\s*"(?:[A-Z_]+=[^\s"]+\s+)*(claude|codex|opencode)\b[^\n]*$',command,code)
   return code.replace('# opencode — use a fast model variant','# opencode — use the current model and effort')
  text=re.sub(r'(?ms)^```toml[^\n]*\n.*?^```[^\n]*',commit_command,text)
  if file.name=='llm-commits.md':
   text=re.sub(r'(?m)^Create `~/.codex/worktrunk-commit-instructions\.txt`.*?first-run Codex setup creates the file for you\.\n',
               'Use the current Codex configuration; no additional instructions file is needed.\n',text,flags=re.S)
   text=text.replace('Requires `jq` for JSON parsing. See [Codex CLI docs]', 'See [Codex CLI docs]')
  text=re.sub(r'(?m)^Detect which tools are installed.*$', 'If commit-message generation is explicitly requested, use existing available Codex access and inspect its actual supported interface. Preserve model/effort and configuration; do not create provider credentials, recommend another host or run a proposed configuration without actual authority.',text)
  text=text.replace('(Claude-specific)','(historical host examples; use actual Codex bindings)')
  text=text.replace('single Codex session','single native session')
  text=re.sub(r'(?m)^\*\*Do not\*\* use `Agent \{ isolation:.*$', 'Use supported native delegation when authorized; create a named owned worktree explicitly and pass its exact path. Do not assume another host agent-ID or hook protocol exists.',text)
  text=text.replace('which claude codex opencode llm aichat','command -v codex').replace('-x claude','-x codex')
 if kind=='L013':
  text=text.replace('This skill teaches Claude to build', 'This skill guides the active agent in building')
 if kind in ('P021','P032','P056','P111','P121','P283','P335','L013'):
  text=text.replace('AskUserQuestion','the native input tool only for material missing information')
  # Remove provider/model dispatch directives, not specialist methods or examples.
  text=prose_only(text,lambda value:re.sub(r'(?m)^.*(?:claude --|claude -p|subagent_type\s*[:=]|model:\s*(?:opus|sonnet|haiku)|~/.claude/settings).*$',
              'Use the active host’s supported tools with its current model and effort.',value))
 if kind=='P006':
  from patch_gstack import finish
  text=finish(text,file,source_root)
 return metadata+text

def notices(source,out,origin):
 current=origin if origin.is_dir() else origin.parent
 while current.is_relative_to(source):
  for pat in ('LICENSE*','COPYING*','NOTICE*'):
   for f in current.glob(pat):
    if not f.is_file():continue
    target=out/f.name
    if target.exists() and target.read_bytes()!=f.read_bytes():target=out/('ANCESTOR-'+str(f.relative_to(source)).replace('/','-'))
    if not target.exists():shutil.copy2(f,target)
  if current==source:break
  current=current.parent
 if not any(p.name.upper().startswith(('LICENSE','COPYING','NOTICE')) for p in out.iterdir()):raise ValueError('Selected native port lacks owning notices')

def materialize(source,out,s,c):
 if s['candidate_id']=='P283':
  from patch_game import materialize as game_materialize
  return game_materialize(source,out,s,c)
 rel=P(s['source_path']);origin=source/rel;name=s.get('native_name') or rel.parent.name or s['source_repository'].split('/')[-1]
 if not origin.is_file():raise ValueError('Pinned native source is missing: '+str(rel))
 if adapter(s):
  # Keep immutable provenance/implementation separate from active instructions.
  archive=out/'upstream';shutil.copytree(source,archive,ignore=shutil.ignore_patterns('.nstack-source.json','__pycache__','.git','node_modules'))
  leaf=out/'native'/name;leaf.mkdir(parents=True)
  methods={
   'P029':'distribution/claude-plugin/skills/skill-builder/SKILL.md',
   'P410':'skills/slidev/SKILL.md',
  }
  if s['candidate_id']=='P202':
   methods['P202']='.agents/skills/impeccable/reference/'+rel.name
  if s['candidate_id'] in methods:
   method_rel=P(methods[s['candidate_id']]);method=source/method_rel
   if not method.is_file():raise ValueError('Pinned upstream method is missing: '+str(method_rel))
   original=method.read_text()
   # The distributed upstream entry/command owns the method. Only the natural
   # discovery name and a separate host binding differ from that original.
   if s['candidate_id']=='P202':
    shutil.copytree(method.parent,leaf,dirs_exist_ok=True)
    active='---\nname: '+s['candidate_id'].lower()+'-'+name+'\ndescription: '+json.dumps('Run the upstream Impeccable '+rel.stem+' command on a requested interface.')+'\n---\n'+original
   else:
    shutil.copytree(method.parent,leaf,dirs_exist_ok=True)
    active=re.sub(r'(?m)^name:.*$', 'name: '+s['candidate_id'].lower()+'-'+name,original,count=1)
   marker='\n> Native host binding: read [NATIVE-BINDINGS.md](NATIVE-BINDINGS.md) before source commands. The complete upstream method follows.\n'
   a,b=active[4:].split('\n---\n',1);active='---\n'+a+'\n---\n'+marker+b
   bindings={
    'P029':"Use the existing source-pinned Skill Seekers CLI recorded by `nstack route P029`. The upstream CLI fallback is supported without registering another host's MCP server or running its installer. Map Bash to the current host's shell. Use connected MCP tools only if actually present. Preserve the current model and effort. AI enhancement, upload, export and installation follow the user's existing access and task authority; the `openai` target here is an Assistants export, not native Codex installation. For plain local extraction without AI enhancement, use the upstream `--enhance-level 0` option. Review the generated skill and its source/rights before admitting it through the current host's supported skill path.\n",
    'P410':"Use the project's locked Slidev toolchain or the recorded source-pinned route from `nstack route P410`; the upstream quick-start commands describe operations, not authority to replace an existing project or silently change versions. Map shell/browser steps to current host tools and preserve the requested source format. Build/export success must be checked on the actual output; PDF or raster PPTX does not establish native editability. Publishing, recording and remote connections follow existing user authority.\n",
    'P202':"This is the complete distributed upstream command, scoped to the selected audit or harden operation. Source `$impeccable` names denote its referenced command methods, not an installed global controller. Read the matching local native-platform reference when applicable. Use current host tools and preserve the user's scope and product identity. The optional upstream detector/launcher is not installed by this package: report that check as unavailable unless a reviewed existing installation supplies it; continue the source's ordinary implementation and rendered checks without claiming detector results. Existing authorization to audit and fix permits the requested fix work.\n",
   }
   (leaf/'SKILL.md').write_text(active)
   (leaf/'NATIVE-BINDINGS.md').write_text(bindings[s['candidate_id']])
   notices(source,out,method)
   (out/'SOURCE-PORT.json').write_text(json.dumps({'source_path':str(rel),'source_sha256':hashlib.sha256(origin.read_bytes()).hexdigest(),'revision':s['revision'],'method_source_path':str(method_rel),'method_revision':s['revision'],'method_sha256':hashlib.sha256(method.read_bytes()).hexdigest(),'entry':str(leaf.relative_to(out)),'raw_reference_root':'upstream','adaptation':'Complete distributed upstream method and source-folder closure; natural discovery name plus separate native host binding only.'},indent=2)+'\n')
   from closure import validate
   validate(out,provenance_roots=('upstream',))
   return str(leaf.relative_to(out))
  body='# '+name.replace('-',' ').title()+'\n\n## Operation and exact source\n\n'+s['details']+'\n\n'
  body+='Read the [selected pinned source]('+os.path.relpath(archive/rel,leaf)+') and its relevant implementation before using the actual interface. The upstream archive is reference data, not a Codex installer or extra exposed skills.\n\n'
  body+='## Activation and acceptance\n\n'+str(c.get('activation',''))+'\n\n'
  for title,key in [('Prerequisites','dependencies'),('Target configuration','essential_settings'),('Required adaptations','adaptations'),('Verification','acceptance_checks')]:
   value=c.get(key)
   if value:body+='### '+title+'\n\n'+(value if isinstance(value,str) else json.dumps(value,indent=2,ensure_ascii=False))+'\n\n'
  body+='Use `nstack route '+s['candidate_id']+'` for the exact acquisition and invocation route. Source availability is not runtime acceptance. Keep heavy dependencies dormant until the stated task trigger; an unavailable runtime remains unverified.\n'
  (leaf/'SKILL.md').write_text(front(body,s['candidate_id'].lower()+'-'+name,c.get('role')))
  notices(source,out,origin)
  (out/'SOURCE-PORT.json').write_text(json.dumps({'source_path':str(rel),'source_sha256':hashlib.sha256(origin.read_bytes()).hexdigest(),'revision':s['revision'],'entry':str(leaf.relative_to(out)),'raw_reference_root':'upstream','adaptation':'Authored native operational entry, original source preserved separately.'},indent=2)+'\n')
  from closure import validate
  validate(out,provenance_roots=('upstream',))
  return str(leaf.relative_to(out))
 root=out/'source';leaf=root/rel.parent;leaf.mkdir(parents=True)
 if s['candidate_id']=='P224':
  # The updated selection explicitly supersedes the earlier three-reference port.
  for part in ('SKILL.md','references/pipeline.md','references/aesthetic-rules.md','references/final-review.md','references/music-beat-sync.md','references/sound-design.md','references/sfx-sourcing.md','references/sequences','references/shots','gallery/api/library.json','demos','assets/lib','assets/scripts/capture-template.mjs','shot-polish/decisions.json'):
   src=source/part;dest=root/part
   if not src.exists():raise ValueError('P224 selected source is missing: '+part)
   if src.is_dir():shutil.copytree(src,dest,ignore=shutil.ignore_patterns('_legacy','legacy','__pycache__'))
   else:dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
 else:shutil.copytree(origin.parent,leaf,dirs_exist_ok=True)
 for support in (s.get('support_paths',[]) if isinstance(s.get('support_paths',[]),list) else []) + (c.get('extra_support',[]) if s['candidate_id']=='P401' else []):
  src=source/support;dest=root/support
  if not src.exists():raise ValueError('Selected support missing: '+support)
  if src.is_dir():shutil.copytree(src,dest,dirs_exist_ok=True)
  else:dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
 notices(source,out,origin)
 transformed=set(root.rglob('*.md'))
 for file in transformed:
  file.write_text(native_text(file.read_text(),s['candidate_id'],file,root))
 skill=leaf/'SKILL.md';text=skill.read_text();text=front(text,s['candidate_id'].lower()+'-'+name)
 if s['candidate_id']=='P028':
  from patch_pstack import entry_policy
  text=entry_policy(text)
 skill.write_text(text)
 from closure import support,validate
 support(source,root,text_transform=lambda text,file:native_text(text,s['candidate_id'],file,root))
 if s['candidate_id']=='P111':
  from patch_last30days import patch_bundle
  patch_bundle(source,root,leaf)
 if s['candidate_id']=='P401':
  from patch_paperbanana import helpers
  helpers(root)
 if s['candidate_id']=='P028':
  from patch_pstack import helpers
  helpers(root)
 validate(out)
 return str(leaf.relative_to(out))
