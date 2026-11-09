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
 body=text
 if text.startswith('---\n') and '\n---\n' in text[4:]:
  metadata,body=text[4:].split('\n---\n',1)
  if description is None:
   match=re.search(r'(?m)^description:\s*(.+)$',metadata)
   if match and match[1] not in ('>','>-','|','|-'):description=match[1].strip().strip('"\'')
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

def native_text(text,kind,file,source_root):
 if kind=='P006':
  from patch_gstack_ranges import patch as raw_gstack
  text=raw_gstack(text,file)
 text=re.sub(r'(?m)^<!-- AUTO-GENERATED.*?-->\n|^<!-- Regenerate:.*?-->\n','',text)
 text=text.replace('Claude Code','Codex').replace('CLAUDE.md','AGENTS.md')
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
  a=text.find('Run the **arena** skill with the design-sketch task')
  b=text.find('Design it twice.',a) if a>=0 else -1
  if b>=0:text=text[:a]+('Compare plausible structural alternatives when their consequences justify it. Use the complete [design runner brief](references/runner-prompt.md) and actual source evidence. Native Codex owns the task; preserve the current model and effort.\n\n')+text[b:]
  text=text.replace('Arena returns one synthesized design package.','Synthesize the supported candidates into one design package.')
  text=text.replace('Return to Phase B and re-run arena.','Return to Phase B and compare the revised alternatives.')
  text=text.replace('run the **interrogate** skill','perform a proportionate adversarial review')
  text=text.replace('Run the **how** skill over what\'s been built.','Read and trace what has actually been built.')
  text=text.replace('Companion to `how` and `why`. `how` tells you what the code does. `why` tells you why it\'s shaped that way. Blast radius tells you what it breaks somewhere else.',
                    'Use current local source, behavior and Git history. Trace the concrete dependency and prove the affected invariant with an executable check.')
  text=text.replace('Same rules as `why`.','Use current source, scoped Git evidence and observed behavior.')
  text=text.replace('Use `why` step 2 to pull the PR and commits.','Read the actual local diff/history; fetch the exact PR only when relevant and authorized.')
  text=re.sub(r'(?m)^.*pstack-models\.mdc.*$', 'Preserve the current user-selected model and effort; no model registry or fixed runner roster is required.',text)
  text=re.sub(r'(?m)^.*(?:claude-opus-|grok-4\.|run it as an `arena`).*$', 'For consequential independent review, use supported native delegation within existing task authority and available capacity.',text)
  text=text.replace('Write it through `unslop`, cite real code, and strip anything private before it goes anywhere public.','Write plainly, cite actual source and remove private material before specifically authorized publication.')
  text=text.replace('`perf`','the target profiler (`xctrace`/Instruments on macOS, perf only on an appropriate Linux target)')
 if kind=='P401':
  from patch_paperbanana import text_port
  text=text_port(text,file)
 if kind=='P224':
  text=replace_sections(text,('交付收尾（所有模式共用）',))
  text=re.sub(r'(?m)^.*然后明确询问：.*$', '依据现有简报选择合适路线并继续；只有影响结果的重大歧义才询问。',text)
  text=text.replace('用户尚未决定：停在此处等待选择；不要默认替用户选择，也不要开始制作。','用户未指定路线：根据已给简报选择可行路线并继续；只询问无法合理决定的重大分歧。')
  text=re.sub(r'(?ms)^交付后先 `node workbench/scripts/open\.mjs.*?(?=^\*\*常见坑)', '交付所请求的成片、可编辑源、音频分轨和证据。动效工作台仅在用户要求其编辑界面时另行配置；不附加发布、推广或展示页任务。\n\n',text)
  text=re.sub(r'(?ms)^9\. \*\*为交付后的动效工作台留好接口\*\*.*?(?=^\*\*产出)', '9. 时间线、字幕和音效共用明确的帧原点与可编辑参数；只有用户要求工作台编辑时才按对应源配置工作台。\n\n',text)
  text=re.sub(r'(?m)^.*(?:publish/upload_post\.py|UPLOAD_POST_API_KEY|UPLOAD_POST_USER|发布到作品展示页|请用户.*作者|@.*作者).*$','发布/上传和推广不属于默认交付；只在用户另行明确授权时处理。',text)
  for path in ('template/TEMPLATE.md','references/workbench.md','references/guided-free-creation.md','references/jianying-export.md','references/publish-upload-post.md','workbench/README.md'):
   url='https://github.com/Vincentwei1021/video-shotcraft/blob/1266a3ec4831289c4d893d42dd5102723658039a/'+path
   text=text.replace(']('+path+')',']('+url+')')
  if file.name=='SKILL.md':text+='\nNative source/runtime boundary: choose gallery index → requested cards → exact tuned demo → its transitive fixtures/assets lazily. Preserve original motion/camera math. Template and workbench are separate task-triggered source closures, not installed workflow commands. The upstream template is4.0.484; do not relabel it4.0.540 without the required baseline-versus-candidate moving-frame/audio proof. Product-specific visual/hold/music examples follow the actual brief. Asset/track rights are separate from code. No paid provider/key acquisition follows from a reference.\n'
 if kind=='P056':
  text=re.sub(r'(?m)^Detect which tools are installed.*$', 'If commit-message generation is explicitly requested, use existing available Codex access and inspect its actual supported interface. Preserve model/effort and configuration; do not create provider credentials, recommend another host or run a proposed configuration without actual authority.',text)
  text=text.replace('(Claude-specific)','(historical host examples; use actual Codex bindings)')
  text=text.replace('single Codex session','single native session')
  text=re.sub(r'(?m)^\*\*Do not\*\* use `Agent \{ isolation:.*$', 'Use supported native delegation when authorized; create a named owned worktree explicitly and pass its exact path. Do not assume another host agent-ID or hook protocol exists.',text)
  text=text.replace('which claude codex opencode llm aichat','command -v codex').replace('-x claude','-x codex')
 if kind in ('P021','P032','P056','P111','P121','P283','P335','L013'):
  text=text.replace('AskUserQuestion','the native input tool only for material missing information')
  # Remove provider/model dispatch directives, not specialist methods or examples.
  text=re.sub(r'(?m)^.*(?:claude --|claude -p|subagent_type\s*[:=]|model:\s*(?:opus|sonnet|haiku)|~/.claude/settings).*$',
              'Use the current native tools, model and effort. Delegate a bounded independent question only when useful and authorized.',text)
 if kind=='P006':
  from patch_gstack import finish
  text=finish(text,file,source_root)
 return text

