"""Exact-source Go commands with an isolated compiler and readonly module lock."""
import json,os,pathlib,platform,subprocess,sys
P=pathlib.Path
def environment(n,prefix,toolchain):
 home=prefix/'build-home';home.mkdir(exist_ok=True)
 return {'PATH':str(toolchain/'bin')+os.pathsep+os.environ.get('PATH','/usr/bin:/bin'),'HOME':str(home),'TMPDIR':os.environ.get('TMPDIR','/private/tmp'),'LANG':'C.UTF-8','LC_ALL':'C','GOROOT':str(toolchain),'GOENV':'off','GOTOOLCHAIN':'local','GOTELEMETRY':'off','GOWORK':'off','GOFLAGS':'','CGO_ENABLED':'0','GOOS':'darwin','GOARCH':'arm64','GOCACHE':str(n.STATE/'cache/go-build'),'GOMODCACHE':str(n.STATE/'cache/go-modules'),'GOPATH':str(n.STATE/'cache/go-path'),'GOPROXY':'https://proxy.golang.org','GOSUMDB':'sum.golang.org','GOPRIVATE':'','GONOPROXY':'','GONOSUMDB':''}
def locked(n,id,op,r,folder):
 saved=n.load(n.STATE/'locks'/f'{id}-{op}.json');prefix=n.STATE/'runtimes'/id/op
 if saved['recipe_sha256']!=n.sha((folder/'recipe.json').read_bytes()) or saved['revision']!=r['revision']:raise ValueError('Go runtime recipe/source changed; commission a reviewed release delta')
 if saved['prefix']!=str(prefix):raise ValueError('Runtime escaped its registered prefix')
 for name,digest in saved['files'].items():
  file=prefix/n.safe_relative(name)
  if file.is_symlink() or not file.is_file() or n.sha(file.read_bytes())!=digest:raise ValueError('Go runtime binary/build metadata changed')
 return saved
def commission(n,id,op,r,folder):
 if (id,op) not in [('P190','cli'),('P082','cli'),('P188','cli'),('L023','cli'),('X-OASDIFF','cli')] or n.component(id)['deployment']!='on demand':raise ValueError('No admitted Go command recipe')
 if platform.system()!='Darwin' or platform.machine()!='arm64':raise ValueError('This Go source recipe has only been commissioned for native Darwin ARM64')
 source=n.acquire(r['source_repository'],r['revision'])/n.safe_relative(r['source_subdirectory']);prefix=n.STATE/'runtimes'/id/op;receipt=n.STATE/'locks'/f'{id}-{op}.json'
 with n.lock(n.STATE/'runtime-writers'/f'{id}-{op}.lock'):
  if receipt.exists():return locked(n,id,op,r,folder)
  identity={'id':id,'operation':op,'revision':r['revision'],'recipe_sha256':n.sha((folder/'recipe.json').read_bytes())};owner=prefix/'build-owner.json'
  if prefix.exists() and (not owner.is_file() or n.load(owner)!=identity):raise ValueError('Unowned or changed source build prefix')
  prefix.mkdir(parents=True,exist_ok=True);n.dump(owner,identity)
  import native_archive
  toolchain,compiler=native_archive.acquire(n,r['toolchain']);runenv=environment(n,prefix,toolchain);bin=prefix/'bin';bin.mkdir(exist_ok=True);binary=bin/r['binary']
  if r.get('go_mod_sha256') and n.sha((source/'go.mod').read_bytes())!=r['go_mod_sha256']:raise ValueError('Go build metadata differs from the inspected recipe')
  args=[str(toolchain/'bin/go'),'build','-mod=readonly','-trimpath','-buildvcs=false']
  linker=r.get('linker_arguments',[])
  if r.get('version_variable'):linker+=['-X='+r['version_variable']+'='+r['build_version']]
  if linker:args+=['-ldflags',' '.join(linker)]
  args+=['-o',str(binary),r['package']]
  with (prefix/'build.log').open('a') as log:subprocess.run(args,cwd=source,env=runenv,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1200)
  observed=subprocess.check_output([str(binary),*r['version_arguments']],text=True,env=runenv).strip()
  if r.get('build_version') and observed!=r['build_version']:raise ValueError('Source build identity did not match')
  metadata=subprocess.check_output([str(toolchain/'bin/go'),'version','-m',str(binary)],text=True,env=runenv);(prefix/'go-build-info.txt').write_text(metadata);n.check_source(source)
  saved={**identity,'adapter':'go-source','prefix':str(prefix),'version':observed,'compiler_version':compiler['version'],'compiler_spec_sha256':compiler['spec_sha256'],'go_mod_sha256':n.sha((source/'go.mod').read_bytes()),'go_sum_sha256':n.sha((source/'go.sum').read_bytes()),'files':{str(p.relative_to(prefix)):n.sha(p.read_bytes()) for p in [binary,prefix/'go-build-info.txt']},'state':'exact source built; acceptance check required'};n.dump(receipt,saved);return saved
def invoke(n,id,op,r,folder,args):
 with n.read_lock(n.STATE/'runtime-writers'/f'{id}-{op}.lock'):
  saved=locked(n,id,op,r,folder)
  import scanner
  if id=='P190':
   if args in (['version'],['--help']):subprocess.run([str(P(saved['prefix'])/'bin'/r['binary']),*args],check=True,env=scanner.environment(P(saved['prefix'])))
   else:scanner.invoke(n,r,saved,args)
  else:
   if not args:raise ValueError('Pass explicit command arguments; no service or scan is started implicitly')
   subprocess.run([str(P(saved['prefix'])/'bin'/r['binary']),*args],check=True,env=os.environ|{'GOTOOLCHAIN':'local','GOTELEMETRY':'off'})
def check(n,id,op,r,folder):
 import scanner
 with n.read_lock(n.STATE/'runtime-writers'/f'{id}-{op}.lock'):
  saved=locked(n,id,op,r,folder)
  if id=='P190':return scanner.check(n,r,saved)
  output=subprocess.check_output([str(P(saved['prefix'])/'bin'/r['binary']),*r['version_arguments']],text=True,env=scanner.environment(P(saved['prefix'])),timeout=30)
  if not output.strip():raise ValueError('Native command health returned no output')
  result={'id':id,'operation':op,'source_revision':r['revision'],'binary_sha256':saved['files']['bin/'+r['binary']],'native_command_health':True,'claim':'Exact source build and local command health only; account, database, advisory freshness and task-output acceptance remain separate.','acceptance_checks':n.component(id)['acceptance_checks']};n.dump(n.STATE/'checks'/f'{id}-{op}.json',result);return result
