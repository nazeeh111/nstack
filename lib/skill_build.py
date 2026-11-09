"""Reviewed per-leaf transformations. Unimplemented adaptations fail closed."""
import pathlib,re,shutil,json,hashlib
P=pathlib.Path

def replace(text,old,new):
 if old not in text:raise ValueError('Pinned patch anchor missing: '+old[:75])
 return text.replace(old,new)

def patch_p001(out,name):
 p=out/'SKILL.md';text=p.read_text()
 if name=='diagnosing-bugs':
  start=text.index('Stop and say so explicitly.');end=text.index('\n### Completion criterion',start)
  text=text[:start]+('Document attempted reproductions and the unavailable observation. Continue with source-backed hypotheses, redacted traces, or runnable subfixtures. Distinguish local evidence from an unobserved production symptom. Ask for missing access only when necessary for dependent work.\n')+text[end:]
  text=replace(text,'If you catch yourself reading code to build a theory before this command exists, **stop: jumping straight to a hypothesis is the exact failure this skill prevents.** No red-capable command, no Phase 2.','Prefer a red-capable symptom check. If the actual environment is unavailable, proceed using explicitly bounded source evidence or a runnable subfixture; do not claim the production symptom was reproduced.')
  text=replace(text,'Do not proceed until you have reproduced **and** minimised.','Minimise the observed failure where possible. If only a subfixture or source trace is available, record that limitation and continue the corresponding bounded investigation.')
 elif name=='tdd':
  start=text.index('**Test only at pre-agreed seams.**');end=text.index('\nWhen the shape',start)
  text=text[:start]+('Infer the existing public contracts and choose tests at the boundaries that cover the requested behavior. Record what each proposed test catches and misses. Ask the user only when unresolved product semantics materially change the deliverable.\n')+text[end:]
  text=replace(text,'call the Skill tool with "codebase-design"','consult the reviewed codebase-design reference if this task merits it')
 elif name=='codebase-design':
  text=replace(text,'Use these terms exactly: don\'t substitute "component," "service," "API," or "boundary." Consistent language is the whole point.','Map these terms to the project\'s existing vocabulary. Use component, service, API or boundary where that is clearer for the current codebase.')
  text=replace(text,'spin up parallel sub-agents to design the interface several radically different ways, then compare on depth, locality, and seam placement.','compare competing interface designs when the tradeoffs justify the work. Use delegation only within the user\'s authorized scope.')
  deep=out/'DEEPENING.md'
  if deep.exists():
   old=deep.read_text();old=re.sub(r'(?m)^.*Old unit tests.*$', 'Retire existing internal tests only after demonstrating behavior parity and a discriminating replacement. Retain public, safety and compatibility probes where they cover behavior the replacement does not.', old);deep.write_text(old)
  text=re.sub(r'_Avoid_:[^\n]+','Use the project vocabulary where clearer.',text)
  text=re.sub(r'(?m)^- \*\*\"Boundary\"\*\*:.*$', '- Use boundary consistently with the project vocabulary, including domain boundaries where relevant.',text)
 else:raise ValueError('Unreviewed P001 leaf')
 p.write_text(text)

