"""Journaled same-volume profile changes; fail closed on concurrent or later edits."""
import contextlib,ctypes,errno,fcntl,hashlib,json,os,pathlib,shutil,stat,subprocess,sys,tempfile
P=pathlib.Path

def raw_xattrs(path):
 if sys.platform!='darwin':return {name:os.getxattr(path,name,follow_symlinks=False) for name in os.listxattr(path,follow_symlinks=False)}
 lib=ctypes.CDLL('/usr/lib/libSystem.B.dylib',use_errno=True);lib.listxattr.argtypes=[ctypes.c_char_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_int];lib.listxattr.restype=ctypes.c_ssize_t;lib.getxattr.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.c_uint32,ctypes.c_int];lib.getxattr.restype=ctypes.c_ssize_t
 size=lib.listxattr(os.fsencode(path),None,0,1)
 if size<0:raise OSError(ctypes.get_errno(),'Cannot read extended attributes')
 names=ctypes.create_string_buffer(size);count=lib.listxattr(os.fsencode(path),names,size,1)
 if count<0:raise OSError(ctypes.get_errno(),'Cannot list extended attributes')
 result={}
 for name in names.raw[:count].split(b'\0'):
  if not name:continue
  length=lib.getxattr(os.fsencode(path),name,None,0,0,1)
  if length<0:raise OSError(ctypes.get_errno(),'Cannot size extended attribute')
  value=ctypes.create_string_buffer(length);actual=lib.getxattr(os.fsencode(path),name,value,length,0,1)
  if actual<0:raise OSError(ctypes.get_errno(),'Cannot read extended attribute')
  result[os.fsdecode(name)]=value.raw[:actual]
 return result

def metadata(path):
 # macOS assigns com.apple.provenance to the new file identity during copy.
 # Do not overwrite that security tag to make a copy compare equal. All other
 # extended attributes, ACLs, flags, ownership and file bytes remain exact.
 s=path.lstat();attrs={name:hashlib.sha256(value).hexdigest() for name,value in raw_xattrs(path).items() if name!='com.apple.provenance'}
 acl=''
 if sys.platform=='darwin':
  lib=ctypes.CDLL('/usr/lib/libSystem.B.dylib',use_errno=True);getter=lib.acl_get_link_np if path.is_symlink() else lib.acl_get_file;getter.argtypes=[ctypes.c_char_p,ctypes.c_int];getter.restype=ctypes.c_void_p;lib.acl_to_text.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_ssize_t)];lib.acl_to_text.restype=ctypes.c_void_p;lib.acl_free.argtypes=[ctypes.c_void_p]
  handle=getter(os.fsencode(path),0x100)
  if handle:
   length=ctypes.c_ssize_t();raw=lib.acl_to_text(handle,ctypes.byref(length))
   if raw:acl=ctypes.string_at(raw,length.value).decode();lib.acl_free(raw)
   lib.acl_free(handle)
  elif ctypes.get_errno() not in (0,errno.ENOENT):raise OSError(ctypes.get_errno(),'Cannot read filesystem ACL')
 return {'mode':stat.S_IMODE(s.st_mode),'uid':s.st_uid,'gid':s.st_gid,'flags':getattr(s,'st_flags',0),'xattrs':attrs,'acl_sha256':hashlib.sha256(acl.encode()).hexdigest()}

