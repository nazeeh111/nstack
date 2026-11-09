"""Supported native CLI discovery; discard raw config and retain safe metadata."""
import json,pathlib,queue,shutil,subprocess,threading,time
P=pathlib.Path
def effective_metadata(data,configuration):
 if not isinstance(data,dict) or not isinstance(data.get('data'),list) or len(data['data'])!=1:raise ValueError('Unexpected native skill inventory schema')
 row=data['data'][0]
 if not isinstance(row,dict) or not isinstance(row.get('skills'),list) or not isinstance(row.get('errors'),list):raise ValueError('Native skill inventory lacks explicit skills/error status')
 skills=[]
 for item in row['skills']:
  if not isinstance(item,dict) or not all(isinstance(item.get(key),str) and item[key] for key in ('name','path','scope')):raise ValueError('Unexpected native skill identity metadata')
  skills.append({key:item[key] for key in ('name','path','scope')})
 if not isinstance(configuration,dict) or not isinstance(configuration.get('config'),dict):raise ValueError('Native effective configuration payload is missing')
 config=configuration['config'];servers=config.get('mcp_servers',config.get('mcpServers',{}));plugins=config.get('plugins',{})
 if not isinstance(servers,dict) or not isinstance(plugins,dict):raise ValueError('Unexpected native server/plugin configuration metadata')
 flags={}
 for key,value in plugins.items():
  if not isinstance(value,dict) or (value.get('enabled') is not None and type(value['enabled']) is not bool):raise ValueError('Unexpected native local-plugin enablement metadata')
  flags[key]=value.get('enabled')
 return {'skill_count':len(skills),'skills':skills,'loader_error_count':len(row['errors']),'mcp_server_names':sorted(servers),'local_plugin_enablement':flags}
def plugin_metadata(data):
 """Allowlist installation metadata; omit account, config and sharing payloads."""
 if not isinstance(data,dict) or not isinstance(data.get('marketplaces'),list):raise ValueError('Unexpected native plugin inventory schema')
 result=[];seen=set()
 for marketplace in data['marketplaces']:
  if not isinstance(marketplace.get('name'),str) or not isinstance(marketplace.get('plugins'),list):raise ValueError('Unexpected native marketplace inventory schema')
  for item in marketplace['plugins']:
   if not isinstance(item,dict):raise ValueError('Unexpected native plugin metadata type')
   if not all(isinstance(item.get(key),str) and item[key] for key in ('id','name')) or any(type(item.get(key)) is not bool for key in ('installed','enabled')):raise ValueError('Unexpected native plugin identity/state')
   source=item.get('source') or {}
   if not isinstance(source,dict) or any(item.get(key) is not None and not isinstance(item[key],str) for key in ('version','localVersion')) or (source.get('type') is not None and not isinstance(source['type'],str)):raise ValueError('Unexpected native plugin version/source metadata')
   if item['id'] in seen:raise ValueError('Ambiguous duplicate native plugin identity')
   seen.add(item['id']);result.append({'id':item['id'],'name':item['name'],'marketplace':marketplace['name'],'installed':item['installed'],'enabled':item['enabled'],'version':item.get('version'),'local_version':item.get('localVersion'),'source_type':source.get('type')})
 errors=data.get('marketplaceLoadErrors',[])
 if not isinstance(errors,list):raise ValueError('Unexpected native plugin error schema')
 return {'plugins':result,'plugin_marketplace_error_count':len(errors),'plugin_catalog_scope':'Configured native marketplaces, including the default remote catalog when enabled by the host. Not an exhaustive external directory or proof of tool access. Raw errors, account/sharing data and configuration are discarded.'}
def installed_plugins(project,binary):
 # Match the supported CLI's installed-plugin catalog behavior. This read-only
 # inventory client never requests or relays authentication tokens.
 process=subprocess.run([binary,'plugin','list','--json'],cwd=project,capture_output=True,text=True,timeout=120)
 if process.returncode:raise ValueError('Native installed-plugin command failed; raw diagnostics withheld')
 try:data=json.loads(process.stdout)
 except ValueError:raise ValueError('Native installed-plugin command returned no valid standalone JSON') from None
 if not isinstance(data,dict) or any(not isinstance(data.get(key),list) for key in ('installed','available')):raise ValueError('Unexpected native installed-plugin schema')
 if set(data)-{'installed','available'}:raise ValueError('Unexpected native installed-plugin completeness/error fields; no clean inventory claim')
 markets={}
 for item in data['installed']:
  if not isinstance(item,dict) or not isinstance(item.get('source',{}),dict):raise ValueError('Unexpected native installed-plugin metadata type')
  market=item.get('marketplaceName')
  if not isinstance(market,str) or not market:raise ValueError('Native installed plugin lacks marketplace identity')
  markets.setdefault(market,[]).append({'id':item.get('pluginId'),'name':item.get('name'),'installed':item.get('installed'),'enabled':item.get('enabled'),'version':item.get('version'),'source':{'type':item.get('source',{}).get('source')}})
 result=plugin_metadata({'marketplaces':[{'name':name,'plugins':plugins} for name,plugins in markets.items()]})
 warning=bool(process.stderr.strip());result['plugin_native_warning_present']=warning;result['plugin_marketplace_error_count']=None if warning else 0
 result['plugin_catalog_scope']='Supported native plugin list --json installed entries only. Any native warning leaves catalog completeness unresolved; raw diagnostics, account/sharing data and configuration are discarded. Enabled does not prove successful tool access.'
 return result
def inspect(project,binary=None,include_plugins=False):
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
  # Supported effective-config metadata is necessary for server names. Do not
  # request source layers or inspect credential files; discard the raw response.
  data=request(2,'skills/list',{'cwds':[str(project)],'forceReload':True});configuration=request(3,'config/read',{'includeLayers':False,'cwd':str(project)})
  result={'binary':str(P(binary).absolute()),'project':str(project),**effective_metadata(data,configuration),'scope':'Fresh native CLI metadata only. Local config alone does not establish hosted plugin state; --plugins separately reads native installed/enabled metadata. This does not prove desktop relaunch, provider access or successful tool effects. Raw config, env values, arguments and error text are discarded.'}
 finally:
  process.terminate()
  try:process.wait(timeout=10)
  except subprocess.TimeoutExpired:process.kill();process.wait(timeout=10)
 if include_plugins:result.update(installed_plugins(project,binary))
 return result
