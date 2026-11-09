"""Lazy exact-source Python wheel builds, isolated build/runtime hash locks."""
import email.parser,hashlib,json,os,pathlib,platform,re,shutil,subprocess,sys,time,zipfile
P=pathlib.Path

def environment(n,prefix):
 home=prefix/'build-home';home.mkdir(exist_ok=True)
 return {'PATH':os.environ.get('PATH','/usr/bin:/bin'),'HOME':str(home),'TMPDIR':os.environ.get('TMPDIR','/private/tmp'),'LANG':'en_US.UTF-8','LC_ALL':'en_US.UTF-8','UV_CACHE_DIR':str(n.STATE/'cache/uv'),'UV_NO_CONFIG':'1','UV_KEYRING_PROVIDER':'disabled','UV_PYTHON_INSTALL_DIR':str(n.STATE/'toolchains/python'),'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1','HF_HUB_OFFLINE':'1','HF_HUB_DISABLE_TELEMETRY':'1','DO_NOT_TRACK':'1','GIT_CONFIG_GLOBAL':'/dev/null','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_COUNT':'2','GIT_CONFIG_KEY_0':'core.hooksPath','GIT_CONFIG_VALUE_0':'/dev/null','GIT_CONFIG_KEY_1':'credential.helper','GIT_CONFIG_VALUE_1':'','GIT_TERMINAL_PROMPT':'0'}

def normalized(value):return re.sub('[-_.]+','-',value).lower()

def checkout(n,r,prefix,env):
 """Keep the build's mutable Git checkout separate from immutable source cache."""
 source=prefix/'build-source'
 if not source.exists():
  source.mkdir();subprocess.run(['git','init','-q',str(source)],check=True,env=env)
  subprocess.run(['git','-C',str(source),'fetch','-q','--depth=1','https://github.com/'+r['source_repository']+'.git',r['revision']],check=True,env=env,timeout=600)
  subprocess.run(['git','-C',str(source),'checkout','-q','--detach','FETCH_HEAD'],check=True,env=env)
 actual=subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True,env=env).strip()
 if actual!=r['revision']:raise ValueError('Python build source commit differs')
 # Submodules need a separately reviewed recursive lock, never automatic fetch.
 if (source/'.gitmodules').exists() and not r.get('submodules_not_required'):raise ValueError('Selected source requires a reviewed submodule build lock')
 dirty=subprocess.check_output(['git','-C',str(source),'status','--porcelain','--untracked-files=no'],env=env)
 if dirty:raise ValueError('Tracked Python build source was changed; preserve and review before retry')
 return source

def wheel_identity(wheel,distribution):
 with zipfile.ZipFile(wheel) as archive:
  names=archive.namelist();metadata=[p for p in names if p.endswith('.dist-info/METADATA')]
  if len(metadata)!=1:raise ValueError('Wheel must identify one distribution')
  for name in names:
   if P(name).is_absolute() or '..' in P(name).parts:raise ValueError('Unsafe wheel path')
  message=email.parser.BytesParser().parsebytes(archive.read(metadata[0]))
  if normalized(message['Name'])!=normalized(distribution):raise ValueError('Wheel distribution differs from the registered package')
  return {'name':message['Name'],'version':message['Version']}

def files(n,prefix):
 prefix=prefix.resolve(strict=True)
 result={}
 for folder in ('venv','wheels'):
  for file in (prefix/folder).rglob('*'):
   relative=str(file.relative_to(prefix))
   if file.is_symlink():
    # Only uv's explicit interpreter aliases may point outside the owned env.
    # Record directory links too; rglob does not descend them.
    resolved=file.resolve(strict=True);hashed=any(resolved.is_relative_to(prefix/root) for root in ('venv','wheels'))
    interpreter=(file.parent==prefix/'venv/bin' and file.name in ('python','python3','python3.12') and resolved==(prefix/'venv/bin/python').resolve(strict=True))
    if not hashed and not interpreter:raise ValueError('Unexpected external runtime symlink or target outside hashed trees')
    result[relative]={'symlink':str(file.readlink()),'resolved':str(resolved)}
   elif file.is_file():result[relative]={'sha256':n.sha(file.read_bytes())}
 for name in ('requirements.lock','build-requirements.lock'):
  result[name]={'sha256':n.sha((prefix/name).read_bytes())}
 return result

