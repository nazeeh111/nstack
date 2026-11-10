"""Project-scoped canonical records with generations, provenance and tombstones."""
import hashlib,json,pathlib,uuid,datetime,contextlib,fcntl,os
P=pathlib.Path

def root(project):
 project=P(project).resolve(strict=True)
 if not P.cwd().resolve().is_relative_to(project):raise ValueError('Knowledge retrieval requires the current project scope')
 p=project/'.nstack'
 if p.resolve()!=p or (p/'knowledge').resolve()!=p/'knowledge':raise ValueError('Linked knowledge store')
 return project,p

def identity(project,writer):
 project,p=root(project);file=p/'project.json'
 if file.is_symlink():raise ValueError('Linked project identity')
 if file.exists():return json.loads(file.read_text())['scope']
 if not writer:return None
 scope=str(uuid.uuid4());writer(file,{'scope':scope});return scope

@contextlib.contextmanager
def writer_lock(project):
 project,p=root(project);p.mkdir(exist_ok=True)
 file=p/'knowledge-writer.lock'
 # Do not follow a substituted lock outside the owner project.
 fd=os.open(file,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'a') as handle:
  fcntl.flock(handle,fcntl.LOCK_EX)
  root(project)
  yield

def change(project,id,claim,source,delete,writer,expected_generation=0):
 import re
 if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,100}',id):raise ValueError('Invalid fact ID')
 if type(expected_generation) is not int or expected_generation<0:raise ValueError('Invalid expected generation')
 with writer_lock(project):
  project,p=root(project);f=p/'knowledge'/f'{id}.json'
  if f.is_symlink():raise ValueError('Linked canonical record')
  old=json.loads(f.read_text()) if f.exists() else {}
  if old.get('generation',0)!=expected_generation:raise ValueError('Knowledge generation changed; reread before correcting')
  scope=identity(project,writer)
  if old and old['scope']!=scope:raise ValueError('Wrong knowledge scope')
  evidence=None
  if not delete:
   source=P(source).resolve(strict=True)
   if not source.is_relative_to(project):raise ValueError('Canonical evidence must belong to this project')
   evidence={'path':str(source.relative_to(project)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
  record={'id':id,'scope':scope,'generation':expected_generation+1,'state':'deleted' if delete else 'current','claim':None if delete else claim,'source':evidence,'supersedes_generation':old.get('generation'),'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
  writer(f,record);return record

def recall(project,id):
 import re
 if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,100}',id):raise ValueError('Invalid fact ID')
 project,p=root(project);f=p/'knowledge'/f'{id}.json'
 if f.is_symlink():raise ValueError('Linked canonical record')
 if not f.exists():return {'id':id,'state':'absent'}
 record=json.loads(f.read_text())
 if record['scope']!=identity(project,None):raise ValueError('Wrong knowledge scope')
 if record['state']=='deleted':return {'id':id,'state':'deleted','generation':record['generation']}
 source=record['source'];file=(project/source['path']).resolve()
 if not file.is_relative_to(project) or not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest()!=source['sha256']:raise ValueError('Knowledge source changed; reread and correct the canonical record')
 return {**record,'canonical_record':str(f.relative_to(project))}