NATIVE_SCOPE="""## Native execution

Use this specialist on demand with current Codex tools, model, effort, permissions and existing task authority. Source host commands are adapted below. Read relevant full support; verify actual artifacts and report missing coverage. No controller, telemetry, credential setup or new spending is installed.

"""

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
 rel=P(s['source_path']);origin=source/rel;name=s.get('native_name') or rel.parent.name or s['source_repository'].split('/')[-1]
 if not origin.is_file():raise ValueError('Pinned native source is missing: '+str(rel))
 if adapter(s):
  # Keep immutable provenance/implementation separate from active instructions.
  archive=out/'upstream';shutil.copytree(source,archive,ignore=shutil.ignore_patterns('.nstack-source.json','__pycache__','.git','node_modules'))
  leaf=out/'native'/name;leaf.mkdir(parents=True)
  body='# '+name.replace('-',' ').title()+'\n\n'+NATIVE_SCOPE+'## Operation and exact source\n\n'+s['details']+'\n\n'
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
 a=text.index('\n---\n')+5;text=text[:a]+'\n'+NATIVE_SCOPE+text[a:];skill.write_text(text)
 from closure import support,validate
 support(source,root,text_transform=lambda text,file:native_text(text,s['candidate_id'],file,root))
 if s['candidate_id']=='P401':
  from patch_paperbanana import helpers
  helpers(root)
 if s['candidate_id']=='P028':
  from patch_pstack import helpers
  helpers(root)
 validate(out)
 return str(leaf.relative_to(out))
