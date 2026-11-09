"""Selected media expertise ports; editable source and requested final artifact control."""
import pathlib,re
P=pathlib.Path
ROUTING='''## Source, timing and output contract

The requested editable source controls dispatch: keep React scenes in Remotion, standalone HTML motion in HyperFrames, and native shots/grades/buses in the chosen engine or Resolve/Fusion/Fairlight. Transfer cue IDs, frame rate/origin, stems and asset receipts rather than screenshots alone. Keep a paused timeline registered after fonts/async setup; deterministic renderAt(time) and seeded inputs must reproduce the same frame. Check representative moving frames plus endpoint/blank-frame controls and the final mux. A launch-film aesthetic checker does not validate scientific values or gameplay readability. Keep the last successful artifact until replacement succeeds.
'''
def change(s,old,new):
 if old not in s:raise ValueError('Missing media patch anchor: '+old[:90])
 return s.replace(old,new)
def patch(id,name,spec,out):
 p=out/'SKILL.md';s=p.read_text()
 if id=='P215':
  for file in out.rglob('*.md'):
   text=file.read_text();text=text.replace('npx hyperframes', '"$NSTACK_HYPERFRAMES"')
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
