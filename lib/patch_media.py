"""Selected media expertise ports; editable source and requested final artifact control."""
import pathlib,re,json,hashlib,difflib
P=pathlib.Path
PRIVACY_BOUNDARY='''## Native media client admission

**UNADMITTED: credential-discovering clients.** Do not invoke the bundled audio engine, direct HeyGen TTS/voice scripts, cloud/provider/avatar clients, or the HyperFrames CLI `media-use` and `auth` commands. This includes `media-use --local-only`, cache/doctor/list modes and an explicitly approved cloud budget: those paths can inspect credentials before selecting a provider. The three bundled audio command entrypoints fail closed; the shared HeyGen helper performs no environment-file or global-store discovery. Full original methods remain in the source archive for review. Do not bypass the gate by importing another provider helper, changing environment variables, choosing another working directory for `media-use`, or running the archive.

Preserve the full story, timing, audio, asset, caption, local treatment and editing methods below. Use user-supplied media and current authorized native tools. The separate locked CLI `tts` command uses local Kokoro, but startup reads cwd `.env` and checks desktop catch-up records for argument paths. Its conditional local route therefore requires a newly created, empty task-owned temporary working directory AND a separate fresh empty process home. Use a clean process environment containing only the approved toolchain PATH, locale, owned HOME/TMPDIR and HYPERFRAMES_NO_TELEMETRY=1, DO_NOT_TRACK=1, HYPERFRAMES_NO_UPDATE_CHECK=1, HYPERFRAMES_NO_AUTO_INSTALL=1, HYPERFRAMES_SKIP_SKILLS=1; inherit no provider keys, config-directory overrides or NODE_OPTIONS. Copy only the authorized script text into that working directory, then use `tts --text-file <owned-temp/script.txt> --output <owned-temp/narration.wav>`. Keep every CLI file argument inside it: no literal script text or project paths in argv, and no environment/chat/config files copied. Copy the finished audio back with native tools afterward. Verify the recorded executable and already available local model/dependencies first; do not download or install them incidentally. If this isolated route lacks its model/runtime, report the gap. This is source-reviewed, not evidence that synthesis ran. Other local CLI commands need their own source/effect check; `--local-only` alone proves neither credential privacy nor admission. A missing key-safe capability is a gap to report, not permission to discover credentials. Re-admit cloud clients only after a separate review establishes explicit task-scoped input, no file/store discovery or refresh, and actual account/spending authority.

Cloud, sign-in, provider and bundled-audio examples below retain upstream method detail as reference only; they are blocked under this boundary. See the bundle's NATIVE-PRIVACY provenance and exact original source copies.
'''
UNADMITTED='UNADMITTED media client: credential discovery is disabled; use an admitted native/local route.'

