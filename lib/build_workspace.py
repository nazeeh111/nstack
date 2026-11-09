"""Owned editable source workspaces for native, manually commissioned recipes."""
import hashlib,json,os,pathlib,re,subprocess,sys,time
P=pathlib.Path
def prepare(n,id,project,fresh=False,retire=False):
 if not re.fullmatch('[A-Z][A-Z0-9-]{0,79}',id):raise ValueError('Invalid workspace component ID')
 c={} if retire else n.component(id)
 if not retire:
  if c['deployment']!='on demand':raise ValueError('Source workspace activation requires the per-ID trial/substitute gate; consult entries never install')
  if not isinstance(c.get('repository'),str) or not re.fullmatch(r'[\w.-]+/[\w.-]+',c['repository']) or not re.fullmatch('[0-9a-f]{40}',c.get('revision','')):raise ValueError('This route uses its official entitled surface, not a local source workspace')
  if c['implementation_mode']=='official plugin':raise ValueError('Official plugin material stays on its entitled host surface')
 project=n.project_paths(project);st=project.stat();scope=n.sha(json.dumps([str(project),st.st_dev,st.st_ino]).encode());owner=n.STATE/'workspace-owners'/scope/id;record=owner/'current.json'
 with n.lock(owner/'writer.lock'):
  saved=n.load(record) if record.exists() else None
  if saved:
   prefix=P(saved['prefix']);expected_parent=n.STATE/'workspaces'/scope/id
   if prefix.parent!=expected_parent or prefix.is_symlink() or prefix.resolve()!=prefix.absolute() or saved['id']!=id or saved['project']!=str(project):raise ValueError('Workspace ownership coordinates differ')
   if saved.get('phase')=='retiring':
    destination=P(saved['retired'])
    if destination.parent!=n.STATE/'retired-workspaces' or not destination.name.startswith(scope+'-'+id+'-') or destination.is_symlink():raise ValueError('Workspace retirement coordinates differ')
    if prefix.exists():
     if destination.exists():raise ValueError('Both workspace retirement locations exist')
     os.rename(prefix,destination)
    elif not destination.is_dir():raise ValueError('Missing workspace retirement destination')
    saved['phase']='retired';n.dump(record,saved)
   if saved.get('phase') not in ('active','preparing','retired'):raise ValueError('Unknown workspace journal phase')
   if saved.get('phase')=='preparing' and not (fresh or retire):raise ValueError('Interrupted source preparation retained; use --fresh or retire-workspace to reconcile it')
   if saved.get('phase') in ('active','preparing') and (fresh or retire):
    destination=n.STATE/'retired-workspaces'/f'{scope}-{id}-{time.time_ns()}';destination.parent.mkdir(parents=True,exist_ok=True);saved.update({'phase':'retiring','retired':str(destination)});n.dump(record,saved);os.rename(prefix,destination);saved['phase']='retired';n.dump(record,saved)
   if saved.get('phase')=='active':
    if saved['revision']!=c['revision'] or saved['source_repository']!=c['repository']:raise ValueError('Source selection changed; retain the workspace and request a fresh reviewed attempt')
    source=prefix/'build-source';source_boundary(source)
    # The editable index may hide changes via assume-unchanged/skip-worktree.
    # Compare actual bytes, modes, links and Git metadata against the private
    # before-image; never execute Git config/hooks from a reused checkout.
    if source_snapshot(n,source)!=saved.get('pristine_files'):raise ValueError('Workspace has edited/generated inputs. Preserve it for existing build use; --fresh retains the whole attempt and creates a new source checkout')
    return summary(saved)
  if retire:return {'id':id,'state':'retired' if saved else 'absent','retained':saved.get('retired') if saved else None}
  prefix=n.STATE/'workspaces'/scope/id/str(time.time_ns());prefix.mkdir(parents=True);saved={'id':id,'project':str(project),'source_repository':c['repository'],'revision':c['revision'],'prefix':str(prefix),'phase':'preparing'};n.dump(record,saved)
  env=clean_environment(prefix);source=prefix/'build-source';subprocess.run(['git','init','-q',str(source)],check=True,env=env);subprocess.run(['git','-C',str(source),'fetch','-q','--depth=1','https://github.com/'+c['repository']+'.git',c['revision']],check=True,env=env,timeout=600);subprocess.run(['git','-C',str(source),'checkout','-q','--detach','FETCH_HEAD'],check=True,env=env)
  actual=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True,env=env).strip()
  if actual!=c['revision']:raise ValueError('Source workspace commit mismatch')
  source_boundary(source);saved.update({'phase':'active','source':str(source),'output':str(prefix/'output'),'pristine_files':source_snapshot(n,source),'claim':'Editable source preparation only. Follow the per-ID native build, dependency/model/asset locks and actual artifact checks; this is not a runtime acceptance receipt.'});(prefix/'output').mkdir();n.dump(record,saved);return summary(saved)
def summary(saved):return {k:v for k,v in saved.items() if k!='pristine_files'}
def source_boundary(source):
 if source.is_symlink() or source.resolve()!=source.absolute() or not source.is_dir():raise ValueError('Linked or missing workspace source')
 git=source/'.git'
 if git.is_symlink() or git.resolve()!=git.absolute() or not git.is_dir():raise ValueError('Workspace Git metadata escaped the owned checkout')
def source_snapshot(n,source):
 result={}
 def failed(error):raise ValueError('Unreadable workspace input') from None
 for folder,dirs,files in os.walk(source,followlinks=False,onerror=failed):
  for name in dirs+files:
   file=P(folder)/name;key=str(file.relative_to(source))
   if file.is_symlink():result[key]={'link':str(file.readlink())}
   elif file.is_file():result[key]={'sha256':n.sha(file.read_bytes()),'mode':file.stat().st_mode&0o777}
   elif not file.is_dir():raise ValueError('Nonregular workspace input')
 return result
def clean_environment(prefix):
 home=prefix/'build-home';home.mkdir(exist_ok=True)
 return {'PATH':os.environ.get('PATH','/usr/bin:/bin'),'HOME':str(home),'TMPDIR':os.environ.get('TMPDIR','/private/tmp'),'LANG':'en_US.UTF-8','GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1','GIT_TERMINAL_PROMPT':'0','GIT_CONFIG_COUNT':'2','GIT_CONFIG_KEY_0':'credential.helper','GIT_CONFIG_VALUE_0':'','GIT_CONFIG_KEY_1':'core.hooksPath','GIT_CONFIG_VALUE_1':'/dev/null'}