def fingerprint(path):
 path=P(path)
 if path.is_symlink():return {'kind':'link','target':os.readlink(path),'metadata':metadata(path)}
 if not path.exists():return {'kind':'absent'}
 if path.is_file():return {'kind':'file','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'metadata':metadata(path)}
 if path.is_dir():return {'kind':'directory','metadata':metadata(path),'entries':{str(f.relative_to(path)):fingerprint(f) for f in sorted(path.rglob('*'))}}
 raise ValueError('Unsupported target type')

def replace_entry(source,target):
 """Atomically exchange unlike directory types; retain the displaced entry."""
 source=P(source);target=P(target)
 source_dir=source.is_dir() and not source.is_symlink()
 target_dir=target.is_dir() and not target.is_symlink()
 if (target.exists() or target.is_symlink()) and source_dir!=target_dir:
  # Darwin's RENAME_SWAP and Linux's RENAME_EXCHANGE both use flag 2.
  # No delete-then-link gap, including when restoring an original directory.
  lib=ctypes.CDLL('/usr/lib/libSystem.B.dylib' if sys.platform=='darwin' else None,use_errno=True)
  if sys.platform=='darwin':
   fn=lib.renamex_np;fn.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_uint];args=(os.fsencode(source),os.fsencode(target),2)
  elif sys.platform.startswith('linux') and hasattr(lib,'renameat2'):
   fn=lib.renameat2;fn.argtypes=[ctypes.c_int,ctypes.c_char_p,ctypes.c_int,ctypes.c_char_p,ctypes.c_uint];args=(-100,os.fsencode(source),-100,os.fsencode(target),2)
  else:raise ValueError('Atomic directory exchange is unavailable; original entry left untouched')
  fn.restype=ctypes.c_int
  if fn(*args)!=0:raise OSError(ctypes.get_errno(),'Atomic directory exchange failed; original entry retained')
  return True
 os.replace(source,target);return False

def atomic_json(path,data):
 path=P(path);path.parent.mkdir(parents=True,exist_ok=True);raw=json.dumps(data,sort_keys=True,indent=2)+'\n'
 if path.exists() and path.read_text()==raw:return
 fd,name=tempfile.mkstemp(prefix='.'+path.name,dir=path.parent)
 with os.fdopen(fd,'w') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 os.chmod(name,0o600);os.replace(name,path)

def copy(src,dest):
 src=P(src);dest=P(dest);dest.parent.mkdir(parents=True,exist_ok=True)
 if src.is_symlink() and sys.platform=='darwin':subprocess.run(['/bin/cp','-a',str(src),str(dest)],check=True)
 elif src.is_symlink():dest.symlink_to(os.readlink(src));shutil.copystat(src,dest,follow_symlinks=False)
 elif sys.platform=='darwin':subprocess.run(['/usr/bin/ditto','--rsrc','--extattr','--acl',str(src),str(dest)],check=True)
 elif src.is_dir():shutil.copytree(src,dest,symlinks=True)
 else:shutil.copy2(src,dest)
 if sys.platform=='darwin':
  # ditto can omit UF_TRACKED on document files. Preserve native flags through
  # the supported owner API; a denial fails the copy rather than being ignored.
  nodes=sorted(src.rglob('*'),key=lambda p:len(p.parts),reverse=True)+[src] if src.is_dir() and not src.is_symlink() else [src]
  for node in nodes:
   target=dest/node.relative_to(src) if node!=src else dest
   flags=node.lstat().st_flags
   if target.lstat().st_flags!=flags:os.chflags(target,flags,follow_symlinks=False)

def same(path,expected):
 if fingerprint(path)!=expected:raise ValueError('Concurrent change or rollback conflict at '+str(path))

