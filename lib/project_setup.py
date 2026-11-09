"""Reversible, project-local publisher registration using owned TOML keys."""
import hashlib,os,pathlib,sys
from transaction import Transaction,fingerprint,same
import config_merge as cm

def configure(n,project,remove=False,trust=False):
 p=n.project_paths(project);run=n.STATE/'project-config'/hashlib.sha256(str(p).encode()).hexdigest();tx=Transaction(run)
 with tx.lock():
  if remove:
   result=n.verify(p)
   if result['active']:raise ValueError('Deactivate the recorded project leaves before removing its publisher')
   tx.rollback();return {'project':str(p),'publisher':'removed; later unrelated config preserved'}
  path=p/'.codex/config.toml'
  if path.is_symlink() or path.parent.is_symlink():raise ValueError('Linked project config')
  home=pathlib.Path(os.environ.get('CODEX_HOME',pathlib.Path.home()/'.codex'));config=home/'config.toml'
  if trust and config.is_symlink():raise ValueError('Linked user config; reconcile explicitly')
  if trust and config.parent.resolve()!=config.parent:raise ValueError('Linked user config parent; reconcile explicitly')
  trust_baseline=fingerprint(config) if trust else None
  trust_before=config.read_text() if trust and config.exists() else ''
  baseline=fingerprint(path);before=path.read_text() if path.exists() else '';same(path,baseline)
  existing=cm.tomllib.loads(before).get('mcp_servers',{}).get('nstack_project')
  if existing is not None and not any(row['path']==str(path) and row['phase']!='rolled-back' for row in tx.rows):raise ValueError('Existing nstack_project registration is not owned by this setup')
  updates=[(['mcp_servers','nstack_project','command'],sys.executable),(['mcp_servers','nstack_project','args'],[str(n.ROOT/'nstack.py'),'publisher',str(p)]),(['mcp_servers','nstack_project','env','NSTACK_STATE'],str(n.STATE)),(['mcp_servers','nstack_project','startup_timeout_sec'],120)]
  after=cm.apply(before,updates,[]);spec={'updates':[[k,v] for k,v in updates],'retire':[]}
  if trust:
   trust_updates=[(['projects',str(p),'trust_level'],'trusted')];trust_after=cm.apply(trust_before,trust_updates,[])
  for target,expected in [(path,baseline)]+([(config,trust_baseline)] if trust else []):
   if expected['kind'] not in ('file','absent'):raise ValueError('Unsupported project configuration destination')
   parent=target.parent
   while not parent.exists():parent=parent.parent
   if parent.resolve()!=parent or not parent.is_dir() or parent.stat().st_dev!=run.stat().st_dev or not os.access(parent,os.W_OK):raise ValueError('Unsupported configuration parent or transaction volume')
   same(target,expected)
  tx.replace_file(path,after.encode(),0o600,spec,expected=baseline)
  if trust:tx.replace_file(config,trust_after.encode(),0o600,{'updates':[[k,v] for k,v in trust_updates],'retire':[]},expected=trust_baseline)
 return {'project':str(p),'publisher':'registered for fresh normally launched sessions','trusted':trust,'rollback_run':str(run)}