def finalize_credentials(source,out,spec):
 """Gate every mirrored P215 client copy after support closure is complete."""
 if spec['candidate_id']!='P215':raise ValueError('Media privacy gate is P215-only')
 record=out/'NATIVE-PRIVACY'
 if record.exists():raise ValueError('Media privacy gate must run once after closure')
 changes=[]
 def retain(file,text):
  before=file.read_text()
  if before==text:return
  rel=file.relative_to(out);origin=source/rel
  if not origin.is_file():raise ValueError('Missing pinned media original: '+str(rel))
  original=origin.read_bytes();archive=record/'upstream'/P(str(rel)+'.reference.txt')
  archive.parent.mkdir(parents=True,exist_ok=True);archive.write_bytes(original)
  file.write_text(text)
  changes.append({'path':str(rel),'upstream_sha256':hashlib.sha256(original).hexdigest(),
                  'active_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
                  'original':str(archive.relative_to(out)),
                  'patch':''.join(difflib.unified_diff(original.decode().splitlines(True),text.splitlines(True),fromfile='upstream/'+str(rel),tofile='native/'+str(rel)))})
 for file in sorted(out.rglob('*.md')):
  if record in file.parents:continue
  text=file.read_text()
  if file.name!='SKILL.md' and not re.search(r'heygen|audio\.mjs|media-use|--provider|auth (?:login|status|refresh)',text,re.I):continue
  # Keep frontmatter first and retain the complete source method after the boundary.
  offset=text.index('\n---',3)+4 if text.startswith('---\n') else 0
  retain(file,text[:offset]+'\n\n'+PRIVACY_BOUNDARY+'\n'+text[offset:].lstrip('\n'))
 for file in sorted(out.rglob('heygen.mjs')):
  if record in file.parents or file.parts[-3:]!=('scripts','lib','heygen.mjs'):continue
  text=file.read_text()
  start=text.index('// Walk up ≤5 dirs');end=text.index('// → { headers }',start)
  text=text[:start]+'// Native admission: never load a project or ancestor environment file.\nexport function loadEnvFromDir(_startDir) {}\n\n'+text[end:]
  start=text.index('function resolveCredential()');end=text.index('// → "oauth"',start)
  text=text[:start]+'// No cloud client is admitted here, including explicit process credentials.\nfunction resolveCredential() { return null; }\n\n'+text[end:]
  start=text.index('// → auth headers object');end=text.index('// Authed JSON request',start)
  text=text[:start]+'export function heygenAuthHeaders() { throw new Error('+json.dumps(UNADMITTED)+'); }\n\n'+text[end:]
  start=text.index('export async function heygenJSON(');end=text.index('function errorCode(',start)
  text=text[:start]+'export async function heygenJSON() { throw new Error('+json.dumps(UNADMITTED)+'); }\n\n'+text[end:]
  retain(file,text)
 for name in ('audio.mjs','heygen-tts.mjs','heygen-voice.mjs'):
  for file in sorted(out.rglob(name)):
   if record in file.parents or file.parent.name!='scripts' or file.parent.parent.name!='audio':continue
   text=file.read_text();offset=text.index('\n')+1 if text.startswith('#!') else 0
   retain(file,text[:offset]+'// Native command admission; full method retained below and in the source archive.\nthrow new Error('+json.dumps(UNADMITTED)+');\n'+text[offset:])
 if not changes:raise ValueError('P215 media privacy closure was empty')
 record.mkdir(exist_ok=True)
 (record/'ADAPTATION.patch').write_text(''.join(x.pop('patch') for x in changes))
 (record/'SOURCE-ADAPTATION.json').write_text(json.dumps({'candidate_id':'P215','repository':spec['source_repository'],'revision':spec['revision'],
  'boundary':'Credential-discovering bundled command clients and CLI media-use/auth/cloud/provider/avatar routes are unadmitted; source methods remain available for review. This instruction gate does not sandbox arbitrary archived/direct source execution.',
  'local_limit':'CLI tts is local Kokoro but requires empty owned working directory to avoid startup .env, telemetry opt-outs, exact commissioned runtime and already available models. No runtime/provider execution is claimed.',
  'files':changes},indent=2)+'\n')
ROUTING='''## Source, timing and output contract

The requested editable source controls dispatch: keep React scenes in Remotion, standalone HTML motion in HyperFrames, and native shots/grades/buses in the chosen engine or Resolve/Fusion/Fairlight. Transfer cue IDs, frame rate/origin, stems and asset receipts rather than screenshots alone. Keep a paused timeline registered after fonts/async setup; deterministic renderAt(time) and seeded inputs must reproduce the same frame. Check representative moving frames plus endpoint/blank-frame controls and the final mux. A launch-film aesthetic checker does not validate scientific values or gameplay readability. Keep the last successful artifact until replacement succeeds.
'''
def change(s,old,new):
 if old not in s:raise ValueError('Missing media patch anchor: '+old[:90])
 return s.replace(old,new)
def scope_pipeline(text,spec):
 # Retain the production expertise, not template onboarding or delivery promotion.
 text=text[text.index('## 阶段 0：'):text.index('## 阶段 7：')]
 start=text.index('9. **为交付后的动效工作台留好接口**')
 end=text.index('**产出**',start)
 text=text[:start]+'9. Keep one editable timeline/cue manifest. Derive subtitles, SFX and transitions from it; preserve the incumbent project without adding a workbench.\n\n'+text[end:]
 start=text.index('1. 读 `references/sound-design.md` 与 `references/sfx-sourcing.md`')
 end=text.index('3. **BGM**',start)
 sourcing=f'https://github.com/{spec["source_repository"]}/blob/{spec["revision"]}/references/sfx-sourcing.md'
 review=f'https://github.com/{spec["source_repository"]}/blob/{spec["revision"]}/references/final-review.md'
 text=text[:start]+('1. Read the local sound-design reference. User-supplied audio wins; choose rights-cleared recordings, stock or procedural sounds for the task. '+
       f'Consult the [pinned sourcing reference]({sourcing}) only for relevant methods; no provider or missing download script is installed.\n'+
       '2. Record source, license, cue identity, actual quality and measured offsets in the project audio manifest. Preserve revisable stems.\n')+text[end:]
 text=text.replace('`references/aesthetic-rules.md`','the brief-specific visual acceptance criteria')
 text=text.replace('`references/shots/`',"the incumbent project's approved shot references")
 text=text.replace('`references/sequences/`',"the incumbent project's sequence references")
 text=text.replace('`src/workbench.ts`','the editable timeline/cue manifest').replace('`assets/audio/bgm/`','existing rights-cleared music')
 text=text.replace('从 Freesound','从用户选定且许可清楚的音频来源').replace('用 Freesound 的','用许可清楚的')
 return ('# Scoped production methods\n\nModified from the pinned upstream pipeline. This is read-only shot, timing, mix and QA expertise. '+
         'The three retained local references are pipeline.md, sound-design.md and music-beat-sync.md. Other upstream project paths, commands, templates and example assets are illustrative, not installed tools or instructions to acquire a workflow. '+
         'Preserve the brief, incumbent renderer, model/effort and current authority; no fixed brand style or agent team applies.\n\n'+text+
         '\n## Final acceptance and handoff\n\n'+f'Consult the [pinned final-QA reference]({review}) for relevant checks, adapting to the supplied brief. '+
         'Inspect current rendered frames and actual mux; check text, cuts, cue/frame offsets, loudness and peak, and reopen the final export. '+
         'Use a fresh reviewer only when it earns the cost and is authorized. Preserve editable source, stems, cue/asset/license manifests and the last accepted render. '+
         'Deliver the requested artifact; do not launch a workbench, publish, upload, solicit promotion or add another installer.\n')