def materialize(source,out,s,c,m,support=None,_inside=False):
 path=P(s['source_path']);name=path.parent.name
 from patch_native34 import handles,materialize as native34
 if handles(s):return native34(source,out,s,c)
 if s['candidate_id']=='P333':
  from patch_office import materialize as office_pack
  return office_pack(source,out,s,c)
 from closure import needs, support as mirror_support, validate
 if needs(s) and not _inside:
  entry=out/path.parent;entry.mkdir(parents=True,exist_ok=True)
  materialize(source,entry,s,c,m,support,True)
  def selected_support(rel,dest):
   selected=next((x for x in m['skills'] if x['candidate_id']==s['candidate_id'] and x['source_repository']==s['source_repository'] and x['revision']==s['revision'] and x['source_path']==rel and x['delivery'] in ('intact upstream leaf','narrow-patched leaf')),None)
   if selected is None:return False
   dest.mkdir(parents=True,exist_ok=True);materialize(source,dest,selected,c,m,support,True);return True
  if s['candidate_id']=='P094':
   import os
   from closure import links
   for file in entry.rglob('*.md'):
    for rel in list(links(file)):
     old_target=(file.parent/rel).resolve()
     if old_target.is_relative_to(out.resolve()) and not old_target.exists():
      missing=old_target.relative_to(out.resolve())
      if missing.parts and missing.parts[0].startswith('n8n-') and (source/'skills'/missing).exists():
       replacement=os.path.relpath(out/'skills'/missing,file.parent)
       file.write_text(file.read_text().replace(']('+rel,']('+replacement))
  if s['candidate_id'] in ('X-CREATIVE-BLENDER-SKILLS','X-CREATIVE-UNREAL'):
   core='skills/dcc/blender/scenario-blender-expert/SKILL.md' if s['candidate_id']=='X-CREATIVE-BLENDER-SKILLS' else 'skills/game-engines/unreal/scenario-unreal-expert/SKILL.md'
   if not (out/core).exists():selected_support(core,out/P(core).parent)
  if s['candidate_id']=='P321':
   for core in ('kicad','datasheets'):
    rel='skills/'+core+'/SKILL.md'
    if not (out/rel).exists():selected_support(rel,out/P(rel).parent)
  mirror_support(source,out,selected_support,{'runtime/career-ops':'.'} if s['candidate_id']=='P354' else None);validate(out)
  return str(path.parent)
 if s['candidate_id']=='P343' and name in ('prospecting','cold-email'):
  from patch_prospecting import materialize as scoped
  return scoped(source,out,s)
 if s['delivery']=='narrow-patched leaf' and not ((s['candidate_id']=='P001' and name in ('diagnosing-bugs','tdd','codebase-design')) or s['candidate_id'] in ('P112','P119') or s['candidate_id'] in ('P343','P347','P351','P354','P357','L036','X-AUTO-EVE','X-CREATIVE-BLENDER-SKILLS','X-CREATIVE-UNREAL','L006','L014','L020','L050','P183','P321','P094','P215','P226','P224','P238') or s['candidate_id'] in ('P200','P328','P403','X-CREATIVE-COLORFIGURES','X-CREATIVE-ARCHIFY') or s['candidate_id']=='P195' or s['candidate_id']=='P150' or s['candidate_id'] in ('P007','P016','P037','L010','P008','P011','P013','P028','P062','P064','P066','P068','P083')):raise ValueError('Required narrow patch not yet commissioned: '+s['candidate_id']+'/'+name)
 folder=source/path.parent
 for f in folder.rglob('*'):
  # This root-level source is explicitly a three-reference expertise port,
  # not the upstream workbench, provider tooling or translated orchestration.
  if s['candidate_id']=='P224' and str(f.relative_to(folder)) not in ('SKILL.md','references/pipeline.md','references/sound-design.md','references/music-beat-sync.md'):continue
  if f.is_symlink():raise ValueError('Source closure symlink needs explicit review')
  if f.is_file():
   if f.name=='SKILL.md' and f!=folder/'SKILL.md':raise ValueError('Unexpected sibling skill in closure')
   if f.name=='.nstack-source.json' or any(x in f.parts for x in ('.git','node_modules','__pycache__')):continue
   target=out/f.relative_to(folder);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target)
 notices=[f.name for f in out.iterdir() if f.is_file() and f.name.upper().startswith(('LICENSE','COPYING','NOTICE'))]
 # Retain notices from the selected leaf's owning ancestor chain, never unrelated siblings.
 ancestors=[];current=folder
 while current.is_relative_to(source):
  ancestors.append(current)
  if current==source:break
  current=current.parent
 for ancestor in ancestors:
  for pattern in ('LICENSE*','COPYING*','NOTICE*'):
   for f in ancestor.glob(pattern):
    if not f.is_file():continue
    target=out/f.name
    if target.exists() and target.read_bytes()!=f.read_bytes():
     origin=str(f.relative_to(source)).replace('/','-');target=out/('ANCESTOR-'+origin)
    if not target.exists():shutil.copy2(f,target)
    notices.append(target.name)
 if not notices and s['candidate_id']=='P019':
  # Exact upstream SPDX declaration, not an inferred sibling grant.
  readme=source/'README.md';decl=readme.read_text()
  if not re.search(r'(?m)^## License\s*\n\s*MIT\s*$',decl) or not re.search(r'(?m)^license: MIT$',(source/path).read_text()):raise ValueError('Pinned explicit MIT declaration changed')
  terms=(P(__file__).resolve().parents[1]/'LICENSE').read_text().split('Permission is hereby granted',1)[1]
  (out/'LICENSE-UPSTREAM-MIT.txt').write_text('Upstream explicitly declares MIT in README.md and this leaf frontmatter at '+s['revision']+'. Existing notices in source files remain retained. No copyright holder/year has been invented.\n\nPermission is hereby granted'+terms)
  (out/'SOURCE-LICENSE-DECLARATION.json').write_text(json.dumps({'source_repository':s['source_repository'],'revision':s['revision'],'declaration_path':'README.md','declaration_sha256':hashlib.sha256(readme.read_bytes()).hexdigest(),'leaf_path':s['source_path'],'leaf_license':'MIT'},indent=2)+'\n');notices=['LICENSE-UPSTREAM-MIT.txt']
 if not notices:raise ValueError('No retained upstream license; establish rights before building')
 if 'Apache-2.0' in s.get('rights','') and not any('Apache License' in (out/name).read_text(errors='replace') for name in notices):
  shutil.copy2(P(__file__).resolve().parents[1]/'licenses/Apache-2.0.txt',out/'LICENSE-APACHE-2.0.txt')
 if s['candidate_id']=='P001' and name=='codebase-design':
  refs=[r for r in m['skills'] if r['candidate_id']=='P001' and r['delivery']=='selective-merge reference']
  ref=refs[0];origin=(support or {}).get(ref['source_repository'])
  if origin is None:raise ValueError('P001 requires the named pinned Caldo diagnostic source')
  original=(origin/ref['source_path']).read_text();start=original.index('**2. List every problem**');end=original.index('**4. Fix everything on the list**');log=original[original.index('<a id="decision-log-example"></a>'):]
  folder=out/'references';folder.mkdir(exist_ok=True)
  diagnostic='# Caldo coupling diagnostic reference\n\nSource: '+ref['source_url']+'\n\nUse this inventory and decision log only where coupling or co-change matters. This is read-only diagnostic material, not permission to run the original whole-codebase refactor. Git co-change nominates candidates; confirm actual callers with P028, structural patterns with P053, and use the appropriate security checks. Review the inventory before editing, then make bounded changes with behavior-preserving tests.\n\n'+original[start:end]+log
  (folder/'caldo-coupling.md').write_text(diagnostic);shutil.copy2(origin/'LICENSE',folder/'CALDO-LICENSE')
  (out/'SKILL.md').write_text((out/'SKILL.md').read_text()+'\n\nWhen a coupling or co-change question merits it, consult [Caldo’s diagnostic inventory and decision log](references/caldo-coupling.md). It is a reference, not a second executable refactor workflow.\n')
  (folder/'caldo-source.json').write_text(json.dumps({k:ref[k] for k in ['candidate_id','source_repository','revision','source_path','rights']},indent=2)+'\n')
 if s['delivery']=='narrow-patched leaf':
  if s['candidate_id']=='P001':patch_p001(out,name)
  elif s['candidate_id']=='P112':
   if name=='scientific-visualization':patch_scientific_visualization(out)
   if name=='paper-lookup':
    from patch_paper_lookup import patch
    patch(out)
   else:
    from patch_science import patch
    patch(out,name)
  elif s['candidate_id'] in ('P007','P016','P037','L010'):
   from patch_lightweight import patch
   patch(s['candidate_id'],name,source,out)
  elif s['candidate_id'] in ('P008','P011','P013'):
   from patch_workflows import patch
   patch(s['candidate_id'],name,source,out)
  elif s['candidate_id'] in ('P028','P062','P064','P066','P068','P083'):
   from patch_interfaces import patch
   patch(s['candidate_id'],name,source,out)
  elif s['candidate_id']=='P183' or (s['candidate_id']=='P195' and name in ('property-based-testing','fp-check','codeql')):
   from patch_data_checks import patch
   patch(s['candidate_id'],name,source,out)
  elif s['candidate_id']=='P195':
   from patch_security import patch
   patch(name,source,out)
  elif s['candidate_id']=='P119':
   from patch_research import patch
   patch(name,out)
  elif s['candidate_id'] in ('P200','P328','P403','X-CREATIVE-COLORFIGURES','X-CREATIVE-ARCHIFY'):
   from patch_visuals import patch
   patch(s['candidate_id'],source,out)
  elif s['candidate_id']=='P094':
   p=out/'SKILL.md';text=p.read_text();text=re.sub(r'(?m)^- Average:.*$', '- Timing is task-dependent; measure the actual fixture.',text);text=re.sub(r'\b(?:23|58)(?:s| seconds?)\b','task-dependent time',text);text+='\n\n## nstack runtime acceptance\n\nKeep credentials in the platform credential mechanism; test with isolated fixture credentials and authorized endpoints. After every update, call n8n_get_workflow and inspect live schema and connection readback. validate_workflow establishes structure only. Execute the isolated fixture and read the actual business effect and output fields, including a structurally valid miswired negative control. A pinned workflow may still invoke mutable external nodes; record their actual versions and observation date. Telemetry-derived example timings are observations, not performance expectations. No external side effect follows from validation alone.\n';p.write_text(text)
  elif s['candidate_id'] in ('P215','P226','P224','P238'):
   from patch_media import patch
   patch(s['candidate_id'],name,s,out)
  elif s['candidate_id']=='P321':
   from patch_hardware import patch
   patch(name,source,out)
  elif s['candidate_id'] in ('L006','L014','L020','L050'):
   from patch_host_skills import patch
   patch(s['candidate_id'],name,out)
  elif s['candidate_id'] in ('X-CREATIVE-BLENDER-SKILLS','X-CREATIVE-UNREAL'):
   from patch_dcc import patch
   patch(s['candidate_id'],name,out)
  elif s['candidate_id'] in ('L036','X-AUTO-EVE'):
   from patch_conditional import patch
   patch(s['candidate_id'],out)
  elif s['candidate_id'] in ('P343','P347','P351','P354','P357'):
   from patch_business import patch
   patch(s['candidate_id'],name,source,out)
  elif s['candidate_id']=='P150':
   if name=='train-sentence-transformers':
    from patch_training import patch
    patch(out,P(__file__).parent)
    from patch_hf import SPLIT
    (out/'SKILL.md').write_text((out/'SKILL.md').read_text()+'\n'+SPLIT)
   else:
    from patch_hf import patch
    patch(name,out)
 if s['candidate_id']=='P019' and (out/'AGENTS.md').exists():
  # Preserve the intact aggregate's relative rule links via byte-identical support copies.
  from closure import links
  for rel in links(out/'AGENTS.md'):
   target=(out/rel).resolve()
   if target.is_relative_to(out.resolve()) and not target.exists() and P(rel).name==rel.removeprefix('./') and (out/'rules'/P(rel).name).is_file():
    shutil.copy2(out/'rules'/P(rel).name,target)
 skill=out/'SKILL.md';text=skill.read_text()
 if not text.startswith('---\n'):raise ValueError('Skill has no frontmatter')
 text=re.sub(r'(?m)^name:.*$', 'name: '+s['candidate_id'].lower()+'-'+re.sub(r'[^a-z0-9-]+','-',(name or s['source_repository'].split('/')[-1]).lower()).strip('-'),text,count=1)
 skill.write_text(text)
 if not _inside:validate(out)


