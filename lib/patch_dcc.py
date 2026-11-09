"""Independent per-leaf DCC ports, preserving exact helpers and authored asset sources."""
import pathlib,re,shutil
P=pathlib.Path

def patch(id,name,out):
 p=out/'SKILL.md';s=p.read_text()
 # Remove the exact upstream on-missing-sibling fetch/install policy, across wrapped variants.
 s=re.sub(r'If a sibling skill.*?flag\s+the gap\.', 'Resolve only the siblings selected for this task from the local nstack registry. If none is eligible, use the native application API and report the unsupported technique; do not fetch Scenario MCP or install a collection.',s,flags=re.S|re.I,count=1)
 if id=='X-CREATIVE-BLENDER-SKILLS':
  s+='''\n## Exact target and delivery

Resolve the actual project-specific Blender executable, OS/version and add-on state. Use direct background bpy by default; live GUI/bridge work requires that explicit interaction need. Keep each selected technique leaf distinct with its original references and helper signatures; no Scenario service or paid generation is installed by this port. Source5.2 claims are source reports, not evidence that another target supports them. Inspect the target API and run its representative check before relying on a helper. Aesthetic thresholds are guides tied to the actual brief and art direction.

Retain editable .blend plus requested GLB. At the user's actual frame rate, verify first/last sampler time, target-engine duration/playback, node/material mapping, bounds/scale, animation endpoints and cue/event timing. For a game, verify input -> state -> visible/audio consequence, restart and actual device output. Rigged/textured/lit shots also require deformation/color and a rendered frame. Reopen the actual exported file in its target; an internal audit or Python exit code alone is insufficient.
'''
 else:
  s=re.sub(r'(?m)^description:.*$', 'description: Version-checked native Unreal project or cinematic work using the actual installed engine and selected local technique helpers. Preserve C++/Blueprint gameplay; no global Scenario service or fixed Mac engine path is assumed.',s)
  s=s.replace('Target: UE 5.8 on macOS Apple Silicon.','Source reference target: UE5.8/macOS Apple Silicon; resolve and verify the actual requested target before use.')
  s=s.replace('tests/code/unreal-cinematics/job_00_probe_cine.py','scripts/nstack_two_shot_probe.py')
  s+='''\n## Target commissioning

Resolve the explicit engine root, Build.version, executable, OS and .uproject. Pass the exact target to helpers; do not choose a version by directory recency or reuse a hardcoded Mac path. Source5.8 API examples need actual target verification. Keep optional official local toolsets conditional and preserve native C++/Blueprint logic. Apply lighting/HDR guidance to the brief, not a universal aesthetic score.

In a disposable owned project, use the two-shot probe where supplied to create two sequences/cameras and read back queued job identity/status. Check actual render callbacks in the installed engine before automated rendering. Queue completion, written-frame manifests, missing-asset negative controls and decoded first/last frames are independent acceptance gates; an offline fake-Unreal test is not an engine pass.
'''
  if name=='scenario-unreal-cinematics':shutil.copy2(P(__file__).parent/'unreal_two_shot_probe.py',out/'scripts/nstack_two_shot_probe.py')
 p.write_text(s)
 # Keep every copied helper explicit about the actual engine root, not auto-selected defaults.
 env=out/'scripts/ue_env.py'
 if env.exists():
  t=env.read_text();start=t.index('    patterns = [',t.index('def candidate_roots'));end=t.index('\n    return roots',start)
  t=t[:start]+'''    # nstack: caller supplies the version-checked target root; do not scan/choose another install.
    if not roots:
        raise ValueError("Set UE_ROOT to the explicit version-checked engine root")
'''+t[end:];env.write_text(t)
