"""Actual source conservation for two previously replaced skill methods."""
import hashlib,json,pathlib,re,sys,tempfile,unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'lib')]
import nstack
from skill_build import materialize
from closure import validate
class SourceMethods(unittest.TestCase):
 def test_original_find_skills_and_career_modes_are_retained(self):
  m=nstack.manifest();state=nstack.STATE/'sources'
  with tempfile.TemporaryDirectory()as temp:
   for id in ['P016','P354']:
    s=next(x for x in m['skills']if x['candidate_id']==id and x['delivery']=='narrow-patched leaf');source=state/s['source_repository'].replace('/','--')/s['revision']
    if not(source/'.nstack-source.json').is_file():self.skipTest('Pinned offline source absent; no acquisition')
    original=(source/s['source_path']).read_text();out=pathlib.Path(temp)/id;out.mkdir();c=next(x for x in m['components']if x['id']==id);entry=materialize(source,out,s,c,m);leaf=out/(entry or '.')
    active=(leaf/'SKILL.md').read_text();body=active.split('> Native ',1)[1].split('\n\n',1)[1]
    self.assertEqual(body,original[4:].split('\n---\n',1)[1].replace('Claude Code','native host'))
    self.assertEqual((leaf/'UPSTREAM_SKILL.md').read_text(),original)
    validate(out)
    if id=='P016':
     for part in ['npx skills find','npx skills add','When to Use This Skill']:self.assertIn(part,active)
    else:
     for part in ['interview','tracker','apply','cover']:self.assertIn(part,active)
     source_modes={str(x.relative_to(source/'modes'))for x in(source/'modes').rglob('*.md')}
     retained={str(x.relative_to(out/'runtime/career-ops/modes'))for x in(out/'runtime/career-ops/modes').rglob('*.md')}
     self.assertEqual(source_modes,retained)
if __name__=='__main__':unittest.main()
