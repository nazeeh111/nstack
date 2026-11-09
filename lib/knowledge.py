"""Project-scoped canonical records with generations, provenance and tombstones."""
import hashlib,json,pathlib,uuid,datetime
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

def change(project,id,claim,source,delete,writer):
 import re
 if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,100}',id):raise ValueError('Invalid fact ID')
 project,p=root(project);scope=identity(project,writer);f=p/'knowledge'/f'{id}.json'
 if f.is_symlink():raise ValueError('Linked canonical record')
 old=json.loads(f.read_text()) if f.exists() else {};generation=old.get('generation',0)+1
 evidence=None
 if not delete:
  source=P(source).resolve(strict=True)
  if not source.is_relative_to(project):raise ValueError('Canonical evidence must belong to this project')
  evidence={'path':str(source.relative_to(project)),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
 record={'id':id,'scope':scope,'generation':generation,'state':'deleted' if delete else 'current','claim':None if delete else claim,'source':evidence,'supersedes_generation':old.get('generation'),'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
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
