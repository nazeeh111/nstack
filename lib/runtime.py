"""Per-operation local runtimes. Only explicitly implemented adapters execute."""
import hashlib,importlib.util,json,pathlib,subprocess,os,sys,wave,struct,math
P=pathlib.Path

def admitted(n,id,r):
 c=n.component(id)
 if c['deployment']!='on demand':raise ValueError('Per-ID trial/substitute verifier is required before executing this operation')
 revision=r.get('reviewed_source_revision',r.get('revision'))
 if revision!=c['revision']:raise ValueError('Operation recipe differs from the current admitted source revision')
 if r.get('source_repository',c['repository'])!=c['repository']:raise ValueError('Operation recipe differs from the current admitted repository')

def recipe(n,id,op):
 n.component(id)
 if not all(x and x.replace('-','').isalnum() for x in [id,op]):raise ValueError('Invalid operation coordinates')
 f=n.ROOT/'recipes'/id/op/'recipe.json'
 if not f.exists():f=n.ROOT/'recipes'/id/'recipe.json'
 if not f.is_file():raise ValueError('No commissioned operation adapter; read per-ID prerequisites and acceptance before implementation')
 r=n.load(f)
 if r['id']!=id or r['operation']!=op:raise ValueError('Wrong operation recipe')
 return r,f.parent

def commission(n,id,op):
 c=n.component(id);r,folder=recipe(n,id,op)
 admitted(n,id,r)
 intent=n.STATE/'runtime-retirements'/f'{id}-{op}.json'
 if intent.is_file() and n.load(intent).get('phase')!='complete':remove(n,id,op)
 if c['deployment']!='on demand':raise ValueError('Per-ID trial/substitute verifier is required before commissioning')
 if (n.STATE/'locks'/f'{id}-{op}.json').is_file():
  # An ordinary worker can verify/reuse a completed commission without a
  # private write grant. New installations still require the owner lane.
  with n.read_lock(n.STATE/'runtime-writers'/f'{id}-{op}.lock'):
   if r['adapter']=='npm-bin':
    import npm_runtime
    return npm_runtime.locked(n,id,op,r,folder)
   if r['adapter']=='ffmpeg-source':
    import ffmpeg_runtime
    return ffmpeg_runtime.locked(n,id,op,r,folder)
   if r['adapter']=='python-module' and (id,op)==('P318','rt60'):return locked(n,id,op)
   if r['adapter']=='go-source':
    import go_runtime
    return go_runtime.locked(n,id,op,r,folder)
   if r['adapter']=='python-source':
    import python_source
    return python_source.locked(n,id,op,r,folder)
   if r['adapter']=='stdlib-helper':
    import local_helpers
    return local_helpers.locked(n,id,op,r,folder)
   raise ValueError('Adapter is not implemented')
 if r['adapter']=='npm-bin':
  import npm_runtime
  return npm_runtime.commission(n,id,op,r,folder)
 if r['adapter']=='ffmpeg-source':
  import ffmpeg_runtime
  return ffmpeg_runtime.commission(n,id,op,r,folder)
 if r['adapter']=='go-source':
  import go_runtime
  return go_runtime.commission(n,id,op,r,folder)
 if r['adapter']=='python-source':
  import python_source
  return python_source.commission(n,id,op,r,folder)
 if r['adapter']=='stdlib-helper':
  import local_helpers
  return local_helpers.commission(n,id,op,r,folder)
 if r['adapter']!='python-module' or (id,op)!=('P318','rt60'):raise ValueError('Adapter is not implemented')
 source=n.acquire(r['source_repository'],r['revision']);module=source/n.safe_relative(r['source_path']);env=n.STATE/'runtimes'/id/op;env.mkdir(parents=True,exist_ok=True)
 with n.lock(n.STATE/'runtime-writers'/f'{id}-{op}.lock'):
  lockfile=env/'requirements.lock';receiptfile=n.STATE/'locks'/f'{id}-{op}.json'
  if receiptfile.exists():
   receipt=n.load(receiptfile)
   if receipt['recipe_sha256']!=n.sha((folder/'recipe.json').read_bytes()):raise ValueError('Runtime recipe changed; commission a reviewed release delta')
   if n.sha(lockfile.read_bytes())!=receipt['requirements_sha256'] or n.sha(module.read_bytes())!=receipt['module_sha256']:raise ValueError('Runtime lock or source changed')
   return receipt
  uv=os.environ|{'UV_CACHE_DIR':str(n.STATE/'cache/uv')}
  published=folder/'requirements.lock'
  if not published.is_file():raise ValueError('Immutable dependency lock is required')
  if lockfile.exists() and lockfile.read_bytes()!=published.read_bytes():raise ValueError('Unrecorded existing dependency lock differs from recipe')
  if not lockfile.exists():
   import shutil
   shutil.copy2(published,lockfile)
  if not (env/'venv/bin/python').is_file():subprocess.run(['uv','venv','--python',r['python'],str(env/'venv')],check=True,env=uv)
  subprocess.run(['uv','pip','sync','--require-hashes','--python',str(env/'venv/bin/python'),str(lockfile)],check=True,env=uv)
  receipt={'id':id,'operation':op,'repository':r['source_repository'],'revision':r['revision'],'source_path':r['source_path'],'module':str(module),'module_sha256':n.sha(module.read_bytes()),'python':str(env/'venv/bin/python'),'requirements_sha256':n.sha(lockfile.read_bytes()),'recipe_sha256':n.sha((folder/'recipe.json').read_bytes()),'state':'ready, synthetic target check required'}
  n.dump(receiptfile,receipt);return receipt

