"""Acquire exactly pinned native artifacts without touching the desktop application."""
import hashlib,json,os,pathlib,platform,subprocess,tarfile,tempfile,urllib.request
P=pathlib.Path

def binary_pair(root,state,archives=None):
 if platform.system()!='Darwin' or platform.machine()!='arm64':raise ValueError('This tested bootstrap requires native macOS ARM64; another target needs its exact official 0.167.0 artifacts and target acceptance')
 registry=json.loads((root/'registry/manifest.json').read_text());runtime_locks=json.loads((root/'registry/runtime-locks.json').read_text());host=runtime_locks['codex-code-mode-host'];cli=next(a for a in registry['native_release']['assets'] if a['name']=='codex-aarch64-apple-darwin.tar.gz')
 specs=[{'file':'codex','member':'codex-aarch64-apple-darwin','url':cli['url'],'sha256':cli['digest'].split(':')[1]},{'file':'codex-code-mode-host','member':'codex-code-mode-host-aarch64-apple-darwin','url':host['url'],'sha256':host['sha256']}]
 for spec in specs:spec['binary_sha256']=runtime_locks[spec['file']]['binary_sha256']
 dest=state/'bin/0.167.0';lock=dest/'LOCK.json'
 if lock.exists():
  saved=json.loads(lock.read_text())
  if saved.get('version')!='codex-cli 0.167.0' or saved.get('platform')!='Darwin arm64' or saved.get('files')!=specs:raise ValueError('Cached native receipt differs from exact required artifact set')
  for r in specs:
   binary=dest/r['file']
   if binary.is_symlink() or not binary.is_file() or not os.access(binary,os.X_OK) or hashlib.sha256(binary.read_bytes()).hexdigest()!=r['binary_sha256']:raise ValueError('Pinned native binary changed or missing')
  if subprocess.check_output([str(dest/'codex'),'--version'],text=True).strip()!='codex-cli 0.167.0':raise ValueError('Wrong cached CLI version')
  return dest/'codex'
 dest.parent.mkdir(parents=True,exist_ok=True);cache=state/'cache/native';cache.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='.native-',dir=dest.parent) as tmp:
  out=P(tmp)/'bin';out.mkdir();receipts=[]
  for spec in specs:
   archive=P(archives[spec['file']]) if archives and spec['file'] in archives else cache/(spec['member']+'-0.167.0.tar.gz')
   if not archive.exists():
    fd,name=tempfile.mkstemp(prefix='.download-',dir=cache);os.close(fd)
    try:
     with urllib.request.urlopen(spec['url'],timeout=120) as response,P(name).open('wb') as f:
      while chunk:=response.read(1024*1024):f.write(chunk)
     if hashlib.sha256(P(name).read_bytes()).hexdigest()!=spec['sha256']:raise ValueError('Official native archive digest mismatch')
     os.replace(name,archive)
    finally:
     if P(name).exists():P(name).unlink()
   if hashlib.sha256(archive.read_bytes()).hexdigest()!=spec['sha256']:raise ValueError('Native archive digest mismatch')
   with tarfile.open(archive) as tar:
    members=tar.getmembers()
    if len(members)!=1 or members[0].name!=spec['member'] or not members[0].isfile():raise ValueError('Unexpected native archive members')
    raw=tar.extractfile(members[0]).read()
    if hashlib.sha256(raw).hexdigest()!=spec['binary_sha256']:raise ValueError('Native member digest differs from verified artifact lock')
    (out/spec['file']).write_bytes(raw);(out/spec['file']).chmod(0o755)
   receipts.append({**spec,'binary_sha256':hashlib.sha256(raw).hexdigest()})
  version=subprocess.check_output([str(out/'codex'),'--version'],text=True).strip()
  if version!='codex-cli 0.167.0':raise ValueError('Wrong pinned CLI version')
  (out/'LOCK.json').write_text(json.dumps({'version':version,'platform':'Darwin arm64','files':receipts},indent=2)+'\n');os.rename(out,dest)
  for f in dest.iterdir():f.chmod(0o555 if f.name!='LOCK.json' else 0o444)
  dest.chmod(0o555)
 return dest/'codex'
