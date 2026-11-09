import pathlib,tempfile,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'lib'))
from skill_build import materialize
class MediaScope(unittest.TestCase):
 def test_full_upstream_repository_exposes_only_selected_expertise_references(self):
  with tempfile.TemporaryDirectory() as temp:
   root=pathlib.Path(temp);source=root/'source';source.mkdir();out=root/'out';out.mkdir();refs=source/'references';refs.mkdir()
   (source/'SKILL.md').write_text('---\nname: upstream\ndescription: whole workflow\n---\n# Workbench\n')
   (source/'LICENSE').write_text('MIT fixture\n');(source/'README_JA.md').write_text('[excluded](references/sfx-sourcing.md)\n');(source/'scripts').mkdir();(source/'scripts/legacy-upload.sh').write_text('do not install')
   (refs/'pipeline.md').write_text('Original onboarding\n## 阶段 0：产品理解\nShot planning\n9. **为交付后的动效工作台留好接口** missing runtime\n**产出** `src/workbench.ts`\n## 阶段 6：声音设计\n1. 读 `references/sound-design.md` 与 `references/sfx-sourcing.md`，从 Freesound 下载。\n2. 用 `assets/scripts/sfx-source.py get` 下载。\n3. **BGM** preserve stems and timing\n## 阶段 7：验收\nnode workbench/scripts/open.mjs\n');(refs/'music-beat-sync.md').write_text('Beat alignment\n');(refs/'sound-design.md').write_text('新制作与换音统一从 **Freesound** 搜索、下载，操作见 [sfx-sourcing.md](sfx-sourcing.md)。\n[Beat](music-beat-sync.md) [Review](final-review.md)\n');(refs/'sfx-sourcing.md').write_text('excluded provider workflow');(refs/'final-review.md').write_text('excluded orchestration')
   spec={'candidate_id':'P224','source_path':'SKILL.md','delivery':'narrow-patched leaf','source_repository':'Vincentwei1021/video-shotcraft','revision':'1'*40,'rights':'MIT'}
   materialize(source,out,spec,{}, {})
   self.assertEqual({str(p.relative_to(out)) for p in out.rglob('*') if p.is_file()},{'SKILL.md','LICENSE','references/pipeline.md','references/sound-design.md','references/music-beat-sync.md'})
   self.assertIn('/blob/'+'1'*40+'/references/final-review.md',(out/'references/sound-design.md').read_text());self.assertTrue((source/'scripts/legacy-upload.sh').exists());pipeline=(out/'references/pipeline.md').read_text();self.assertIn('User-supplied audio wins',pipeline);self.assertIn('preserve stems and timing',pipeline);self.assertNotIn('assets/scripts/sfx-source.py',pipeline);self.assertNotIn('workbench/scripts/open.mjs',pipeline);self.assertIn('pinned final-QA reference',pipeline)
if __name__=='__main__':unittest.main()
