"""Supported native CLI discovery; discard raw config and retain safe metadata."""
import json,pathlib,queue,shutil,subprocess,threading,time
P=pathlib.Path
def inspect(project,binary=None):
 binary=binary or shutil.which('codex')
 if not binary:raise ValueError('Native Codex CLI is not on PATH')
 project=P(project).resolve(strict=True)
 if not project.is_dir():raise ValueError('Inventory requires an existing project directory')
 process=subprocess.Popen([binary,'app-server','--stdio'],cwd=project,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True);messages=queue.Queue()
 def reader():
  for line in process.stdout:
   try:messages.put(json.loads(line))
   except ValueError:pass
 threading.Thread(target=reader,daemon=True).start()
 def send(value):process.stdin.write(json.dumps(value)+'\n');process.stdin.flush()
 def request(id,method,params):
  send({'id':id,'method':method,'params':params});end=time.monotonic()+30
  while time.monotonic()<end:
   try:value=messages.get(timeout=1)
   except queue.Empty:
    if process.poll() is not None:raise ValueError('Native inventory process exited; no successful loader claim')
    continue
   if value.get('id')==id:
    if 'error' in value:raise ValueError('Native inventory request failed: '+method+'; raw configuration/error withheld')
    return value['result']
  raise ValueError('Native inventory timed out: '+method)
 try:
  request(1,'initialize',{'clientInfo':{'name':'nstack-inventory','version':'1.0'},'capabilities':{'experimentalApi':True}});send({'method':'initialized','params':{}})
  data=request(2,'skills/list',{'cwds':[str(project)],'forceReload':True});configuration=request(3,'config/read',{'includeLayers':True,'cwd':str(project)})
  rows=data.get('data',[])
  if len(rows)!=1 or not isinstance(rows[0].get('skills'),list):raise ValueError('Unexpected native skill inventory schema')
  skills=[{key:item[key] for key in ('name','path','scope') if key in item} for item in rows[0]['skills']]
  config=configuration.get('config',{});servers=config.get('mcp_servers',config.get('mcpServers',{}));plugins=config.get('plugins',{})
  result={'binary':str(P(binary).absolute()),'project':str(project),'skill_count':len(skills),'skills':skills,'loader_error_count':len(rows[0].get('errors',[])),'mcp_server_names':sorted(servers),'local_plugin_enablement':{key:value.get('enabled') for key,value in plugins.items() if isinstance(value,dict)},'scope':'Fresh native CLI metadata only. This does not prove desktop relaunch, hosted plugin enablement, provider access or successful tool effects. Raw config, env values, arguments and error text are discarded.'}
  return result
 finally:
  process.terminate()
  try:process.wait(timeout=10)
  except subprocess.TimeoutExpired:process.kill();process.wait(timeout=10)
