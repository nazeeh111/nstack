"""Pinned P283 game methods/support closure; no game, model or framework launch."""
import hashlib
import json
import os
import pathlib
import re
import shutil
import sys
import tempfile
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'lib')]
from closure import links,validate
from patch_game import REPOSITORY,REVISION,SUPPORT,FRAMEWORK,materialize as game_materialize
from skill_build import materialize

SOURCE=pathlib.Path(os.environ.get('NSTACK_GAME_SOURCE',pathlib.Path.home()/'Library/Application Support/nstack/sources/Donchitos--Claude-Code-Game-Studios'/REVISION))
SHA=lambda data:hashlib.sha256(data).hexdigest()


def fenced(text,language):
 return re.findall(r'```'+language+r'\n(.*?)\n```',text,re.S)


class GameNative(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if not (SOURCE/'.nstack-source.json').is_file():raise unittest.SkipTest('Exact offline game source unavailable; no fetch')
  cls.registry=json.loads((ROOT/'registry/manifest.json').read_text());cls.component=next(c for c in cls.registry['components'] if c['id']=='P283')
  cls.specs=[s for s in cls.registry['skills'] if s['candidate_id']=='P283' and s['delivery']=='narrow-patched leaf']
  cls.temp=tempfile.TemporaryDirectory(prefix='nstack-game-native-');cls.addClassCleanup(cls.temp.cleanup);cls.base=pathlib.Path(cls.temp.name);cls.outputs={}
  for spec in cls.specs:
   out=cls.base/spec['native_name'];out.mkdir();entry=materialize(SOURCE,out,spec,cls.component,cls.registry);cls.outputs[spec['native_name']]=(out,out/entry/'SKILL.md',spec)

 def test_each_selected_skill_closes_real_support_and_only_one_discoverable_entry(self):
  self.assertEqual(len(self.outputs),3)
  for name,(out,entry,spec) in self.outputs.items():
   validate(out)
   self.assertEqual(len(list(out.rglob('SKILL.md'))),1)
   for rel in SUPPORT:self.assertTrue((out/'source'/rel).is_file(),(name,rel))
   for file in (out/'source').rglob('*.md'):
    for target in links(file):
     resolved=(file.parent/target).resolve();self.assertTrue(resolved.is_relative_to(out.resolve()) and resolved.exists(),(file,target))
   # The role methods are reachable through the mandatory native support map,
   # not merely preserved in an inert archive.
   mapping=(out/'source/.claude/docs/native-execution.md').read_text()
   for role in ['art-director','technical-artist','ux-designer','creative-director']:
    self.assertIn('.claude/agents/'+role+'.md',mapping)
   self.assertIn('../../docs/native-execution.md',entry.read_text())

 def test_art_bible_retains_all_nine_sections_and_craft_questions(self):
  out,entry,spec=self.outputs['game-art-bible'];active=entry.read_text();original=(SOURCE/spec['source_path']).read_text()
  headings=re.findall(r'^### Section \d+: .+$',original,re.M)
  self.assertEqual(len(headings),8)  # Section 9 is the Phase 4 heading upstream.
  for heading in headings:self.assertIn(heading,active)
  self.assertIn('## Phase 4: Reference Direction (Section 9)',active)
  for marker in ['one-line visual rule plus 2–3 supporting principles','Character silhouette philosophy','Colorblind safety','Prop density','prop density','each shape principle','mutually consistent','legible against each other','engine-specific hard constraints']:
   # Source capitalisation varies; preserve each substantive concept.
   self.assertIn(marker.lower(),active.lower())
  template=(out/'source/.claude/docs/templates/art-bible.md').read_text()
  self.assertEqual(re.findall(r'^## \d+\. .+$',template,re.M),re.findall(r'^## \d+\. .+$',(SOURCE/'.claude/docs/templates/art-bible.md').read_text(),re.M))
  self.assertIn('Only work on sections with Status: Empty or Placeholder',active)

 def test_asset_spec_keeps_inventory_spec_manifest_ids_and_shared_asset_protocol(self):
  out,entry,spec=self.outputs['game-asset-spec'];active=entry.read_text();original=(SOURCE/spec['source_path']).read_text()
  self.assertEqual(fenced(active,'markdown'),fenced(original,'markdown'))
  for marker in ['## Asset ID Assignment','## Shared Asset Protocol','ASSET-[highest + 1]','reference the existing ASSET-ID','## Error Recovery Protocol','Always produce a partial spec','engine-specific constraints','exact dimensions or polycount','Audio (SFX, music — descriptions only, no generation prompts)']:
   self.assertIn(marker,active)

 def test_playtest_template_is_exact_and_observation_routes_remain_distinct(self):
  out,entry,spec=self.outputs['game-playtest-report'];active=entry.read_text();original=(SOURCE/spec['source_path']).read_text()
  self.assertEqual(fenced(active,'markdown'),fenced(original,'markdown'))
  for marker in ['## Phase 2B: Analyze Mode','## Phase 3: Action Routing','Design changes needed','Balance adjustments','Bug reports','Polish items','Bugs\nEncountered','Pain points are for how the game feels to play','No pillars available — assess against the hypothesis alone','NOT ASSESSED']:
   self.assertIn(marker,active)
  self.assertIn('blank template output; nothing saved',active)
  self.assertIn('trace the affected design references before changing them',active)

 def test_roles_and_review_checklists_keep_their_domain_method(self):
  for out,entry,spec in self.outputs.values():
   for role,start,end in [('art-director','### Key Responsibilities','## Gate Verdict Format'),('technical-artist','### Key Responsibilities','### What This Agent Must NOT Do'),('ux-designer','### Key Responsibilities','### What This Agent Must NOT Do'),('creative-director','### Vision Articulation Framework','### What This Agent Must NOT Do')]:
    rel='.claude/agents/'+role+'.md';source=(SOURCE/rel).read_text();block=source[source.index(start):source.index(end)].rstrip();block=block.replace('/ux-design accessibility','establish the requested accessibility criteria');active=(out/'source'/rel).read_text();self.assertIn(block,active,role)
   for name in ['ad-art-bible','cd-playtest']:
    rel='.claude/docs/director-gates/'+name+'.md';source=(SOURCE/rel).read_text();prompt=source[source.index('**Prompt**:'):];self.assertIn(prompt,(out/'source'/rel).read_text())

 def test_native_callbacks_have_no_foreign_hook_roster_model_or_required_write_gate(self):
  for out,entry,spec in self.outputs.values():
   for file in (out/'source').rglob('*.md'):
    active=file.read_text()
    self.assertNotIn('!`bash',active)
    self.assertNotIn('${CLAUDE_SKILL_DIR}',active)
    self.assertNotIn('via `Agent`',active)
    self.assertNotRegex(active,r'(?m)^(?:model|memory|allowed-tools|tools):')
    self.assertNotIn('do not use Write/Edit until the user has said yes',active)
   native=(out/'source/.claude/docs/native-execution.md').read_text()
   for binding in ['`rg -n`','`rg --files -g`','not a callable agent ID','No framework mode or approval policy overrides','not files that should exist in this skill bundle']:
    # The project-input distinction is in the entry rather than duplicated map.
    self.assertIn(binding,native+entry.read_text())
   self.assertFalse((out/'source/.claude/hooks').exists())
   self.assertFalse((out/'source/project.yaml').exists())

 def test_exact_source_archives_notice_and_current_port_provenance(self):
  receipt=json.loads((SOURCE/'.nstack-source.json').read_text())
  for out,entry,spec in self.outputs.values():
   record=json.loads((out/'NATIVE-ADAPTATION.json').read_text());self.assertEqual(record['revision'],REVISION);self.assertEqual(record['port_sha256'],SHA((ROOT/'lib/patch_game.py').read_bytes()))
   for rel,mod in record['modifications'].items():
    original=(SOURCE/rel).read_bytes();self.assertEqual(SHA(original),receipt['files'][rel]);self.assertEqual((out/mod['archival_original']).read_bytes(),original)
    if mod['active_path']:self.assertEqual(SHA((out/mod['active_path']).read_bytes()),mod['adapted_sha256'])
   self.assertEqual((out/'LICENSE').read_bytes(),(SOURCE/'LICENSE').read_bytes())
   for rel in FRAMEWORK:self.assertIsNone(record['modifications'][rel]['active_path'])

 def test_wrong_source_or_missing_required_persona_fails_before_output(self):
  source=self.base/'incomplete-source';source.mkdir();receipt=json.loads((SOURCE/'.nstack-source.json').read_text());(source/'.nstack-source.json').write_text(json.dumps(receipt));spec=self.specs[0];out=self.base/'missing-persona-output'
  with self.assertRaisesRegex(ValueError,'Missing or linked game support'):game_materialize(source,out,spec,self.component)
  self.assertFalse(out.exists())
  receipt['revision']='wrong';(source/'.nstack-source.json').write_text(json.dumps(receipt))
  with self.assertRaisesRegex(ValueError,'Wrong pinned game source'):game_materialize(source,out,spec,self.component)
  self.assertFalse(out.exists())


if __name__=='__main__':unittest.main()
