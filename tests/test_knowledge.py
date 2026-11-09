import pathlib,tempfile,unittest,os,sys,importlib.util
P=pathlib.Path;sys.path.insert(0,str(P(__file__).resolve().parents[1]/'lib'));import knowledge
spec=importlib.util.spec_from_file_location('nstack',P(__file__).resolve().parents[1]/'nstack.py');n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
class KnowledgeTests(unittest.TestCase):
 def test_correction_deletion_stale_source_and_scope(self):
  old=P.cwd()
  with tempfile.TemporaryDirectory() as temp:
   project=P(temp).resolve();os.chdir(project)
   try:
    source=project/'evidence.txt';source.write_text('Synthetic decay constant is 0.8 seconds.');knowledge.change(project,'decay','0.8 seconds',source,False,n.dump);self.assertEqual(knowledge.recall(project,'decay')['claim'],'0.8 seconds')
    source.write_text('Synthetic decay constant is 1.1 seconds.')
    with self.assertRaisesRegex(ValueError,'source changed'):knowledge.recall(project,'decay')
    knowledge.change(project,'decay','1.1 seconds',source,False,n.dump);self.assertEqual(knowledge.recall(project,'decay')['generation'],2)
    knowledge.change(project,'decay',None,None,True,n.dump);self.assertNotIn('claim',knowledge.recall(project,'decay'))
    os.chdir(old)
    with self.assertRaisesRegex(ValueError,'current project scope'):knowledge.recall(project,'decay')
   finally:os.chdir(old)
if __name__=='__main__':unittest.main()
