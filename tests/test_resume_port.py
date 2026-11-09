import json,pathlib,sys,tempfile,unittest
P=pathlib.Path;sys.path.insert(0,str(P(__file__).resolve().parents[1]/'lib'));from patch_resume import materialize
class ResumePort(unittest.TestCase):
 def source(self,root,tracking=True):
  tools=root/'apps/backend/app/mcp_server/tools';tools.mkdir(parents=True)
  for name in ('verify_resume','parse_check_file','parse_check_resume','export_resume_pdf','save_tailored_resume','tailor_and_verify'):
   args='resume_id'
   if name=='parse_check_file':args='file_path'
   if name in ('save_tailored_resume','tailor_and_verify'):args='resume_id, track_application=True' if tracking else 'resume_id'
   (tools/(name+'.py')).write_text('async def '+name+'('+args+'):\n raise RuntimeError("Must never execute source while building")\n')
 def test_build_is_static_and_excludes_broad_startup_and_tracking(self):
  with tempfile.TemporaryDirectory() as t:
   root=P(t);self.source(root);out=root/'out';out.mkdir();skill=materialize(root,out);contract=json.loads((out/'references/tool-contract.json').read_text());self.assertEqual(contract['required_save_arguments'],{'track_application':False});self.assertIn('keep this trial conditional',skill);self.assertNotIn('nohup',skill);self.assertNotIn('npm install',skill);self.assertNotIn('jobs/README.md',skill)
 def test_upstream_save_that_cannot_disable_tracking_is_refused(self):
  with tempfile.TemporaryDirectory() as t:
   root=P(t);self.source(root,False);out=root/'out';out.mkdir()
   with self.assertRaisesRegex(ValueError,'cannot disable'):materialize(root,out)
if __name__=='__main__':unittest.main()
