#!/usr/bin/env python3
"""Pinned local Google Maps fast-mode runner; no Docker or browser installation."""
import argparse,hashlib,json,math,os,pathlib,platform,subprocess,tempfile,urllib.request
from datetime import datetime,timezone
P=pathlib.Path
VERSION='1.18.2'
REVISION='146aefe83844960bb534f335261a4435783a58cc'
SHA256='c166042f5bd00bc8ae48b9e05ab38dc029b55b8613c4d8ad2602b2f4e6b40ff4'
URL='https://github.com/gosom/google-maps-scraper/releases/download/v1.18.2/google_maps_scraper-1.18.2-darwin-amd64'
STATE=P(os.environ.get('NSTACK_STATE',P.home()/'Library/Application Support/nstack'))
def digest(path):return hashlib.sha256(P(path).read_bytes()).hexdigest()
def install(state=STATE):
 if platform.system()!='Darwin':raise ValueError('This pinned runtime recipe supports macOS only')
 if platform.machine()=='arm64' and subprocess.run(['/usr/bin/arch','-x86_64','/usr/bin/true'],capture_output=True).returncode:
  raise ValueError('The official release needs existing Rosetta on Apple Silicon; this recipe does not install Rosetta or change the machine')
 root=P(state)/'native-tools/google-maps-scraper'/VERSION;root.mkdir(parents=True,exist_ok=True);binary=root/'google_maps_scraper'
 if binary.exists():
  if binary.is_symlink() or digest(binary)!=SHA256:raise ValueError('Installed scraper differs from the pinned release; preserved')
  return binary
 fd,name=tempfile.mkstemp(prefix='.download-',dir=root);os.close(fd);stage=P(name)
 try:
  urllib.request.urlretrieve(URL,stage)
  if digest(stage)!=SHA256:raise ValueError('Official scraper SHA256 mismatch')
  stage.chmod(0o755);os.replace(stage,binary)
 finally:
  if stage.exists():stage.unlink()
 (root/'SOURCE.json').write_text(json.dumps({'repository':'gosom/google-maps-scraper','revision':REVISION,'version':VERSION,'url':URL,'sha256':SHA256,'architecture':'darwin-amd64','license':'MIT'},indent=2)+'\n')
 return binary

def runtime_env():
 # Do not pass proxy, cloud/provider credentials or account environment to the scraper.
 env={k:os.environ[k] for k in ['PATH','LANG','LC_ALL','TMPDIR','TZ'] if k in os.environ}
 env['DISABLE_TELEMETRY']='1';return env

def read_rows(path):
 raw=path.read_text().strip() if path.exists() else ''
 if not raw:return [],0
 try:
  d=json.loads(raw);rows=d if isinstance(d,list) else [d]
  return [r for r in rows if isinstance(r,dict)],sum(not isinstance(r,dict) for r in rows)
 except json.JSONDecodeError:
  rows=[];invalid=0
  for line in raw.splitlines():
   if not line.strip():continue
   try:
    r=json.loads(line)
    if isinstance(r,dict):rows.append(r)
    else:invalid+=1
   except json.JSONDecodeError:invalid+=1
  return rows,invalid

def run_query(binary,query,out,timeout=90,geo=None):
 if not query.strip() or '\n' in query or '\r' in query:raise ValueError('Provide one nonempty public-place query')
 if not 1<=timeout<=300:raise ValueError('Timeout must be between 1 and 300 seconds')
 try:lat,lon=map(float,geo.split(','))
 except (ValueError,AttributeError):raise ValueError('Provide --geo latitude,longitude for the public search center')
 if not all(map(math.isfinite,[lat,lon])) or not -90<=lat<=90 or not -180<=lon<=180:raise ValueError('Invalid public search center')
 out=P(out).absolute()
 if out.exists() or out.is_symlink():raise ValueError('Output directory already exists; choose a fresh destination')
 out.mkdir(parents=True);(out/'queries.txt').write_text(query.strip()+'\n');results=out/'results.jsonl'
 cmd=[str(binary),'-input',str(out/'queries.txt'),'-results',str(results),'-json','-fast-mode','-c','1','-depth','1','-lang','en','-exit-on-inactivity','20s','-geo',geo,'-radius','1000']
 timed_out=False
 with (out/'stdout.log').open('wb') as stdout,(out/'stderr.log').open('wb') as stderr:
  try:r=subprocess.run(cmd,cwd=out,env=runtime_env(),stdout=stdout,stderr=stderr,timeout=timeout);code=r.returncode
  except subprocess.TimeoutExpired:timed_out=True;code=124
 rows,invalid=read_rows(results);record={'observed_at':datetime.now(timezone.utc).isoformat(),'version':VERSION,'revision':REVISION,'binary_sha256':digest(binary),'query':query.strip(),'geo':geo,'radius_m':1000,'mode':'fast','concurrency':1,'depth':1,'telemetry_disabled':True,'returncode':code,'timed_out':timed_out,'rows':len(rows),'invalid_records':invalid,'results_sha256':digest(results) if results.exists() else None,'status':'completed' if code==0 and rows and not invalid else 'incomplete','scope':'Bounded public-place HTTP extraction. Not comprehensive coverage, review/email extraction or verified current business facts.'}
 (out/'run.json').write_text(json.dumps(record,indent=2)+'\n');return record

def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True);sub.add_parser('install');sub.add_parser('help');a=sub.add_parser('run');a.add_argument('--query',required=True);a.add_argument('--geo',required=True);a.add_argument('--outdir',required=True);a.add_argument('--timeout',type=int,default=90);args=p.parse_args()
 try:
  binary=install()
  if args.command=='install':print(json.dumps({'binary':str(binary),'version':VERSION,'sha256':digest(binary)}))
  elif args.command=='help':subprocess.run([str(binary),'-h'],env=runtime_env(),check=True)
  else:
   record=run_query(binary,args.query,args.outdir,args.timeout,args.geo);print(json.dumps(record,indent=2));return 0 if record['status']=='completed' else 2
 except (ValueError,OSError) as e:p.exit(2,str(e)+'\n')
if __name__=='__main__':raise SystemExit(main())