class Transaction:
 def __init__(self,run):
  self.run=P(run).resolve();self.run.mkdir(parents=True,exist_ok=True,mode=0o700);self.run.chmod(0o700);self.file=self.run/'journal.json';self.rows=[];self.held=False
 def save(self):atomic_json(self.file,self.rows)
 @contextlib.contextmanager
 def lock(self):
  # All runs in one state/runs parent serialize the live profile, not just a run ID.
  with (self.run.parent/'.nstack-profile-writer.lock').open('a') as f:
   fcntl.flock(f,fcntl.LOCK_EX);self.rows=json.loads(self.file.read_text()) if self.file.exists() else [];self.held=True
   try:yield
   finally:self.held=False
 def require_lock(self):
  if not self.held:raise ValueError('Profile transaction requires the writer lock')
 def preserve_attempt(self,path,label):
  path=P(path)
  if not path.exists() and not path.is_symlink():return
  folder=self.run/'preparation-retries';folder.mkdir(exist_ok=True)
  fd,name=tempfile.mkstemp(prefix=label+'-',dir=folder);os.close(fd);os.unlink(name);os.rename(path,name)
 def complete_backup(self,row):
  backup=P(row['backup']);path=P(row['path']);same(path,row['before'])
  if row['before']['kind']!='absent':
   if fingerprint(backup)!=row['before']:
    self.preserve_attempt(backup,'backup');copy(path,backup);same(backup,row['before']);same(path,row['before'])
  row['phase']='prepared';self.save()
 def prepare(self,path,desired,kind='replace',config=None,expected=None):
  self.require_lock();path=P(path).absolute()
  if path.parent.resolve()!=path.parent:raise ValueError('Linked transaction target parent')
  if expected is not None:same(path,expected)
  for row in reversed(self.rows):
   if row['path']==str(path) and row['phase']!='rolled-back':
    if row['after']!=desired:raise ValueError('Existing transaction has a different desired state')
    if row['phase']=='backup-preparing':self.complete_backup(row)
    return row
  before=fingerprint(path);backup=self.run/'before'/str(len(self.rows))
  row={'path':str(path),'before':before,'after':desired,'backup':str(backup),'kind':kind,'config':config,'phase':'backup-preparing'};self.rows.append(row);self.save();self.complete_backup(row);return row
 def stage_file(self,path,data,mode=0o644,expected=None):
  self.require_lock();path=P(path).absolute();baseline=fingerprint(path)
  if expected is not None:same(path,expected)
  staging=self.run/'file-stages';staging.mkdir(exist_ok=True);fd,name=tempfile.mkstemp(prefix=path.name+'-',dir=staging);os.close(fd);stage=P(name)
  try:
   if baseline['kind']=='file':copy(path,stage);same(path,baseline)
   # Only the private staging copy needs temporary owner-write access.
   stage.chmod(stat.S_IMODE(stage.stat().st_mode)|stat.S_IWUSR)
   with stage.open('wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
   stage.chmod(mode);return stage,baseline,fingerprint(stage)
  except BaseException:
   if stage.exists():stage.unlink()
   raise
 def replace_file(self,path,data,mode=0o644,config=None,expected=None,prepared=None):
  self.require_lock();path=P(path).absolute()
  stage,baseline,desired=prepared if prepared is not None else self.stage_file(path,data,mode,expected)
  if expected is not None:same(path,expected)
  same(path,baseline);same(stage,desired);path.parent.mkdir(parents=True,exist_ok=True)
  try:
   row=self.prepare(path,desired,'config' if config else 'replace',config,baseline)
   if config:
    after_image=self.run/'after'/str(self.rows.index(row));after_image.parent.mkdir(exist_ok=True)
    if fingerprint(after_image)!=desired:
     self.preserve_attempt(after_image,'after-image');copy(stage,after_image);same(after_image,desired)
    row['config_after']=str(after_image);self.save()
   if fingerprint(path)!=desired:
    same(path,row['before'])
    if path.parent.stat().st_dev!=stage.parent.stat().st_dev:raise ValueError('Replacement requires same-volume private state')
    os.replace(stage,path);same(path,desired)
   row.pop('rollback_result',None);row.pop('rollback_expected',None);row['phase']='applied';self.save()
  finally:
   if stage.exists():stage.unlink()
 def link(self,path,target,expected=None):
  self.require_lock();path=P(path).absolute();baseline=fingerprint(path)
  if expected is not None:same(path,expected)
  if baseline['kind']=='link' and baseline['target']==str(target):desired=baseline;stage=None
  else:
   path.parent.mkdir(parents=True,exist_ok=True);staging=self.run/'file-stages';staging.mkdir(exist_ok=True);fd,name=tempfile.mkstemp(prefix=path.name+'-',dir=staging);os.close(fd);os.unlink(name);stage=P(name);stage.symlink_to(target)
   if baseline['kind']=='link':shutil.copystat(path,stage,follow_symlinks=False)
   desired=fingerprint(stage)
  try:
   row=self.prepare(path,desired,expected=baseline)
   if fingerprint(path)!=desired:
    same(path,row['before'])
    if path.parent.stat().st_dev!=stage.parent.stat().st_dev:raise ValueError('Replacement requires same-volume private state')
    swapped=replace_entry(stage,path)
    if swapped:
     if fingerprint(stage)!=row['before']:
      same(path,desired);replace_entry(stage,path)
      raise ValueError('Concurrent change to replaced skill directory; restored current bytes')
     row['displaced_entry']=str(stage)
    same(path,desired)
   row.pop('rollback_result',None);row.pop('rollback_expected',None);row['phase']='applied';self.save()
  finally:
   if stage is not None and (stage.is_symlink() or stage.is_file()):stage.unlink()
 def retire(self,path,expected=None):
  self.require_lock();path=P(path).absolute();row=self.prepare(path,{'kind':'absent'},'retire',expected=expected)
  if fingerprint(path)!=row['after']:
   same(path,row['before']);retained=self.run/'retired'/str(self.rows.index(row));retained.parent.mkdir(parents=True,exist_ok=True)
   if retained.exists() or retained.is_symlink():
    same(retained,row['before']);fd,name=tempfile.mkstemp(prefix=str(self.rows.index(row))+'-',dir=retained.parent);os.close(fd);os.unlink(name);retained=P(name)
   if path.parent.stat().st_dev!=retained.parent.stat().st_dev:raise ValueError('Private retirement state is on a different volume')
   row['retained']=str(retained);self.save();same(path,row['before']);os.rename(path,retained);same(retained,row['before'])
  row.pop('rollback_result',None);row.pop('rollback_expected',None);row['phase']='applied';self.save()
 def rollback(self):
  self.require_lock();import config_merge as cm
  for index in reversed(range(len(self.rows))):
   row=self.rows[index];path=P(row['path']);current=fingerprint(path)
   if row['phase']=='rolled-back':continue
   if row.get('rollback_result')==current:row['phase']='rolled-back';self.save();continue
   if row['phase']=='rollback-prepared':
    same(path,row['rollback_expected']);self._finish_rollback(row);continue
   if current==row['before']:row['phase']='rolled-back';self.save();continue
   stage=self.run/'rollback-stage'/str(index);stage.parent.mkdir(parents=True,exist_ok=True)
   if stage.exists() or stage.is_symlink():
    if row['phase']!='rollback-staging' or row.get('rollback_stage')!=str(stage):raise ValueError('Unexpected rollback stage')
    same(path,row['rollback_expected']);self.preserve_attempt(stage,'rollback')
   row.update(rollback_expected=current,rollback_stage=str(stage),phase='rollback-staging');self.save()
   if row['kind']=='config' and current['kind']=='file' and current!=row['after']:
    if row['before']['kind'] not in ('file','absent'):raise ValueError('Changed replacement of linked config requires manual reconciliation; preserving both current bytes and original link backup')
    before=P(row['backup']).read_text() if row['before']['kind']=='file' else '';after=P(row['config_after']).read_text();settings=row['config'];updates=[(p,cm.MISSING if v=={'nstack_absent':True} else v) for p,v in settings['updates']]
    merged=cm.inverse(path.read_text(),before,after,updates,settings['retire']);same(path,current);copy(path,stage)
    with stage.open('w') as f:f.write(merged);f.flush();os.fsync(f.fileno())
    original_meta=row['before'].get('metadata',{});installed_meta=row['after'].get('metadata',{});current_meta=current['metadata']
    if original_meta.get('mode') is not None and current_meta['mode']==installed_meta.get('mode'):stage.chmod(original_meta['mode'])
    result=fingerprint(stage)
   else:
    same(path,row['after'])
    if row['before']['kind']=='absent':result={'kind':'absent'}
    else:copy(row['backup'],stage);same(stage,row['before']);result=fingerprint(stage)
   row.update(rollback_expected=current,rollback_result=result,rollback_stage=str(stage),phase='rollback-prepared');self.save();self._finish_rollback(row)
 def _finish_rollback(self,row):
  path=P(row['path']);stage=P(row['rollback_stage']);same(path,row['rollback_expected'])
  if row['rollback_result']['kind']=='absent':
   if path.is_dir() and not path.is_symlink():path.rmdir()
   elif path.exists() or path.is_symlink():path.unlink()
  else:
   same(stage,row['rollback_result'])
   if path.parent.stat().st_dev!=stage.parent.stat().st_dev:raise ValueError('Restore must stay on one volume')
   same(path,row['rollback_expected']);replace_entry(stage,path);same(path,row['rollback_result'])
  row['phase']='rolled-back';self.save()
