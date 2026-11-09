"""Project-bound stdio MCP owner for the reviewed shelf. No shell tool."""
import json,os,pathlib,sys

TOOLS=[
 {'name':'activate_leaf','description':'Build and expose one eligible nstack specialist in this project only. Inspect nstack show first. Returns the exact reviewed skill path to read. Trials/substitutes stay locked.',
  'inputSchema':{'type':'object','properties':{'candidate_id':{'type':'string'},'source_path':{'type':'string'}},'required':['candidate_id','source_path'],'additionalProperties':False},
  'annotations':{'readOnlyHint':False,'destructiveHint':False,'idempotentHint':True,'openWorldHint':True}},
 {'name':'deactivate_leaf','description':'Remove only a journaled nstack shelf link from this project; retain source, build and project artifacts.',
  'inputSchema':{'type':'object','properties':{'name':{'type':'string'}},'required':['name'],'additionalProperties':False},
  'annotations':{'readOnlyHint':False,'destructiveHint':False,'idempotentHint':True,'openWorldHint':False}},
 {'name':'verify_shelf','description':'Verify this project shelf against immutable source/build identities and its ownership journal.',
  'inputSchema':{'type':'object','properties':{},'additionalProperties':False},
  'annotations':{'readOnlyHint':True,'destructiveHint':False,'idempotentHint':True,'openWorldHint':False}}]

class Publisher:
 def __init__(self,n,project):
  self.n=n;self.project=n.project_paths(project);st=self.project.stat();self.identity=(st.st_dev,st.st_ino)
 def call(self,name,args):
  p=self.n.project_paths(self.project);st=p.stat()
  if (st.st_dev,st.st_ino)!=self.identity:raise ValueError('Project root identity changed; restart the owner')
  tool=next((t for t in TOOLS if t['name']==name),None)
  if not tool or not isinstance(args,dict):raise ValueError('Unknown tool or invalid arguments')
  schema=tool['inputSchema'];keys=set(args)
  if keys-set(schema['properties']) or not set(schema.get('required',[]))<=keys or any(not isinstance(v,str) for v in args.values()):raise ValueError('Arguments differ from the bounded tool schema')
  if name=='activate_leaf':
   c=self.n.component(args['candidate_id'])
   if c['deployment']!='on demand':raise ValueError('This project publisher admits on-demand leaves only; per-ID trial/substitute verification is required')
   release=self.n.build(args['candidate_id'],args['source_path']);path=self.n.publish(p,release)
   return {'skill_path':str(pathlib.Path(path)/'SKILL.md'),'release':str(release),'shelf':self.n.verify(p),'next':'Read skill_path and the relevant support, then execute the task and independently check its artifact. Activation alone is not use.'}
  if name=='deactivate_leaf':
   import re
   if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,127}',args['name']):raise ValueError('Invalid shelf name')
   if args['name'] in self.n.activation_rows(p):self.n.deactivate(p,args['name'])
   elif (p/'.agents/skills'/args['name']).exists():raise ValueError('Unowned shelf entry')
  return self.n.verify(p)

def serve(n,project):
 owner=Publisher(n,project);initialized=False;ready=False
 for raw in sys.stdin:
  response=None;request=None
  try:
   if len(raw)>1024*1024:raise ValueError('Oversized request')
   request=json.loads(raw)
   if request.get('jsonrpc')!='2.0':raise ValueError('JSON-RPC 2.0 required')
   method=request.get('method');params=request.get('params',{});id=request.get('id')
   if method=='initialize':
    version=params.get('protocolVersion');supported=('2024-11-05','2025-03-26','2025-06-18','2025-11-25')
    result={'protocolVersion':version if version in supported else '2025-06-18','capabilities':{'tools':{'listChanged':False}},'serverInfo':{'name':'nstack-project-publisher','version':'1.0.0'},'instructions':'One project only. Search the installed inventory; activate the exact eligible leaf; read returned SKILL.md; verify actual outputs. No arbitrary command, credential, account or global setting operation is provided.'};initialized=True
   elif method=='notifications/initialized' and initialized:ready=True;continue
   elif method=='ping':result={}
   elif not ready:raise ValueError('Complete initialization first')
   elif method=='tools/list':result={'tools':TOOLS}
   elif method=='tools/call':
    try:result={'content':[{'type':'text','text':json.dumps(owner.call(params.get('name'),params.get('arguments',{})),indent=2)}],'isError':False}
    except (OSError,ValueError,KeyError) as exc:result={'content':[{'type':'text','text':str(exc)}],'isError':True}
   elif id is None:continue
   else:
    response={'jsonrpc':'2.0','id':id,'error':{'code':-32601,'message':'Method not found'}}
   if response is None and id is not None:response={'jsonrpc':'2.0','id':id,'result':result}
  except (ValueError,TypeError,KeyError) as exc:
   response={'jsonrpc':'2.0','id':request.get('id') if isinstance(request,dict) else None,'error':{'code':-32600,'message':str(exc)}}
  if response is not None:print(json.dumps(response,separators=(',',':')),flush=True)