def locked(n,id,op):
 r,folder=recipe(n,id,op);receipt=n.load(n.STATE/'locks'/f'{id}-{op}.json')
 source=n.STATE/'sources'/r['source_repository'].replace('/','--')/r['revision'];expected_module=source/n.safe_relative(r['source_path'])
 if P(receipt['module'])!=expected_module:raise ValueError('Runtime source path changed')
 n.check_source(source)
 if receipt['revision']!=r['revision'] or n.sha(P(receipt['module']).read_bytes())!=receipt['module_sha256'] or n.sha((folder/'recipe.json').read_bytes())!=receipt['recipe_sha256']:raise ValueError('Runtime source/recipe lock changed')
 lockfile=n.STATE/'runtimes'/id/op/'requirements.lock'
 if n.sha(lockfile.read_bytes())!=receipt['requirements_sha256']:raise ValueError('Runtime dependency lock changed')
 return receipt

def invoke(n,id,op,args):
 r,folder=recipe(n,id,op)
 admitted(n,id,r)
 if r['adapter']=='npm-bin':
  import npm_runtime
  return npm_runtime.invoke(n,id,op,r,folder,args)
 if r['adapter']=='ffmpeg-source':
  import ffmpeg_runtime
  return ffmpeg_runtime.invoke(n,id,op,r,folder,args)
 if r['adapter']=='go-source':
  import go_runtime
  return go_runtime.invoke(n,id,op,r,folder,args)
 if r['adapter']=='python-source':
  import python_source
  return python_source.invoke(n,id,op,r,folder,args)
 if r['adapter']=='stdlib-helper':
  import local_helpers
  return local_helpers.invoke(n,id,op,r,folder,args)
 with n.read_lock(n.STATE/'runtime-writers'/f'{id}-{op}.lock'):
  receipt=locked(n,id,op)
  subprocess.run([receipt['python'],str(n.ROOT/'lib/runtime.py'),'_rt60',receipt['module'],*args],check=True,env=os.environ|{'MPLBACKEND':'Agg','PYTHONDONTWRITEBYTECODE':'1'})

def measure(module,input,output):
 sys.dont_write_bytecode=True
 import numpy as np
 # Execute the verified source bytes, never an independently cached .pyc.
 import types
 m=types.ModuleType('nstack_p318_rt60');m.__file__=str(module)
 exec(compile(P(module).read_bytes(),str(module),'exec'),m.__dict__)
 with wave.open(input,'rb') as f:
  if f.getsampwidth()!=2 or f.getnchannels()!=1:raise ValueError('Require mono PCM16 WAV; convert explicitly and retain original')
  fs=f.getframerate();data=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(float)/32768
 if fs<=0 or len(data)<100 or not np.isfinite(data).all() or np.max(np.abs(data))==0:raise ValueError('Invalid or silent impulse response')
 value=float(m.measure_rt60(data,fs=fs,decay_db=30,plot=False))
 if not math.isfinite(value) or value<=0:raise ValueError('RT60 estimate invalid')
 result={'rt60_seconds':value,'sample_rate_hz':fs,'fit':'Schroeder backward energy, -5 to -35 dB, extrapolated to -60 dB','input_sha256':hashlib.sha256(P(input).read_bytes()).hexdigest(),'source_module_sha256':hashlib.sha256(P(module).read_bytes()).hexdigest(),'source_revision':'08d16968f8db414affaf84771a650358a7961446','limits':'Synthetic fixture or calibrated measurement only; noise, fitting interval and physical validity require task-specific checks.'}
 P(output).write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':
 if len(sys.argv)==5 and sys.argv[1]=='_rt60':measure(*sys.argv[2:])
 else:raise SystemExit('Use nstack run P318 rt60 -- INPUT_WAV OUTPUT_JSON')

