import pathlib,tempfile,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'lib'))
from skill_build import materialize
class MediaScope(unittest.TestCase):
 def test_updated_production_expertise_keeps_six_references_and_tuned_sources(self):
  with tempfile.TemporaryDirectory() as temp:
   root=pathlib.Path(temp);source=root/'source';source.mkdir();out=root/'out';out.mkdir()
   files={'SKILL.md':'---\nname: upstream\ndescription: shot production\n---\n# Shot production\nRead [pipeline](references/pipeline.md).\n',
    'LICENSE':'MIT fixture\n','README_JA.md':'[excluded](missing.md)\n',
    'references/pipeline.md':'Plan shots and preserve stems/timing.\n[Audio](sound-design.md)\n',
    'references/aesthetic-rules.md':'Use actual visual brief.\n','references/final-review.md':'Inspect actual moving frames.\n',
    'references/music-beat-sync.md':'Keep beat and frame origin.\n','references/sound-design.md':'[Sourcing](sfx-sourcing.md)\n','references/sfx-sourcing.md':'Check asset rights and existing user audio.\n',
    'references/sequences/sample.md':'Keep substantive sequence choices.\n','references/shots/sample.md':'Keep shot math.\n',
    'gallery/api/library.json':'{}','demos/tuned/math.ts':'const camera = Math.sin(t);',
    'demos/_legacy/old.ts':'not selected','assets/lib/helper.ts':'export const frame = 1;',
    'assets/scripts/capture-template.mjs':'// selected capture helper', 'shot-polish/decisions.json':'{}',
    'workbench/README.md':'Not activated by default','template/TEMPLATE.md':'Separate runtime trigger',
    'publish/upload.py':'not selected','jianying-export/old.py':'not selected'}
   for rel,data in files.items():
    p=source/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(data)
   spec={'candidate_id':'P224','source_path':'SKILL.md','native_name':'video-shotcraft','delivery':'narrow-patched leaf','source_repository':'Vincentwei1021/video-shotcraft','revision':'1'*40,'rights':'MIT'}
   materialize(source,out,spec,{}, {})
   bundle=out/'source'
   for ref in ('pipeline','aesthetic-rules','final-review','music-beat-sync','sound-design','sfx-sourcing'):
    self.assertTrue((bundle/f'references/{ref}.md').is_file())
   self.assertEqual((bundle/'demos/tuned/math.ts').read_text(),'const camera = Math.sin(t);')
   for rel in ('demos/_legacy','workbench','template','publish','jianying-export','README_JA.md'):
    self.assertFalse((bundle/rel).exists(),rel)
   self.assertIn('4.0.484',(bundle/'SKILL.md').read_text());self.assertTrue((source/'publish/upload.py').is_file())
if __name__=='__main__':unittest.main()
