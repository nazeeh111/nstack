#!/usr/bin/env python3
"""Native-first project capability registry and content-addressed publisher."""
from __future__ import annotations
import argparse,contextlib,fcntl,hashlib,json,os,pathlib,re,shutil,subprocess,sys,tempfile,time
P=pathlib.Path
ROOT=P(__file__).resolve().parent
STATE=P(os.environ.get('NSTACK_STATE',P.home()/'Library/Application Support/nstack'))

def load(path):return json.loads(P(path).read_text())
def dump(path,data):
 path=P(path);path.parent.mkdir(parents=True,exist_ok=True)
 raw=(json.dumps(data,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode()
 if path.exists() and path.read_bytes()==raw:return
 fd,name=tempfile.mkstemp(prefix='.'+path.name,dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
  os.replace(name,path)
 finally:
  if os.path.exists(name):os.unlink(name)
def sha(data):return hashlib.sha256(data).hexdigest()
def manifest():return load(ROOT/'registry/manifest.json')
def component(id):
 for row in manifest()['components']:
  if row['id']==id:return row
 raise ValueError('No admitted component '+id)
def leaf(id,path):
 for row in manifest()['skills']:
  if row['candidate_id']==id and row['source_path']==path:return row
 raise ValueError('No selected leaf at these coordinates')
def safe_relative(name):
 p=P(name)
 if p.is_absolute() or '..' in p.parts:raise ValueError('Unsafe relative path')
 return p
@contextlib.contextmanager
def lock(path):
 path.parent.mkdir(parents=True,exist_ok=True)
 if path.is_symlink():raise ValueError('Linked lock file')
 fd=os.open(path,os.O_CREAT|os.O_APPEND|os.O_WRONLY|getattr(os,'O_NOFOLLOW',0),0o600)
 with os.fdopen(fd,'a') as f:
  fcntl.flock(f,fcntl.LOCK_EX);yield

@contextlib.contextmanager
def read_lock(path):
 """Readers need no write grant to the commissioned runtime registry."""
 fd=os.open(path,os.O_RDONLY|getattr(os,'O_NOFOLLOW',0))
 with os.fdopen(fd,'r') as f:
  fcntl.flock(f,fcntl.LOCK_SH);yield

def tree(path):
 result={}
 for f in sorted(path.rglob('*')):
  if f.is_symlink():raise ValueError('Release contains a symlink')
  if f.is_file() and f!=path/'.nstack-release.json':result[str(f.relative_to(path))]=sha(f.read_bytes())
 return result

def verify_release(path):
 receipt=load(path/'.nstack-release.json')
 if tree(path)!=receipt['files']:raise ValueError('Release tampered: '+str(path))
 if sha(json.dumps(receipt['files'],sort_keys=True).encode())!=receipt['content_sha256']:raise ValueError('Invalid release identity')
 return receipt

def check_source(dest):
 info=load(dest/'.nstack-source.json')
 if not info.get('files'):raise ValueError('Source cache requires verified file hashes: '+str(dest))
 files={str(f.relative_to(dest)):sha(f.read_bytes()) for f in dest.rglob('*') if f.is_file() and f!=dest/'.nstack-source.json'}
 if files!=info['files']:raise ValueError('Source cache changed: '+str(dest))
 return dest

def acquire(repo,rev):
 if not isinstance(repo,str) or not isinstance(rev,str) or not re.fullmatch(r'[\w.-]+/[\w.-]+',repo) or not re.fullmatch(r'[0-9a-f]{40}',rev):raise ValueError('A reviewed full Git commit and GitHub repository are required')
 dest=STATE/'sources'/repo.replace('/','--')/rev
 if (dest/'.nstack-source.json').exists():return check_source(dest)
 dest.parent.mkdir(parents=True,exist_ok=True)
 with lock(dest.parent/'.fetch.lock'):
  if (dest/'.nstack-source.json').exists():return check_source(dest)
  with tempfile.TemporaryDirectory(prefix='.fetch-',dir=dest.parent) as tmp:
   tmp=P(tmp);git=tmp/'git';out=tmp/'source';out.mkdir()
   subprocess.run(['git','init','--bare','-q',str(git)],check=True)
   subprocess.run(['git','-C',str(git),'fetch','-q','--depth=1','https://github.com/'+repo+'.git',rev],check=True)
   actual=subprocess.check_output(['git','-C',str(git),'rev-parse','FETCH_HEAD'],text=True).strip()
   if actual!=rev:raise ValueError('Source revision mismatch')
   entries=subprocess.check_output(['git','-C',str(git),'ls-tree','-rz',rev])
   batch=subprocess.Popen(['git','-C',str(git),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
   try:
    for record in entries.split(b'\0'):
     if not record:continue
     meta,name=record.split(b'\t',1);mode,kind,blob=meta.split();rel=safe_relative(os.fsdecode(name))
     if kind!=b'blob' or mode==b'120000':continue
     batch.stdin.write(blob+b'\n');batch.stdin.flush();header=batch.stdout.readline().split()
     if len(header)!=3 or header[:2]!=[blob,b'blob']:raise ValueError('Git source blob identity/type differs')
     length=int(header[2]);raw=batch.stdout.read(length)
     if len(raw)!=length or batch.stdout.read(1)!=b'\n':raise ValueError('Truncated Git source blob')
     f=out/rel;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(raw);f.chmod(0o755 if mode==b'100755' else 0o644)
    batch.stdin.close()
    if batch.wait()!=0:raise ValueError('Git source extraction failed')
   finally:
    if batch.poll() is None:batch.terminate();batch.wait()
   dump(out/'.nstack-source.json',{'repository':repo,'revision':rev,'git_verified':True,'files':{str(f.relative_to(out)):sha(f.read_bytes()) for f in out.rglob('*') if f.is_file()}})
   os.rename(out,dest)
 return dest

def shelf_name(id,path,repo):
 selected=next((s for s in manifest()['skills'] if (s['candidate_id'],s['source_path'],s['source_repository'])==(id,path,repo)),{})
 raw=selected.get('native_name') or P(path).parent.name or repo.split('/')[-1]
 return id.lower()+'-'+re.sub(r'[^a-z0-9-]+','-',raw.lower()).strip('-')

def builder_identity():
 paths=[ROOT/'nstack.py',ROOT/'lib/skill_build.py',ROOT/'lib/publish_scope.py',ROOT/'lib/claim_evidence.py',ROOT/'lib/closure.py',ROOT/'lib/voltage_check.py',ROOT/'lib/gh_comments.py',ROOT/'lib/unreal_two_shot_probe.py',ROOT/'lib/gp_delivery_guard.py',ROOT/'lib/unreal_animation_probe.py']+sorted((ROOT/'lib').glob('patch_*.py'))
 return sha(json.dumps({p.name:sha(p.read_bytes()) for p in paths},sort_keys=True).encode())

def build(id,path):
 c=component(id);s=leaf(id,path)
 if c['deployment']=='consult' or s['delivery'] not in ('intact upstream leaf','narrow-patched leaf','native runtime/method adapter') or (P(path).name!='SKILL.md' and not s.get('native_name')):raise ValueError('This entry must remain a reference, support file, link or entitled surface')
 source=acquire(s['source_repository'],s['revision']);source_leaf=source/safe_relative(path).parent
 if not (source/safe_relative(path)).is_file():raise ValueError('Pinned source entry is missing')
 # The explicit builder defines lawful closure and exact patches. No generic "append override" patch.
 sys.path.insert(0,str(ROOT/'lib'))
 from skill_build import materialize
 pub=STATE/'build/skills'/id;pub.mkdir(parents=True,exist_ok=True)
 with lock(pub/'.build.lock'):
  with tempfile.TemporaryDirectory(prefix='.stage-',dir=pub) as tmp:
   out=P(tmp)/'release';out.mkdir();support={}
   if id=='P001' and P(path).parent.name=='codebase-design':
    for ref in manifest()['skills']:
     if ref['candidate_id']==id and ref['delivery']=='selective-merge reference':support[ref['source_repository']]=acquire(ref['source_repository'],ref['revision'])
   entry_dir=materialize(source,out,s,c,manifest(),support) or '.'
   for f in out.rglob('*'):
    if f.is_symlink():raise ValueError('Linked closure is not allowed')
   files=tree(out);digest=sha(json.dumps(files,sort_keys=True).encode());name=shelf_name(id,path,s['source_repository'])
   receipt={'entry_dir':entry_dir,'builder_sha256':builder_identity(),'candidate_id':id,'source_repository':s['source_repository'],'revision':s['revision'],'source_path':path,'delivery':s['delivery'],'deployment':c['deployment'],'name':name,'files':files,'content_sha256':digest,'manifest_sha256':sha((ROOT/'registry/manifest.json').read_bytes())}
   dump(out/'.nstack-release.json',receipt);dest=pub/sha(json.dumps(receipt,sort_keys=True).encode())
   if dest.exists():verify_release(dest)
   else:
    for f in out.rglob('*'):f.chmod(0o555 if f.is_dir() or f.stat().st_mode & 0o111 else 0o444)
    os.rename(out,dest);dest.chmod(0o555)
   dump(STATE/'publisher-index'/dest.name,{'receipt_sha256':sha((dest/'.nstack-release.json').read_bytes()),'release':str(dest)})
   return dest

def registered_release(release):
 release=P(release).resolve(strict=True);r=verify_release(release)
 if r.get('builder_sha256')!=builder_identity():raise ValueError('Superseded build recipe; rebuild from the reviewed current patch set')
 c=component(r['candidate_id']);s=leaf(c['id'],r['source_path'])
 for field in ('source_repository','revision','delivery'):
  if r.get(field)!=s[field]:raise ValueError('Release source tuple differs from registry')
 if r.get('deployment')!=c['deployment'] or r.get('manifest_sha256')!=sha((ROOT/'registry/manifest.json').read_bytes()):raise ValueError('Stale release manifest')
 sys.path.insert(0,str(ROOT/'lib'));from closure import needs
 from patch_native34 import handles as handles34,entry as entry34
 expected_entry=entry34(s) if handles34(s) else str(P(s['source_path']).parent) if needs(s) or (c['id']=='P343' and P(s['source_path']).parent.name in ('prospecting','cold-email')) else '.'
 if r.get('entry_dir','.')!=expected_entry:raise ValueError('Unexpected entry directory for this selected leaf')
 name=shelf_name(c['id'],s['source_path'],s['source_repository'])
 if r.get('name')!=name or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,127}',name):raise ValueError('Invalid effective shelf name')
 expected=STATE/'build/skills'/c['id']/release.name
 if release!=expected.resolve() or not release.is_relative_to((STATE/'build/skills').resolve()):raise ValueError('Release outside publisher build root')
 index=STATE/'publisher-index'/release.name
 if not index.is_file() or index.is_symlink():raise ValueError('Release lacks publisher provenance')
 seal=load(index)
 if seal!={'receipt_sha256':sha((release/'.nstack-release.json').read_bytes()),'release':str(release)}:raise ValueError('Publisher provenance changed')
 return r,c,s

def project_paths(project):
 project=P(project).resolve(strict=True)
 if not project.is_dir() or project==P.home().resolve() or STATE.resolve().is_relative_to(project) or project.is_relative_to(STATE.resolve()) or any(project.is_relative_to(P.home()/root) for root in ('.codex','.agents')):raise ValueError('A bounded project outside the private state and home root is required')
 for rel in ('.nstack','.agents','.agents/skills'):
  p=project/rel
  if p.resolve()!=p:raise ValueError('Linked project shelf or journal')
 for rel in ('.nstack/activations.json','.nstack/publish.lock'):
  if (project/rel).is_symlink():raise ValueError('Linked project ownership record')
 return project

def journal_paths(project):
 st=project.stat();identity={'project':str(project),'device':st.st_dev,'inode':st.st_ino}
 root=STATE/'project-owners'/sha(json.dumps(identity,sort_keys=True).encode())
 return root,identity

def activation_rows(project):
 root,identity=journal_paths(project);file=root/'activations.json'
 if file.is_symlink():raise ValueError('Linked authoritative journal')
 if not file.exists():return {}
 record=load(file)
 if record.get('identity')!=identity:raise ValueError('Project publisher identity differs')
 return record['entries']

def save_activations(project,entries):
 root,identity=journal_paths(project)
 dump(root/'activations.json',{'identity':identity,'entries':entries})
 # Do not write a privileged mirror through a worker-writable directory.
 # `verify` returns inspection JSON for the worker to save in its own scope.

def publish(project,release,gate=None):
 project=project_paths(project);release=P(release).resolve(strict=True);r,c,s=registered_release(release)
 if c['deployment']=='consult':raise ValueError('Consult entries cannot be activated')
 if c['deployment'] in ('trial','substitute'):
  raise ValueError(c['deployment']+' remains locked until its per-ID acceptance verifier is implemented; a generic gate cannot authorize it')
 target=release/safe_relative(r.get('entry_dir','.'))
 shelf=project/'.agents/skills'
 if shelf.resolve()!=shelf:raise ValueError('Project shelf or parent is linked')
 shelf.mkdir(parents=True,exist_ok=True);dest=shelf/r['name'];record=project/'.nstack/activations.json'
 owner,_=journal_paths(project)
 with lock(owner/'publish.lock'):
  entries=activation_rows(project)
  if dest.is_symlink() and dest.resolve()==target:
   prior=entries.get(r['name'])
   if not prior or prior.get('release')!=str(release) or prior.get('content_sha256')!=r['content_sha256']:raise ValueError('Matching link has no matching ownership journal')
   if prior.get('phase')!='active':
    prior['phase']='active';save_activations(project,entries)
   return str(dest)
  if dest.exists() or dest.is_symlink():raise ValueError('Shelf destination already exists; deactivate its recorded release first')
  # Write-ahead journal survives interruption between journal and link.
  entries[r['name']]={'release':str(release),'content_sha256':r['content_sha256'],'target':str(target),'phase':'prepared'};save_activations(project,entries)
  dest.symlink_to(target,target_is_directory=True)
  entries[r['name']]['phase']='active';save_activations(project,entries)
 return str(dest)

def deactivate(project,name):
 if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,127}',name):raise ValueError('Invalid shelf name')
 project=project_paths(project);record=project/'.nstack/activations.json';shelf=project/'.agents/skills';dest=shelf/name
 owner,_=journal_paths(project)
 with lock(owner/'publish.lock'):
  entries=activation_rows(project);r=entries.get(name)
  if r is None:raise ValueError('No nstack ownership record for '+name)
  if dest.is_symlink() and str(dest.resolve())==r.get('target',r['release']):dest.unlink()
  elif dest.exists() or dest.is_symlink():raise ValueError('Refusing to remove a changed or unowned shelf entry')
  del entries[name];save_activations(project,entries)

def verify(project):
 project=project_paths(project);rows=activation_rows(project)
 for name,r in rows.items():
  if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,127}',name):raise ValueError('Invalid journal name')
  release=P(r['release']);actual,_,_=registered_release(release)
  if r.get('phase')!='active' or r.get('content_sha256')!=actual['content_sha256']:raise ValueError('Unreconciled activation or digest mismatch')
  dest=project/'.agents/skills'/name
  if not dest.is_symlink() or dest.resolve()!=(release/safe_relative(actual.get('entry_dir','.'))):raise ValueError('Incomplete activation: '+name)
 return {'project':str(project),'active':list(rows),'verified':True}

def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='cmd',required=True)
 a=sub.add_parser('search');a.add_argument('terms',nargs='+');a.add_argument('--all',action='store_true');a.add_argument('--limit',type=int,default=12)
 a=sub.add_parser('show');a.add_argument('id')
 a=sub.add_parser('route');a.add_argument('id')
 a=sub.add_parser('inventory');a.add_argument('project',nargs='?',default=str(P.cwd()));a.add_argument('--binary');a.add_argument('--plugins',action='store_true')
 a=sub.add_parser('workspace');a.add_argument('id');a.add_argument('project');a.add_argument('--fresh',action='store_true')
 a=sub.add_parser('retire-workspace');a.add_argument('id');a.add_argument('project')
 a=sub.add_parser('source');a.add_argument('id')
 a=sub.add_parser('build');a.add_argument('id');a.add_argument('path')
 a=sub.add_parser('activate');a.add_argument('project');a.add_argument('release');a.add_argument('--gate')
 a=sub.add_parser('deactivate');a.add_argument('project');a.add_argument('name')
 a=sub.add_parser('verify');a.add_argument('project')
 a=sub.add_parser('publisher');a.add_argument('project')
 a=sub.add_parser('project-init');a.add_argument('project');a.add_argument('--trust',action='store_true')
 a=sub.add_parser('project-remove');a.add_argument('project')
 for command in ['commission','run','check','remove-runtime']:
  a=sub.add_parser(command);a.add_argument('id');a.add_argument('operation');
  if command=='run':a.add_argument('arguments',nargs=argparse.REMAINDER)
 a=sub.add_parser('doctor')
 a=sub.add_parser('knowledge');a.add_argument('action',choices=['set','read','delete']);a.add_argument('project');a.add_argument('id');a.add_argument('--claim');a.add_argument('--source')
 args=p.parse_args()
 try:
  if args.cmd=='search':
   rows=load(ROOT/'registry/discovery.json');terms=[t.lower() for t in args.terms]
   result=[]
   for r in rows:
    text=json.dumps(r).lower();score=sum(term in text for term in terms)
    if score and (args.all or r['admission'] not in ('excluded','consult')):result.append((score,r))
   if not 1<=args.limit<=535:raise ValueError('Search limit must be between 1 and 535')
   print(json.dumps([r for _,r in sorted(result,key=lambda x:-x[0])][:args.limit],indent=2))
  elif args.cmd=='show':
   c=component(args.id);rows=[]
   for file in (STATE/'publisher-index').glob('*'):
    try:
     seal=load(file);path=P(seal['release']);summary=load(path/'.nstack-release.json')
     if summary.get('candidate_id')!=args.id:continue
     r,_,_=registered_release(path)
     if r['candidate_id']==args.id:rows.append({'path':r['source_path'],'release':seal['release'],'name':r['name']})
    except (OSError,ValueError,KeyError):continue
   routes=load(ROOT/'registry/routes.json') if (ROOT/'registry/routes.json').is_file() else {}
   print(json.dumps({**c,'selected_paths':[s for s in manifest()['skills'] if s['candidate_id']==args.id],'staged_builds':rows,'operation_recipes':[load(p) for p in (ROOT/'recipes'/args.id).rglob('recipe.json')],'native_activation_route':routes.get(args.id)},indent=2))
  elif args.cmd=='route':
   component(args.id);print(json.dumps(load(ROOT/'registry/routes.json')[args.id],indent=2))
  elif args.cmd=='inventory':
   sys.path.insert(0,str(ROOT/'lib'));import native_inventory
   print(json.dumps(native_inventory.inspect(args.project,args.binary,args.plugins),indent=2))
  elif args.cmd in ('workspace','retire-workspace'):
   sys.path.insert(0,str(ROOT/'lib'));import build_workspace
   print(json.dumps(build_workspace.prepare(sys.modules[__name__],args.id,args.project,getattr(args,'fresh',False),args.cmd=='retire-workspace'),indent=2))
  elif args.cmd=='source':
   c=component(args.id)
   if c['deployment']=='consult':raise ValueError('Consult only: follow read-only source locator')
   if c['implementation_mode']=='official plugin' or not isinstance(c.get('revision'),str) or not re.fullmatch(r'[0-9a-f]{40}',c['revision']):raise ValueError('Use the registered official/platform locator and its entitlement/version procedure; no source checkout is authorized by this operation')
   print(acquire(c['repository'],c['revision']))
  elif args.cmd=='build':print(build(args.id,args.path))
  elif args.cmd=='activate':print(publish(args.project,args.release,args.gate))
  elif args.cmd=='deactivate':deactivate(args.project,args.name);print('Deactivated '+args.name)
  elif args.cmd=='verify':print(json.dumps(verify(args.project)))
  elif args.cmd=='publisher':
   sys.path.insert(0,str(ROOT/'lib'));import project_publisher
   project_publisher.serve(sys.modules[__name__],args.project)
  elif args.cmd in ('project-init','project-remove'):
   sys.path.insert(0,str(ROOT/'lib'));import project_setup
   print(json.dumps(project_setup.configure(sys.modules[__name__],args.project,args.cmd=='project-remove',getattr(args,'trust',False)),indent=2))
  elif args.cmd in ('commission','run','check','remove-runtime'):
   sys.path.insert(0,str(ROOT/'lib'));import runtime
   if args.cmd=='commission':print(json.dumps(runtime.commission(sys.modules[__name__],args.id,args.operation),indent=2))
   elif args.cmd=='remove-runtime':print(json.dumps(runtime.remove(sys.modules[__name__],args.id,args.operation),indent=2))
   elif args.cmd=='check':print(json.dumps(runtime.check(sys.modules[__name__],args.id,args.operation),indent=2))
   else:runtime.invoke(sys.modules[__name__],args.id,args.operation,[a for a in args.arguments if a!='--'])
  elif args.cmd=='knowledge':
   sys.path.insert(0,str(ROOT/'lib'));import knowledge
   if args.action=='read':result=knowledge.recall(args.project,args.id)
   else:
    if args.action=='set' and (not args.claim or not args.source):raise ValueError('set requires claim and source')
    result=knowledge.change(args.project,args.id,args.claim,args.source,args.action=='delete',dump)
   print(json.dumps(result,indent=2))
  elif args.cmd=='doctor':
   m=manifest();print(json.dumps({'registry':str(ROOT/'registry/manifest.json'),'manifest_version':m['version'],'components':len(m['components']),'paths':len(m['skills']),'decisions':len(load(ROOT/'registry/discovery.json')),'state':str(STATE),'codex':shutil.which('codex'),'git':shutil.which('git'),'python':sys.version.split()[0]},indent=2))
 except (ValueError,OSError,subprocess.CalledProcessError) as e:p.exit(1,str(e)+'\n')
if __name__=='__main__':main()