def patch_scientific_visualization(out):
 p=out/'SKILL.md';text=p.read_text();text=replace(text,'## Citing Scientific Agent Skills', '## Upstream attribution')
 # Remove the compulsory paper citation as specified, preserving legal notices separately.
 text=text[:text.index('## Upstream attribution')].rstrip()+'\n'
 text=replace(text,'### 4. Implement with scoped styles', '### 4. Implement with scoped styles\n\nBefore drawing a quantitative claim, apply [the measurement and source-to-render audit](references/nstack-measurement-audit.md).')
 text=text.replace('publication-ready scientific figures','auditable scientific figures')
 text=re.sub(r'(?m)^allowed-tools:.*\n','',text)
 p.write_text(text)
 (out/'references/nstack-measurement-audit.md').write_text("""# Measurement and source-to-render audit

Preserve raw measurements, units, calibration, estimator, fitting interval, excluded bins and transformation code. Use numeric plotting tools for quantitative charts; do not generate raster charts with an image model. Reopen the delivered SVG/PDF and compare the encoded series with the accepted numeric arrays. Hash source arrays, figure inputs and final exports and bind them in one manifest. Change a known input and regenerate every affected numeric output and figure; reject stale dependency hashes.

For simulation-derived figures, the selected solver remains responsible for physics. The upstream bend plot/export helper is a demo/export step. Record geometry and units, source/monitor locations, signed port and normalization spectra, reference/run IDs and exact transforms. Check analytic/reference cases, convergence, weak or zero incident bins, and points outside plotted limits before drawing. State which powers were measured. Label 1-R-T as unaccounted unless monitored ports, losses and model assumptions establish an absorption interpretation. A successful exporter or attractive chart does not validate a physical model.

For room decay, state sample rate, signal units, direct-path or noise exclusions, fitting interval, dB definition and estimator uncertainty. Compare a known synthetic exponential against an independent analytic decay time. A physical room claim additionally requires measurement calibration and a suitable sound field.
""")
