import pathlib,tempfile,unittest,os,sys,importlib.util,subprocess,json
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
    knowledge.change(project,'decay','1.1 seconds',source,False,n.dump,1);self.assertEqual(knowledge.recall(project,'decay')['generation'],2)
    knowledge.change(project,'decay',None,None,True,n.dump,2);self.assertNotIn('claim',knowledge.recall(project,'decay'))
    os.chdir(old)
    with self.assertRaisesRegex(ValueError,'current project scope'):knowledge.recall(project,'decay')
   finally:os.chdir(old)
 def test_two_writers_cannot_silently_overwrite_the_same_generation(self):
  old=P.cwd()
  with tempfile.TemporaryDirectory() as temp:
   project=P(temp).resolve();os.chdir(project)
   try:
    source=project/'evidence.txt';source.write_text('shared evidence')
    knowledge.change(project,'fact','initial',source,False,n.dump)
    cli=P(__file__).resolve().parents[1]/'nstack.py'
    common=[sys.executable,str(cli),'knowledge','set',str(project),'fact','--source',str(source),'--expected-generation','1','--claim']
    workers=[subprocess.Popen(common+[claim],cwd=project,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True) for claim in ['writer-a','writer-b']]
    results=[(*p.communicate(timeout=15),p.returncode) for p in workers]
    self.assertEqual(sorted(r[2] for r in results),[0,1])
    self.assertIn('generation changed',' '.join(r[1] for r in results))
    record=knowledge.recall(project,'fact');self.assertEqual(record['generation'],2)
    self.assertIn(record['claim'],['writer-a','writer-b'])
    before=(project/'.nstack/knowledge/fact.json').read_bytes()
    with self.assertRaisesRegex(ValueError,'generation changed'):knowledge.change(project,'fact','stale',source,False,n.dump,1)
    self.assertEqual(before,(project/'.nstack/knowledge/fact.json').read_bytes())
   finally:os.chdir(old)
if __name__=='__main__':unittest.main()
