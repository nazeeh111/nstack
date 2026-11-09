"""Digest-locked private toolchains. No global PATH or application mutation."""
import hashlib,json,os,pathlib,re,subprocess,tarfile,tempfile,urllib.parse,urllib.request
P=pathlib.Path
def digest(path):
 h=hashlib.sha256()
 with P(path).open('rb') as f:
  while chunk:=f.read(1024*1024):h.update(chunk)
 return h.hexdigest()
def tree(root):
 result={}
 for path in root.rglob('*'):
  if path.is_symlink():raise ValueError('Linked file in private toolchain')
  if path.is_file() and path!=root/'TOOLCHAIN.json':result[str(path.relative_to(root))]=digest(path)
 return result
def unpack(archive,out,prefix):
 total=0;seen=set()
 with tarfile.open(archive) as tar:
  for count,member in enumerate(tar):
   rel=P(member.name)
   if count>50000 or rel.is_absolute() or '..' in rel.parts or not rel.parts or rel.parts[0]!=prefix or not (member.isfile() or member.isdir()):raise ValueError('Unsafe or unexpected toolchain archive member')
   key=str(rel)
   if key in seen:raise ValueError('Duplicate toolchain archive member')
   seen.add(key);total+=member.size
   if total>1024**3:raise ValueError('Toolchain archive exceeds one GiB unpacked budget')
   target=out/P(*rel.parts[1:]) if len(rel.parts)>1 else out
   if member.isdir():target.mkdir(parents=True,exist_ok=True)
   else:
    target.parent.mkdir(parents=True,exist_ok=True)
    with tar.extractfile(member) as src,target.open('xb') as dst:
     while chunk:=src.read(1024*1024):dst.write(chunk)
    target.chmod(0o755 if member.mode&0o111 else 0o644)
 return total
def acquire(n,key):
 if not re.fullmatch(r'[a-z0-9-]+',key):raise ValueError('Invalid build tool key')
 spec=n.load(n.ROOT/'registry/build-tools.json')[key];identity=n.sha(json.dumps(spec,sort_keys=True).encode());dest=n.STATE/'toolchains'/key/identity
 with n.lock(n.STATE/'toolchain-writers'/(key+'.lock')):
  receipt=dest/'TOOLCHAIN.json'
  if dest.exists():
   if not receipt.is_file() or receipt.is_symlink():raise ValueError('Unowned toolchain prefix')
   saved=n.load(receipt)
   if saved['spec_sha256']!=identity or tree(dest)!=saved['files']:raise ValueError('Pinned toolchain contents changed')
   return dest,saved
  url=urllib.parse.urlsplit(spec['url'])
  if url.scheme!='https' or url.username or url.password or not re.fullmatch(r'[0-9a-f]{64}',spec['sha256']):raise ValueError('Verified HTTPS artifact and SHA256 required')
  cache=n.STATE/'cache/toolchain-archives';cache.mkdir(parents=True,exist_ok=True);archive=cache/(spec['sha256']+'.tar.gz')
  if not archive.exists():
   fd,name=tempfile.mkstemp(prefix='.download-',dir=cache);os.close(fd)
   try:
    with urllib.request.urlopen(spec['url'],timeout=120) as response,P(name).open('wb') as f:
     while chunk:=response.read(1024*1024):f.write(chunk)
    if digest(name)!=spec['sha256']:raise ValueError('Official toolchain digest mismatch')
    os.replace(name,archive)
   finally:
    if P(name).exists():P(name).unlink()
  if digest(archive)!=spec['sha256']:raise ValueError('Cached toolchain archive changed')
  dest.parent.mkdir(parents=True,exist_ok=True)
  with tempfile.TemporaryDirectory(prefix='.toolchain-',dir=dest.parent) as temp:
   out=P(temp)/'release';out.mkdir();size=unpack(archive,out,spec['archive_root']);command=[str(out/spec['version_command'][0]),*spec['version_command'][1:]]
   version=subprocess.check_output(command,text=True,env={'PATH':os.environ.get('PATH','/usr/bin:/bin'),'HOME':str(out),'GOENV':'off','GOTOOLCHAIN':'local','GOTELEMETRY':'off'}).strip()
   if spec['expected_version_substring'] not in version:raise ValueError('Toolchain platform/version differs from registered artifact')
   saved={'spec_sha256':identity,'version':version,'archive_sha256':spec['sha256'],'unpacked_bytes':size,'files':tree(out)};n.dump(out/'TOOLCHAIN.json',saved);os.rename(out,dest)
   for p in dest.rglob('*'):p.chmod(0o555 if p.is_dir() or p.stat().st_mode&0o111 else 0o444)
   dest.chmod(0o555)
  return dest,saved
