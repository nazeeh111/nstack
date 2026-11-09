#!/usr/bin/env python3
"""Read-only base-repository PR comments, with independent and nested pagination."""
import argparse,datetime,json,subprocess
FIELDS='id body createdAt updatedAt author { login }'
PAGE='pageInfo { hasNextPage endCursor }'
THREAD='id isResolved isOutdated path line diffSide startLine startDiffSide originalLine originalStartLine resolvedBy { login }'

def request(query,variables):
 p=subprocess.run(['gh','api','graphql','--input','-'],input=json.dumps({'query':query,'variables':variables}),capture_output=True,text=True)
 if p.returncode:raise RuntimeError('GitHub read failed; inspect native gh authentication/access and error locally')
 data=json.loads(p.stdout)
 if data.get('errors'):raise RuntimeError('GraphQL returned errors; pagination is incomplete')
 return data['data']

def pages(fetch):
 cursor=None;seen=set()
 for _ in range(10000):
  value=fetch(cursor);yield value
  info=value['pageInfo']
  if not info['hasNextPage']:return
  next_cursor=info.get('endCursor')
  if not next_cursor or next_cursor==cursor or next_cursor in seen:raise RuntimeError('Repeated/missing pagination cursor; incomplete')
  seen.add(next_cursor);cursor=next_cursor
 raise RuntimeError('Pagination safety bound exceeded; incomplete')

def dedup(nodes):
 result={}
 for node in nodes:
  if not node or not node.get('id'):raise RuntimeError('Node lacks a stable ID')
  result[node['id']]=node
 return list(result.values())

def fetch_all(owner,repo,number,transport=request):
 if not owner or not repo or int(number)<=0:raise ValueError('Explicit base owner/repository/positive PR number required')
 meta=None;outputs={};started=datetime.datetime.now(datetime.timezone.utc).isoformat()
 for kind in ('comments','reviews','reviewThreads'):
  nodes=FIELDS if kind=='comments' else 'id state body submittedAt author { login }' if kind=='reviews' else THREAD+' comments(first:100) {'+PAGE+' nodes {'+FIELDS+'}}'
  query='query($owner:String!,$repo:String!,$number:Int!,$cursor:String){repository(owner:$owner,name:$repo){pullRequest(number:$number){number url title state '+kind+'(first:100,after:$cursor){'+PAGE+' nodes{'+nodes+'}}}}}'
  def fetch(cursor):
   nonlocal meta
   data=transport(query,{'owner':owner,'repo':repo,'number':int(number),'cursor':cursor});pr=data['repository']['pullRequest']
   if not pr or pr['number']!=int(number):raise RuntimeError('Requested base PR unavailable or identity mismatch')
   if meta is None:meta={k:pr[k] for k in ('number','url','title','state')}|{'owner':owner,'repo':repo}
   return pr[kind]
  outputs[kind]=dedup([node for page in pages(fetch) for node in page.get('nodes',[])])
 for thread in outputs['reviewThreads']:
  first=thread['comments'];initial=True
  query='query($id:ID!,$cursor:String){node(id:$id){... on PullRequestReviewThread{comments(first:100,after:$cursor){'+PAGE+' nodes{'+FIELDS+'}}}}}'
  def fetch_thread(cursor):
   if cursor is None:return first
   data=transport(query,{'id':thread['id'],'cursor':cursor})
   if not data.get('node'):raise RuntimeError('Review thread became unavailable; incomplete')
   return data['node']['comments']
  thread['comments']={'nodes':dedup([node for page in pages(fetch_thread) for node in page.get('nodes',[])])}
 return {'pull_request':meta,'conversation_comments':outputs['comments'],'reviews':outputs['reviews'],'review_threads':outputs['reviewThreads'],'complete':True,'started_at':started,'limits':'Read-only live pagination, deduplicated by stable ID. This is not a transactionally frozen remote snapshot; content may change while reading.'}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--owner',required=True);p.add_argument('--repo',required=True);p.add_argument('--number',type=int,required=True);a=p.parse_args();print(json.dumps(fetch_all(a.owner,a.repo,a.number),indent=2))
if __name__=='__main__':main()