def check(n,id,op):
 import tempfile
 r,folder=recipe(n,id,op)
 admitted(n,id,r)
 if r['adapter']=='npm-bin':
  import runtime_checks
  return runtime_checks.check(n,id,op,r,folder)
 if r['adapter']=='ffmpeg-source':
  import ffmpeg_runtime
  return ffmpeg_runtime.check(n,id,op,r,folder)
 if r['adapter']=='go-source':
  import go_runtime
  return go_runtime.check(n,id,op,r,folder)
 if r['adapter']=='python-source':
  import python_source
  return python_source.check(n,id,op,r,folder)
 if r['adapter']=='stdlib-helper':
  import local_helpers
  return local_helpers.check(n,id,op,r,folder)
 if (id,op)!=('P318','rt60'):raise ValueError('No target check implemented')
 receipt=locked(n,id,op);results=[]
 with tempfile.TemporaryDirectory(prefix='nstack-rt60-check-') as tmp:
  tmp=P(tmp)
  for target in (0.8,1.1):
   fs=16000;values=[int(24000*math.exp(-3*math.log(10)*i/fs/target)*math.sin(2*math.pi*1000*i/fs)) for i in range(2*fs)]
   wav=tmp/'clap.wav';result=tmp/'result.json'
   with wave.open(str(wav),'wb') as f:f.setparams((1,2,fs,len(values),'NONE','not compressed'));f.writeframes(struct.pack('<'+'h'*len(values),*values))
   invoke(n,id,op,[str(wav),str(result)]);actual=n.load(result)['rt60_seconds']
   if abs(actual-target)>0.004:raise ValueError('Synthetic analytic RT60 comparator failed')
   results.append({'known_seconds':target,'measured_seconds':actual,'absolute_error_seconds':abs(actual-target)})
  with wave.open(str(wav),'wb') as f:f.setparams((1,2,fs,1600,'NONE','not compressed'));f.writeframes(b'\0'*3200)
  rejected=subprocess.run([receipt['python'],str(n.ROOT/'lib/runtime.py'),'_rt60',receipt['module'],str(wav),str(result)],capture_output=True,env=os.environ|{'PYTHONDONTWRITEBYTECODE':'1'}).returncode!=0
  if not rejected:raise ValueError('Silence negative control was accepted')
 locked(n,id,op)
 result={'id':id,'operation':op,'checks':results,'silence_rejected':True,'source_revision':receipt['revision'],'source_sha256':receipt['module_sha256'],'requirements_sha256':receipt['requirements_sha256'],'source_cache_unchanged_after_execution':True}
 n.dump(n.STATE/'checks'/f'{id}-{op}.json',result);return result


def remove(n,id,op):
 """Retire only the exact owned runtime into private recovery storage."""
 import time
 r,folder=recipe(n,id,op)
 with n.lock(n.STATE/'runtime-writers'/f'{id}-{op}.lock'):
  receiptfile=n.STATE/'locks'/f'{id}-{op}.json';prefix=n.STATE/'runtimes'/id/op
  intentfile=n.STATE/'runtime-retirements'/f'{id}-{op}.json'
  def finish(intent):
   destination=P(intent['destination'])
   if intent.get('id')!=id or intent.get('operation')!=op or intent.get('original')!=str(prefix) or destination.parent!=n.STATE/'retired-runtimes' or not destination.name.startswith(f'{id}-{op}-') or destination.is_symlink():raise ValueError('Runtime retirement intent differs from owned coordinates')
   if receiptfile.exists() and n.sha(receiptfile.read_bytes())!=intent['receipt_sha256']:raise ValueError('Active receipt changed during retirement')
   if prefix.is_symlink() or prefix.resolve()!=prefix.absolute():raise ValueError('Linked runtime root')
   if prefix.exists():
    if destination.exists():raise ValueError('Both runtime retirement locations exist; preserve and reconcile')
    os.rename(prefix,destination)
   elif not destination.is_dir():raise ValueError('Neither runtime retirement location exists; preserve evidence')
   # The external intent is also the recovery metadata. Never write inside
   # retained bytes: even a same-named unexpected user note must survive.
   if receiptfile.exists():receiptfile.unlink()
   intent['phase']='complete';n.dump(intentfile,intent)
   return {'id':id,'operation':op,'state':'removed from active runtime registry','retained':str(destination)}
  if intentfile.exists():
   pending=n.load(intentfile)
   if pending.get('phase')!='complete':return finish(pending)
  if not receiptfile.exists():
   if prefix.exists():raise ValueError('Unrecorded runtime exists; inspect it before retirement')
   return {'id':id,'operation':op,'state':'absent'}
  if r['adapter']=='npm-bin':
   import npm_runtime
   receipt=npm_runtime.locked(n,id,op,r,folder)
  elif r['adapter']=='ffmpeg-source':
   import ffmpeg_runtime
   receipt=ffmpeg_runtime.locked(n,id,op,r,folder)
  elif r['adapter']=='go-source':
   import go_runtime
   receipt=go_runtime.locked(n,id,op,r,folder)
  elif r['adapter']=='python-source':
   import python_source
   receipt=python_source.locked(n,id,op,r,folder,retiring=True)
  elif r['adapter']=='stdlib-helper':
   import local_helpers
   receipt=local_helpers.locked(n,id,op,r,folder)
  else:receipt=locked(n,id,op)
  if prefix.is_symlink() or prefix.resolve()!=prefix.absolute():raise ValueError('Linked runtime root')
  destination=n.STATE/'retired-runtimes'/f'{id}-{op}-{time.time_ns()}'
  destination.parent.mkdir(parents=True,exist_ok=True)
  # Durable ownership intent precedes rename. A restart can finish from either
  # location, including after the active receipt was already removed.
  intent={'id':id,'operation':op,'original':str(prefix),'destination':str(destination),'receipt':receipt,'receipt_sha256':n.sha(receiptfile.read_bytes()),'phase':'prepared'};n.dump(intentfile,intent)
  return finish(intent)
