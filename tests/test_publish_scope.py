import pathlib,tempfile,unittest,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'lib'));from publish_scope import publish_if_authorized
class Model:
 def __init__(self):self.calls=[]
 def push_to_hub(self,*args,**kw):self.calls.append((args,kw));return 'synthetic receipt'
class PublishTests(unittest.TestCase):
 def test_local_default_and_named_allow_deny(self):
  model=Model()
  with tempfile.TemporaryDirectory() as t:
   self.assertIsNone(publish_if_authorized(model,t,[]));self.assertEqual(model.calls,[])
   with self.assertRaisesRegex(ValueError,'Publishing needs'):publish_if_authorized(model,t,['--publish-repository','owner/model'])
   self.assertEqual(model.calls,[])
   args=['--publish-repository','owner/model','--publish-visibility','private','--publish-rights','synthetic test grant','--publish-artifact',t]
   self.assertEqual(publish_if_authorized(model,t,args),'synthetic receipt');self.assertEqual(model.calls,[(('owner/model',),{'private':True})])
if __name__=='__main__':unittest.main()
