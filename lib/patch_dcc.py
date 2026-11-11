"""Independent per-leaf DCC ports, preserving exact helpers and authored asset sources."""
import pathlib,re,shutil
P=pathlib.Path

def patch(id,name,out):
 p=out/'SKILL.md';s=p.read_text()
 # Remove the exact upstream on-missing-sibling fetch/install policy, across wrapped variants.
 s=re.sub(r'If a sibling skill.*?flag\s+the gap\.', 'Resolve only the siblings selected for this task from the local nstack registry. If none is eligible, use the native application API and report the unsupported technique; do not fetch Scenario MCP or install a collection.',s,flags=re.S|re.I,count=1)
 if id=='X-CREATIVE-BLENDER-SKILLS':
  s+='\nResolve the actual Blender executable/version before using version-specific bpy helpers. Use the existing native application interface; no Scenario service is installed by this port.\n'

 else:
  s=re.sub(r'(?m)^description:.*$', 'description: Version-checked native Unreal project or cinematic work using the actual installed engine and selected local technique helpers. Preserve C++/Blueprint gameplay; no global Scenario service or fixed Mac engine path is assumed.',s)
  s=s.replace('Target: UE 5.8 on macOS Apple Silicon.','Source reference target: UE5.8/macOS Apple Silicon; resolve and verify the actual requested target before use.')
  s=s.replace('tests/code/unreal-cinematics/job_00_probe_cine.py','scripts/nstack_two_shot_probe.py')
  s+='\nUse the explicit version-checked engine root and .uproject with the existing native application interface. Missing upstream probe paths below bind to the retained local helper; an offline helper check is not an editor/render pass.\n'
  if name=='scenario-unreal-cinematics':shutil.copy2(P(__file__).parent/'unreal_two_shot_probe.py',out/'scripts/nstack_two_shot_probe.py')
 p.write_text(s)
 if id=='X-CREATIVE-UNREAL':
  for file in out.rglob('*.md'):
   text=file.read_text()
   text=text.replace('tests/code/unreal-animation/run_all.py --offline','delivered local offline helper checks (not an editor pass)')
   text=text.replace('job_00_anim_probe.py','scripts/nstack_animation_probe.py')
   text=text.replace('tests/code/unreal-pipeline-automation/in_engine/run_in_unreal.py','the actual project import/validator fixture using scripts/ue_pipeline.py; upstream test file is absent')
   file.write_text(text)
  if name=='scenario-unreal-animation':
   shutil.copy2(P(__file__).parent/'unreal_animation_probe.py',out/'scripts/nstack_animation_probe.py')
  helper=out/'scripts/ue_pipeline.py'
  if helper.exists():
   text=helper.read_text();start=text.index('    if not eng:',text.index('def _engine'));end=text.index('    return eng',start)
   text=text[:start]+'    if not eng:\n        raise ValueError("Provide explicit version-checked engine or UE_ROOT; no guessed Mac path")\n'+text[end:];helper.write_text(text)
 if id=='X-CREATIVE-BLENDER-SKILLS' and name=='scenario-blender-grease-pencil':
  from patch_gp import patch as patch_gp
  patch_gp(out)
 # Keep every copied helper explicit about the actual engine root, not auto-selected defaults.
 env=out/'scripts/ue_env.py'
 if env.exists():
  t=env.read_text();start=t.index('    patterns = [',t.index('def candidate_roots'));end=t.index('\n    return roots',start)
  t=t[:start]+'''    # nstack: caller supplies the version-checked target root; do not scan/choose another install.
    if not roots:
        raise ValueError("Set UE_ROOT to the explicit version-checked engine root")
'''+t[end:];env.write_text(t)