def locked(n,id,op,r,folder,retiring=False):
 if not retiring:
  import runtime
  runtime.admitted(n,id,r)
 saved=n.load(n.STATE/'locks'/f'{id}-{op}.json');prefix=n.STATE/'runtimes'/id/op
 if saved['prefix']!=str(prefix) or saved['recipe_sha256']!=n.sha((folder/'recipe.json').read_bytes()) or saved['revision']!=r['revision']:raise ValueError('Python runtime source/recipe changed; commission a reviewed delta')
 if (saved.get('id'),saved.get('operation'),saved.get('adapter'),saved.get('python'))!=(id,op,'python-source',str(prefix/'venv/bin/python')):raise ValueError('Python runtime receipt execution coordinates differ')
 if files(n,prefix)!=saved['files']:raise ValueError('Python runtime environment or lock changed')
 interpreter=prefix/'venv/bin/python'
 if interpreter.resolve()!=P(saved['interpreter_resolved']) or n.sha(interpreter.read_bytes())!=saved['interpreter_sha256']:raise ValueError('Python interpreter changed')
 return saved

def commission(n,id,op,r,folder):
 if n.component(id)['deployment']!='on demand':raise ValueError('This Python route is dormant behind its per-ID gate')
 if r['revision']!=n.component(id)['revision'] or r['source_repository']!=n.component(id)['repository']:raise ValueError('Python recipe source differs from release registry')
 if r.get('supported_platforms') and platform.system() not in r['supported_platforms']:raise ValueError('This source recipe requires the named supported platform: '+', '.join(r['supported_platforms']))
 uv=shutil.which('uv')
 if not uv:raise ValueError('The existing uv prerequisite is missing; use the reviewed P373 route')
 for command in r.get('required_commands',[]):
  if not shutil.which(command):raise ValueError('Missing native build prerequisite: '+command+'; no compiler or global runtime was installed')
 prefix=n.STATE/'runtimes'/id/op;receipt=n.STATE/'locks'/f'{id}-{op}.json'
 with n.lock(n.STATE/'runtime-writers'/f'{id}-{op}.lock'):
  if receipt.exists():return locked(n,id,op,r,folder)
  owner={'id':id,'operation':op,'revision':r['revision'],'recipe_sha256':n.sha((folder/'recipe.json').read_bytes())}
  if prefix.exists() and (not (prefix/'build-owner.json').is_file() or n.load(prefix/'build-owner.json')!=owner):raise ValueError('Unowned or changed Python runtime prefix')
  if prefix.exists():
   # A failed build may leave arbitrary generated or untracked inputs. Preserve
   # the complete owned attempt, then retry from a fresh checkout and venv.
   retired=n.STATE/'retired-runtimes'/f'{id}-{op}-incomplete-{time.time_ns()}';retired.parent.mkdir(parents=True,exist_ok=True);os.rename(prefix,retired)
  prefix.mkdir(parents=True,exist_ok=True);n.dump(prefix/'build-owner.json',owner);env=environment(n,prefix)
  with (prefix/'build.log').open('a') as log:
   def run(args):subprocess.run(args,env=env,cwd=prefix,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=1800)
   source=checkout(n,r,prefix,env);project=source/n.safe_relative(r.get('source_subdirectory','.'))
   if not project.resolve().is_relative_to(source.resolve()):raise ValueError('Linked package root')
   sys.path.insert(0,str(n.ROOT/'vendor'));import tomlkit
   inspected=r['inspected_build_metadata'];metadata=source/n.safe_relative(inspected['path'])
   if not metadata.is_file() or n.sha(metadata.read_bytes())!=inspected['sha256']:raise ValueError('Pinned build metadata differs from the inspected recipe')
   for extra in r.get('additional_build_metadata',[]):
    file=source/n.safe_relative(extra['path'])
    if not file.is_file() or n.sha(file.read_bytes())!=extra['sha256']:raise ValueError('Additional pinned packaging metadata differs')
   config=tomlkit.parse((project/'pyproject.toml').read_text()) if (project/'pyproject.toml').is_file() else {}
   backend=config.get('build-system',{}).get('build-backend')
   requires=list(config.get('build-system',{}).get('requires',[]))
   if not backend and inspected['backend']=='setuptools.build_meta:__legacy__':
    if not (project/'setup.py').is_file():raise ValueError('Legacy setuptools route requires its inspected setup.py')
    backend='setuptools.build_meta:__legacy__';requires=list(r['legacy_build_requirements'])
   if backend!=inspected['backend']:raise ValueError('Python build backend differs')
   if not requires:raise ValueError('Pinned source has no explicit PEP517 build-system requirements; implement its actual build recipe')
   build_in=prefix/'build-requirements.in';build_in.write_text('\n'.join(requires)+'\n');build_lock=prefix/'build-requirements.lock';build_python=prefix/'build-venv/bin/python'
   run([uv,'venv','--python',r['python'],str(prefix/'build-venv')])
   run([uv,'pip','compile',str(build_in),'--python',str(build_python),'--generate-hashes','--no-build','--output-file',str(build_lock)])
   run([uv,'pip','sync','--require-hashes','--python',str(build_python),str(build_lock)])
   wheels=prefix/'wheels';wheels.mkdir(exist_ok=True)
   run([uv,'build','--wheel','--no-build-isolation','--python',str(build_python),'--out-dir',str(wheels),str(project)])
   built=list(wheels.glob('*.whl'))
   if len(built)!=1:raise ValueError('Build must produce exactly one wheel; preserve unexpected files for review')
   identity=wheel_identity(built[0],r['distribution']);requirements=prefix/'requirements.in';requirements.write_text(built[0].as_uri()+'\n')
   python=prefix/'venv/bin/python';run([uv,'venv','--python',r['python'],str(prefix/'venv')])
   run([uv,'pip','compile',str(requirements),'--python',str(python),'--generate-hashes','--no-build','--output-file',str(prefix/'requirements.lock')])
   run([uv,'pip','sync','--require-hashes','--python',str(python),str(prefix/'requirements.lock')])
   checkout(n,r,prefix,env)
  saved={**owner,'adapter':'python-source','prefix':str(prefix),'distribution':identity,'python':str(python),'interpreter_resolved':str(python.resolve()),'interpreter_sha256':n.sha(python.read_bytes()),'uv_version':subprocess.check_output([uv,'--version'],text=True).strip(),'files':files(n,prefix),'state':'source-built and locked; import health and task-specific output checks required'}
  n.dump(receipt,saved);return saved

