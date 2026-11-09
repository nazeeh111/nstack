#!/usr/bin/env python3
"""Install only Worktrunk0.81.0 Mac ARM binary in an explicit owned prefix.

No shell integration, hooks, account access, global config or automatic update.
The selected skill source revision is separate from the upstream release commit.
"""
import argparse,hashlib,io,json,pathlib,platform,subprocess,tarfile,urllib.request
VERSION='0.81.0';SHA256='b9c3f2f8071554cf88500466d65d35e18ad5edad5762479a1f14bcddd5ab7882'
URL='https://github.com/max-sixty/worktrunk/releases/download/v0.81.0/worktrunk-aarch64-apple-darwin.tar.xz'

def install(prefix):
 if platform.system()!='Darwin' or platform.machine()!='arm64':raise ValueError('This checked artifact is macOS arm64 only')
 prefix=pathlib.Path(prefix).absolute();prefix.mkdir(parents=True,exist_ok=True)
 receipt=prefix/'provenance.json'
 if receipt.exists():
  r=json.loads(receipt.read_text())
  for rel,expected in r['files'].items():
   p=prefix/rel
   if p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:raise ValueError('Installed Worktrunk changed')
  return r
 if any(prefix.iterdir()):raise ValueError('Use an empty owned prefix')
 with urllib.request.urlopen(URL,timeout=30) as response:raw=response.read(10*1024*1024)
 if hashlib.sha256(raw).hexdigest()!=SHA256:raise ValueError('Worktrunk release checksum mismatch')
 files={}
 with tarfile.open(fileobj=io.BytesIO(raw),mode='r:xz') as archive:
  for member in archive.getmembers():
   name=pathlib.PurePosixPath(member.name).name
   if not member.isfile() or not (name=='wt' or name.upper().startswith(('LICENSE','NOTICE','COPYING'))):continue
   data=archive.extractfile(member).read();out=prefix/name
   if out.exists():raise ValueError('Ambiguous release member')
   out.write_bytes(data);out.chmod(0o755 if name=='wt' else 0o444);files[name]=hashlib.sha256(data).hexdigest()
 binary=prefix/'wt'
 if not binary.is_file() or not any(n.upper().startswith(('LICENSE','NOTICE','COPYING')) for n in files):raise ValueError('Release lacks binary or owning license')
 version=subprocess.check_output([str(binary),'--version'],text=True).strip()
 if VERSION not in version:raise ValueError('Worktrunk binary version mismatch')
 r={'url':URL,'sha256':SHA256,'version':VERSION,'observed':version,'selected_skill_source_revision':'3bf9166a6e3b74db0de25c2a1f9aeeae54d2873a','release_commit':'e42f0f6','source_release_equivalence':'Separate provenance; no claim release was built from selected skill source revision.','files':files,'command':str(binary)}
 receipt.write_text(json.dumps(r,indent=2)+'\n');return r
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prefix',required=True);args=p.parse_args();print(json.dumps(install(args.prefix),indent=2))