def patch(id,name,spec,out):
 p=out/'SKILL.md';s=p.read_text()
 if id=='P215':
  for file in out.rglob('*.md'):
   text=file.read_text();text=text.replace('npx hyperframes', '"$NSTACK_HYPERFRAMES"')
   text=text.replace("Local or the person's own key (only when they ask)", 'Available native or free local tools')
   text=text.replace('Use local tools only when the person asks, not as a fallback.','Use available native or free local tools when they fit the task.')
   text=re.sub(r'(?m)^\*\*(?:Sign in|Host apps|HeyGen|Credits)\.\*\*.*$', 'Use current native subscription capabilities and free local tools first. No provider sign-in, new credential, credit purchase or paid API call is authorized by this skill. State consequential costs and dependency limits plainly; ask only for actual new spending or required access.',text)
   text=text.replace('Never tell the person prices, estimates or usage','Disclose consequential costs and usage limits before seeking new spending')
   text=text.replace('no cheaper or free swaps','prefer suitable existing native or free tools')
   text=text.replace('the host pays', 'a host setting does not grant spending authority')

   text=re.sub(r'(?m)^After a verified render, send one `feedback.*$', 'Keep task-local diagnostics only. No feedback submission or unsolicited desktop/update promotion is part of this route.',text)
   text=re.sub(r'(?m)^.*feedback --search-miss.*$', 'If the registry has no suitable effect, record the gap locally and choose a brief-appropriate implementation. Do not submit feedback.',text)
   file.write_text(text)
  s=p.read_text()
  if name=='hyperframes':
   s=change(s,'Use it unless another framework or a plain browser recording is asked for.','Use it when standalone HTML motion is the requested or existing source. Preserve a different incumbent renderer and its editable source.')
   s=re.sub(r'; at the start of a new video,.*?remaining plan usage.*?\)\.', '.',s)
   s=change(s,'three storylines that are three different films, in words only; the person picks unless they asked for the file or no stops.','compare distinct story directions when useful, then choose from the supplied brief without a compulsory story-choice gate. Ask only for material missing direction.')
   s=change(s,'- Render when the person approves the Studio preview, asks for the file or asks for no stops, after your check and review pass; otherwise stop at the preview and wait.','- After checks and actual frame review, render the requested final video. A sufficient create/build request carries authority through its finished artifact. Stop at a preview only when that is the requested deliverable.')
  if name=='hyperframes-cli':
   s=re.sub(r'A `--json` result may carry.*?(?=\n\n)', 'Record actual runtime version and task diagnostics. Do not promote updates or change the locked release during a run.',s,flags=re.S)
   s=change(s,'give the person the project URL and wait, unless they asked for the file or for no stops. Passing checks alone is not a reason to render.','inspect the current preview and continue to the requested final render after checks. A preview-only request ends at the preview.')
   s=s.replace('; paid plan: `cloud render --fps <data-fps> --quality high -o out.mp4`','; local free execution only unless a separate route is specifically authorized')
   s=re.sub(r'(?m)^\| Desktop app \|.*$', '| Desktop app | Only for an explicit requested operation; no automatic launch or promotion |',s)
  s+='\n## Locked local invocation\n\nSet HYPERFRAMES_NO_TELEMETRY=1 and DO_NOT_TRACK=1 in the actual process environment. Set NSTACK_HYPERFRAMES to the absolute project/private executable from the commissioned immutable source/package lock. Check its actual help and browser/FFmpeg lock. Never use unbounded npx/latest, install optional sibling skills, send feedback, launch a desktop app or buy cloud/voice/image services by default. Only these four selected leaves may activate; others are references to inspect for a separate explicit need.\n\n'+ROUTING
 elif id=='P226':
  # Fix only the actual monorepo router's malformed sibling coordinate.
  s=s.replace('(./remotion-', '(../remotion-')
  s=s.replace('npx create-video@latest','npx --yes create-video@4.0.540')
  s=s.replace('npx remotion','./node_modules/.bin/remotion')
  if name=='remotion-best-practices':
   s=change(s,"Don't render the video by default unless they are very explicit. They want to instead see an interactive preview.",'Produce the requested deliverable. A make/create/build video request normally includes its final rendered artifact; a preview-only request ends at the interactive preview.')
   s=change(s,'Only render if the user is very explicit in asking for it.','Render the finished video when that is the requested artifact, after actual checks. No extra confirmation is needed for an already authorized output.')
  if name=='remotion-create':
   s=change(s,'The video creation process has finished.','Continue until the requested final video or preview is finished. Preserve editable sources and use the bundled version-matched render browser.')
   s=s.replace('npm i\n', 'npm install --package-lock-only\n# Verify all Remotion package versions are exactly4.0.540, then npm ci from the reviewed lock.\nnpm ci\n')
  s+='\n## Version and artifact acceptance\n\nThis source leaf is4.0.540. Resolve create-video and all Remotion packages to exactly4.0.540 with artifact integrity and a saved dependency lock before execution; do not mix package versions or use @latest. Preserve existing project edits and its incumbent stack. Check installed help and use the version-matched bundled rendering browser. Produce the requested final artifact after frame/layout/audio checks, keep editable JSX/assets and reopen the final export.\n\n'+ROUTING
 elif id=='P224':
  # The manifest selects expertise references, explicitly not whole orchestration.
  pipeline=out/'references/pipeline.md';pipeline.write_text(scope_pipeline(pipeline.read_text(),spec))
  sound=out/'references/sound-design.md';text=sound.read_text()
  text=change(text,'新制作与换音统一从 **Freesound** 搜索、下载，操作见 [sfx-sourcing.md](sfx-sourcing.md)。','优先沿用用户指定的音频；按任务选择许可清楚的实录、素材或程序化声音，不强制使用某个平台。')
  for name in ('sfx-sourcing','final-review'):
   url=f'https://github.com/{spec["source_repository"]}/blob/{spec["revision"]}/references/{name}.md'
   text=text.replace(f']({name}.md)',f']({url})')
   file=out/'references'/f'{name}.md'
   if file.exists():file.unlink()
  sound.write_text('> Scoped reference: keep cue/manifest and audition methods. Fixed renderer, multi-agent, brand and stock-provider assumptions do not control this task. User-supplied audio wins; do not fetch, publish or activate a workflow from a reference.\n\n'+text)
  s='''---
name: video-shotcraft
description: Shot planning, beat alignment and sound-design expertise for a requested editable video or audio revision. Use only the selected local references; whole upstream orchestration, workbench, publication and brand templates are not installed.
---

# Shot and sound craft

Route from the supplied brief and incumbent project. Use [pipeline methods](references/pipeline.md) as a read-only reference for the relevant production phase, [sound design](references/sound-design.md) for cue manifests and audition, and [beat alignment](references/music-beat-sync.md) for music-driven work. Choose routine reversible creative details; no compulsory mode confirmation, workbench launch, showcase promotion or publish step applies. The references do not grant external actions, model choices, parallel workers or paid services.

Record cue event/frame, material and edit intent, with exact frame rate and origin. User-supplied audio wins. Use rights-cleared real foley for recognizable physical actions, or a designed bank family for repeatable UI/game motifs. Rank candidates by acoustic description and contrasts, then blind/level-match them in context. Short-source LUFS alone does not establish a loudness match. Keep voice/music/SFX separately revisable; check masking, actual program loudness and peak against the delivery spec.

Decode the actual master or capture the actual gameplay with audio, measure event offsets, and preserve cue sheet, take/seed/source and license receipts. Sound reference links to sourcing/final-review remain exact pinned upstream links, not extra installed leaves. No production sender, upload API or social publication route is installed.

'''+ROUTING
 elif id=='P238':
  s=re.sub(r'(?m)^description:.*$', 'description: First-pass speech-heavy video/audio cuts or an editable timeline with auto-editor. Recording or microphone capture activates only when explicitly requested; editing an existing file does not authorize capture.',s)
  s=change(s,'## Record and edit a microphone','## Record only when explicitly requested\n\nSkip this section for existing media. Do not start any microphone capture unless recording is part of the user\'s request. Use only the authorized input device and duration.')
  s+='\n## Non-destructive cut acceptance\n\nPreserve originals. Start an isolated trial with --margin 0.2s, preview the removed segments with the installed version\'s inverted-edit option, and check clipped words/meaning before accepting cuts. Export an editable timeline when requested and reopen it with target timing. Record exact CLI/runtime version, input hash, keep/remove intervals and output hash. An analysis completion is not an accepted edit.\n'
 else:raise ValueError('Media leaf is not mapped')
 p.write_text(s)
