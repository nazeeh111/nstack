"""Pinned isolated npm CLI runtimes; scripts disabled except explicit admitted browser install."""
import hashlib,json,os,pathlib,shutil,subprocess
P=pathlib.Path

def digest(path):
 h=hashlib.sha256()
 with P(path).open('rb') as f:
  while chunk:=f.read(1024*1024):h.update(chunk)
 return h.hexdigest()

def env(root,readonly=False):
 config=root/'cache/npm-config'
 if not readonly:config.mkdir(parents=True,exist_ok=True)
 for name in ('user','global'):
  f=config/name
  if f.exists() and (f.is_symlink() or f.read_bytes()):raise ValueError('Unexpected npm config override')
  if readonly:
   if not f.is_file():raise ValueError('Commission the runtime before invocation')
  else:f.touch(mode=0o600,exist_ok=True)
 return os.environ|{'NPM_CONFIG_USERCONFIG':str(config/'user'),'NPM_CONFIG_GLOBALCONFIG':str(config/'global'),'NPM_CONFIG_REGISTRY':'https://registry.npmjs.org','NPM_CONFIG_CACHE':str(root/'cache/npm'),'PLAYWRIGHT_BROWSERS_PATH':str(root/'runtimes/P061/test/browsers')}

def commission(n,id,op,r,folder):
 c=n.component(id)
 if c['deployment']!='on demand' or (id,op) not in [('P053','cli'),('P061','test'),('P049','cli')]:raise ValueError('No eligible npm operation adapter')
 if r['reviewed_source_revision']!=c['revision']:raise ValueError('Recipe does not match reviewed source')
 prefix=n.STATE/'runtimes'/id/op;prefix.mkdir(parents=True,exist_ok=True);receiptfile=n.STATE/'locks'/f'{id}-{op}.json';runenv=env(n.STATE)
 with n.lock(n.STATE/'runtime-writers'/f'{id}-{op}.lock'):
  if receiptfile.exists():return locked(n,id,op,r,folder)
  package={'name':f'nstack-{id.lower()}-{op}','version':'0.0.0','private':True,'dependencies':{r['package']:r['version']}}
  file=prefix/'package.json'
  if file.exists() and n.load(file)!=package:raise ValueError('Unexpected runtime package configuration')
  n.dump(file,package);lock=prefix/'package-lock.json';published=folder/'package-lock.json'
  if published.exists():
   if lock.exists() and lock.read_bytes()!=published.read_bytes():raise ValueError('Local dependency lock differs from immutable recipe')
   if not lock.exists():shutil.copy2(published,lock)
  elif not lock.exists():subprocess.run(['npm','install','--package-lock-only','--ignore-scripts','--no-audit','--no-fund'],cwd=prefix,env=runenv,check=True)
  data=n.load(lock);entry=data['packages']['node_modules/'+r['package']]
  if entry['version']!=r['version'] or entry.get('integrity')!=r['integrity']:raise ValueError('Resolved package differs from verified immutable artifact')
  subprocess.run(['npm','ci','--ignore-scripts','--no-audit','--no-fund'],cwd=prefix,env=runenv,check=True)
  executable=prefix/'node_modules/.bin'/r['bin'];version=subprocess.check_output([str(executable),'--version'],text=True,env=runenv).strip()
  if r['version'] not in version:raise ValueError('Installed CLI version does not match the recipe')
  if id=='P061':subprocess.run([str(executable),'install','chromium','firefox'],cwd=prefix,env=runenv,check=True)
  files={'package-lock.json':digest(lock)}
  for f in (prefix/'node_modules').rglob('*'):
   if f.is_file() and not f.is_symlink():files[str(f.relative_to(prefix))]=digest(f)
  if id=='P061':
   for f in (prefix/'browsers').rglob('*'):
    if f.is_file() and not f.is_symlink() and os.access(f,os.X_OK):files[str(f.relative_to(prefix))]=digest(f)
  receipt={'id':id,'operation':op,'adapter':'npm-bin','package':r['package'],'version':r['version'],'observed_cli_version':version,'reviewed_source_revision':c['revision'],'runtime_source_revision':r['runtime_source_revision'],'recipe_sha256':digest(folder/'recipe.json'),'prefix':str(prefix),'executable':str(executable),'node_version':subprocess.check_output(['node','--version'],text=True).strip(),'files':files,'state':'ready; target acceptance required'}
  n.dump(receiptfile,receipt);return receipt

def locked(n,id,op,r,folder):
 receipt=n.load(n.STATE/'locks'/f'{id}-{op}.json')
 if receipt['recipe_sha256']!=digest(folder/'recipe.json') or receipt['version']!=r['version']:raise ValueError('Npm recipe changed; commission a reviewed release delta')
 prefix=P(receipt['prefix'])
 if prefix!=(n.STATE/'runtimes'/id/op).resolve():raise ValueError('Runtime receipt escaped its owned environment')
 for name,expected in receipt['files'].items():
  file=prefix/n.safe_relative(name)
  if not file.is_file() or file.is_symlink() or digest(file)!=expected:raise ValueError('Runtime file changed: '+name)
 return receipt

def invoke(n,id,op,r,folder,args):
 with n.read_lock(n.STATE/'runtime-writers'/f'{id}-{op}.lock'):
  receipt=locked(n,id,op,r,folder);runenv=env(n.STATE,readonly=True)|{'NODE_PATH':str(P(receipt['prefix'])/'node_modules')};subprocess.run([receipt['executable'],*args],env=runenv,check=True)
