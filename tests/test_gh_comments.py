import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'lib'));import gh_comments as g
class Comments(unittest.TestCase):
 def test_independent_connections_and_nested_thread_pages(self):
  calls=[]
  def page(nodes,next=None):return {'nodes':nodes,'pageInfo':{'hasNextPage':bool(next),'endCursor':next}}
  def transport(query,v):
   calls.append((query,v))
   if 'id' in v:
    self.assertEqual(v['id'],'thread1');self.assertEqual(v['cursor'],'nested1');return {'node':{'comments':page([{'id':'reply1'},{'id':'reply2'}])}}
   self.assertEqual((v['owner'],v['repo'],v['number']),('base-owner','base-repo',7));meta={'number':7,'url':'https://github.com/base-owner/base-repo/pull/7','title':'fixture','state':'OPEN'}
   if 'reviewThreads(first' in query:kind='reviewThreads';data=page([{'id':'thread1','comments':page([{'id':'reply1'}],'nested1')}])
   elif 'reviews(first' in query:kind='reviews';data=page([{'id':'review'}])
   else:kind='comments';data=page([{'id':'comment2'},{'id':'comment1'}]) if v['cursor']=='comments1' else page([{'id':'comment1'}],'comments1')
   return {'repository':{'pullRequest':meta|{kind:data}}}
  result=g.fetch_all('base-owner','base-repo',7,transport);self.assertTrue(result['complete']);self.assertEqual(len(result['conversation_comments']),2);self.assertEqual(len(result['reviews']),1);self.assertEqual(len(result['review_threads'][0]['comments']['nodes']),2);self.assertEqual(len(calls),5)
 def test_repeated_cursor_is_not_complete(self):
  def fetch(cursor):return {'nodes':[],'pageInfo':{'hasNextPage':True,'endCursor':'same'}}
  with self.assertRaisesRegex(RuntimeError,'incomplete'):list(g.pages(fetch))