def invoke(n,id,op,r,folder,args):
 if not args:raise ValueError('Pass an explicit project Python script and its arguments')
 # Environment selection is not an OS sandbox. The native worker's existing
 # permissions remain controlling, including filesystem and outbound actions.
 script=P(args[0]).resolve(strict=True);project=n.project_paths(P.cwd())
 if not script.is_file() or not script.is_relative_to(project):raise ValueError('Use an explicit script inside the current bounded project')
 with n.read_lock(n.STATE/'runtime-writers'/f'{id}-{op}.lock'):
  saved=locked(n,id,op,r,folder);subprocess.run([saved['python'],str(script),*args[1:]],check=True,env=os.environ|{'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1'})

def check(n,id,op,r,folder):
 with n.read_lock(n.STATE/'runtime-writers'/f'{id}-{op}.lock'):
  saved=locked(n,id,op,r,folder)
  code='import importlib,importlib.metadata,json,pathlib; m=importlib.import_module('+repr(r['import_name'])+'); roots=[pathlib.Path(m.__file__).resolve()] if getattr(m,"__file__",None) else [pathlib.Path(p).resolve() for p in getattr(m,"__path__",[])]; assert roots and all(p.is_relative_to(pathlib.Path('+repr(saved['prefix'])+')/"venv") for p in roots), "Import origin escaped the locked environment"; print(json.dumps({"distribution":'+repr(r['distribution'])+',"version":importlib.metadata.version('+repr(r['distribution'])+')}))'
  env=environment(n,P(saved['prefix']));result=json.loads(subprocess.check_output([saved['python'],'-I','-B','-c',code],cwd=saved['prefix'],env=env,text=True,timeout=120))
  if result['version']!=saved['distribution']['version']:raise ValueError('Imported distribution version differs from built wheel')
  locked(n,id,op,r,folder)
  result.update({'id':id,'operation':op,'source_revision':r['revision'],'claim':'Actual import health only; model, device, service and task-output acceptance remain separate.','task_acceptance':n.component(id)['acceptance_checks']});n.dump(n.STATE/'checks'/f'{id}-{op}.json',result);return result
