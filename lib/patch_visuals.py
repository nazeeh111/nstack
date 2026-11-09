"""Reference-led visual ports with brief-specific acceptance and retained editable source."""
import pathlib,re,shutil
P=pathlib.Path

def change(s,old,new):
 if old not in s:raise ValueError('Missing visual patch anchor: '+old[:90])
 return s.replace(old,new)
def patch(id,source,out):
 p=out/'SKILL.md';s=p.read_text()
 if id=='P200':
  s=re.sub(r'description: >-\n(?:  .*\n)+', 'description: Reference-led art direction for a public-facing persuasive or editorial page whose brief explicitly calls for strong visual direction or redesign. Use the supplied brand/reference and retain the complete taste library, scripts and screenshot critique. Ordinary apps, dashboards and bounded fixes stay native.\n',s,count=1)
  start=s.index('   **The floor, which the inspector checks:**');end=s.index('   `references/imagery.md`',start)
  s=s[:start]+'''   **Brief-specific imagery:** Use rights-cleared photographs, footage, illustrations or actual product output when they help communicate the subject. No fixed picture or motion quota applies. Supplied brand, real assets, accessibility, functional UI and truthful content control; never invent client assets or fill an image quota with unrelated material.

'''+s[end:]
  s=change(s,'saves screenshots to `.taste-skill/inspect/`. Fix every `FAIL`. Treat each `WARN` as wrong unless you can defend it to a\ndesigner in one sentence. Re-run until there are no `FAIL`s. Do not argue with the meter and do not\nhide things from it.','saves screenshots to `.taste-skill/inspect/`. Repair functional, content, overflow and accessibility failures. Treat aesthetic FAIL/WARN outputs as brief-dependent evidence; document a supplied-brand or functional reason for any inapplicable house rule. Do not hide defects from the inspector.')
  s=change(s,'## House rules','## House rules as examples\n\nThe supplied design system and references control. These are source examples, not universal bans on fonts, palettes, gradients, borders, layout or motion. Use --keep palette,type when specified and record a fixed seed for a meaningful direction comparison.')
  s=s.replace('`inspect.mjs` shows **0 FAIL** at 1440, 768 and 390, on the final version of the page.','Inspect the actual final page at relevant viewports; resolve material defects and report which aesthetic checks were inapplicable to the brief.')
  s+='\nPreserve the designed project and current-source screenshot evidence. App-screen routing above is reference material for an explicit matching art-direction task; it does not make this a default dashboard or application skill.\n'
 elif id=='P328':
  start=s.index('## 0. First-time setup');end=s.index('## 1. Philosophy',start)
  s=s[:start]+'''## 0. Project style

Read supplied references and project tokens. Resolve an existing profile when applicable; otherwise choose readable defaults appropriate to the subject and proceed. A first diagram does not require style onboarding or a user confirmation. Never overwrite the installed immutable source to save a client profile; keep authorized profile edits in the owning project.

'''+s[end:]
  start=s.index('### Confirm before drawing');end=s.index('\n---',start)
  s=s[:start]+'''### Proceed from the brief

State the chosen semantic pattern, visual type and material scope assumptions briefly. Proceed when the brief is sufficient; ask only for missing information that changes the result. Keep type references, semantic relationships and geometry checks.
'''+s[end:]
  s=s.replace('never JetBrains Mono','use the project font when supplied').replace('and never JetBrains Mono','and the project font remains controlling')
  s=s.replace('14 characters max, all caps, centered on its segment','brief, readable and centered on its segment; case follows the project')
  s=change(s,'## 4. Universal Anti-patterns','## 4. Reference anti-patterns\n\nUse the relevant diagram type and project identity. Font bans, universal all-caps labels and type-specific anatomy assumptions do not override the brief. Preserve semantic correctness, legibility and actual connector/geometry constraints.')
  scripts=out/'scripts';scripts.mkdir(exist_ok=True)
  src=source/'scripts/verify-geometry.py'
  if not src.is_file():raise ValueError('Pinned diagram geometry helper is absent')
  shutil.copy2(src,scripts/src.name)
  s=s.replace('<repo-root>/scripts/verify-geometry.py','<skill-root>/scripts/verify-geometry.py')
 elif id=='P403':
  s=change(s,'https://unpkg.com/@antv/infographic@latest/dist/infographic.min.js','./vendor/infographic-0.2.20.min.js')
  s+='\n\n## Reproducible local renderer\n\nThe reviewed source package is @antv/infographic0.2.20 at commit5ae0d9394ac6280cb688eb4b4345881e291b9209. Commission its exact compatible immutable package/bundle and dependency integrity before rendering; retain the lock and MIT notice. Copy the verified local bundle to the referenced vendor path and use local rights-cleared icons/fonts/assets. No unpkg/latest or implicit remote font/icon fetch is a reproducible offline artifact. Retain the original DSL, editable HTML/SVG export and source data. Reopen the actual export and independently reconcile labels, values and units.\n'
 elif id=='X-CREATIVE-COLORFIGURES':
  s=re.sub(r'(?m)^description:.*$', 'description: Create an editable offline interactive mechanism, cutaway or object explanation with inspectable parts and meaningful actions. Use for operate/how-it-works requests; ordinary static diagrams and decorative pictures use simpler native routes.',s)
  s=change(s,'fix — at most 2 rounds.','fix observed defects until the requested verification passes or a concrete blocker is reported.')
  s=change(s,'## Verify before you finish (keep it light: at most 2 rounds)','## Verify the current interactive artifact')
  s=change(s,'Do **at most two rounds** of shoot → fix. Each round is just:','Use bounded shoot → fix checks driven by observed defects. Do not stop at two rounds while required verification still fails. Each useful pass includes:')
  s=change(s,'Fix what you find, do the second round only if the first found something, then build and hand over. Skip palette\nchecks, long screenshot series and extra test runs.','Fix material defects, rerender affected states, and deliver when the requested checks pass or with a precise remaining blocker. Expand only where changes or failures justify it.')
  s+='\n## Accessible state and controls\n\nProvide a readable text description of the mechanism, parts and current state. Name controls and expose meaningful state changes to assistive technology. Check keyboard operation, visible focus and a sensible out-of-order action. Color is a secondary cue. Keep editable HTML/JS, source assets, deterministic input/action sequence and reopened output together.\n'
 elif id=='X-CREATIVE-ARCHIFY':
  s=change(s,'## Update awareness','## Pinned release and updates')
  start=s.index('`finalize` and standalone `deliver` include `update`');end=s.index('\n\n',start)
  s=s[:start]+'''Set `ARCHIFY_UPDATE_CHECK_DISABLED=1` for reproducible jobs; the pinned runtime supports this without networking or reminder-state writes. Do not promote updates or change the release during a task. A newly discovered update becomes a separate reviewed release delta.'''+s[end:]
  s=s.replace('A page made on request ends its reply with the one-line mode offer under Output.','Use the requested output and concise delivery; no mode promotion is required.')
  s=s.replace('Keep the required update notice under Update awareness.','Report material limits without unsolicited update promotion.')
  start=s.find('After an explainer made on request,')
  if start>=0:s=s[:start].rstrip()+'\n'
  s+='\n## Actual visual review\n\nPrefer the explicitly requested output location. Keep schemas, validators, editable IR and the complete native finalize pipeline with receipts. When readability matters, inspect a representative actual rendered shot from the current successful export after browser checks. Browser-check without perceptual inspection remains labeled as such. Screenshot automation cannot establish source semantics. Keep prior valid artifacts until replacement succeeds.\n'
 else:raise ValueError('Unmapped visual leaf')
 p.write_text(s)
