"""Minimum local-only FFmpeg/ffprobe build from the reviewed Git source."""
import json,os,pathlib,platform,shutil,subprocess,sys,tempfile
P=pathlib.Path

def locked(n,id,op,r,folder):
 receipt=n.load(n.STATE/'locks'/f'{id}-{op}.json');prefix=n.STATE/'runtimes'/id/op
 if receipt['recipe_sha256']!=n.sha((folder/'recipe.json').read_bytes()) or receipt['revision']!=r['revision']:raise ValueError('FFmpeg recipe changed; commission a reviewed release delta')
 for name,digest in receipt['files'].items():
  file=prefix/n.safe_relative(name)
  if file.is_symlink() or not file.is_file() or n.sha(file.read_bytes())!=digest:raise ValueError('FFmpeg binary/configuration changed')
 return receipt

def commission(n,id,op,r,folder):
 if (id,op)!=('P230','media') or n.component(id)['deployment']!='on demand':raise ValueError('Unregistered FFmpeg operation')
 if platform.system()!='Darwin' or platform.machine()!='arm64':raise ValueError('This source-build recipe has only been commissioned for Darwin ARM64')
 if not shutil.which('clang') or not shutil.which('make'):raise ValueError('Install the free Apple compiler toolchain through its native setup first')
 source=n.acquire(r['source_repository'],r['revision']);prefix=n.STATE/'runtimes'/id/op;receiptfile=n.STATE/'locks'/f'{id}-{op}.json'
 with n.lock(n.STATE/'runtime-writers'/f'{id}-{op}.lock'):
  if receiptfile.exists():return locked(n,id,op,r,folder)
  owner=prefix/'build-owner.json';identity={'id':id,'operation':op,'revision':r['revision'],'recipe_sha256':n.sha((folder/'recipe.json').read_bytes())}
  if prefix.exists() and (not owner.is_file() or n.load(owner)!=identity):raise ValueError('Unowned or changed FFmpeg build directory')
  prefix.mkdir(parents=True,exist_ok=True);n.dump(owner,identity);bin=prefix/'bin';bin.mkdir(exist_ok=True)
  environment=os.environ|{'LC_ALL':'C','SOURCE_DATE_EPOCH':'0'}
  # FFmpeg refuses whitespace in its build/source path. Use a private temporary
  # copy, verify its bytes, then retain binaries and log in durable state.
  with tempfile.TemporaryDirectory(prefix='nstack-ffmpeg-',dir='/private/tmp' if sys.platform=='darwin' else None) as tmp:
   tmp=P(tmp);tmp.chmod(0o700);copied=tmp/'source';shutil.copytree(source,copied);n.check_source(copied);build=tmp/'build';build.mkdir()
   argv=[str(copied/'configure'),*r['configuration'],'--extra-version=nstack-'+r['revision'][:12]]
   with (prefix/'build.log').open('a') as log:
    subprocess.run(argv,cwd=build,env=environment,stdout=log,stderr=subprocess.STDOUT,check=True)
    subprocess.run(['make','-j4','ffmpeg','ffprobe'],cwd=build,env=environment,stdout=log,stderr=subprocess.STDOUT,check=True)
   for name in ('ffmpeg','ffprobe'):shutil.copy2(build/name,bin/name)
  versions={name:subprocess.check_output([str(bin/name),'-version'],text=True).splitlines()[0] for name in ('ffmpeg','ffprobe')}
  configuration=subprocess.check_output([str(bin/'ffmpeg'),'-buildconf'],stderr=subprocess.STDOUT,text=True)
  (prefix/'buildconf.txt').write_text(configuration);n.check_source(source)
  receipt={**identity,'adapter':'ffmpeg-source','versions':versions,'configure_argv':argv,'compiler':subprocess.check_output(['clang','--version'],text=True).splitlines()[0],'files':{str(f.relative_to(prefix)):n.sha(f.read_bytes()) for f in [bin/'ffmpeg',bin/'ffprobe',prefix/'buildconf.txt']},'license':'LGPL configuration from the recorded exact source; no GPL/nonfree flags','state':'commissioned; actual output check required'}
  n.dump(receiptfile,receipt);return receipt

def invoke(n,id,op,r,folder,args):
 if not args or args[0] not in ('ffmpeg','ffprobe'):raise ValueError('Select ffmpeg or ffprobe explicitly')
 with n.read_lock(n.STATE/'runtime-writers'/f'{id}-{op}.lock'):
  locked(n,id,op,r,folder);subprocess.run([str(n.STATE/'runtimes'/id/op/'bin'/args[0]),*args[1:]],check=True)

def check(n,id,op,r,folder):
 import media_fixture
 root=n.STATE/'checks/artifacts/P230';root.mkdir(parents=True,exist_ok=True);bin=n.STATE/'runtimes'/id/op/'bin';checks=[]
 with n.read_lock(n.STATE/'runtime-writers'/f'{id}-{op}.lock'):
  receipt=locked(n,id,op,r,folder)
  for cue in (15,21):
   out=root/('cue-'+str(cue));config=media_fixture.make(out,cue)
   log=out/'render.log'
   with log.open('w') as stream:subprocess.run([str(bin/'ffmpeg'),'-y','-framerate','30','-i',str(out/'frames/%03d.ppm'),'-i',str(out/'audio.wav'),'-c:v','ffv1','-c:a','pcm_s16le','-shortest',str(out/'output.mkv')],stdout=stream,stderr=stream,check=True)
   subprocess.run([str(bin/'ffmpeg'),'-v','error','-i',str(out/'output.mkv'),'-c:v','rawvideo','-c:a','pcm_s16le','-f','null','-'],check=True)
   probe=json.loads(subprocess.check_output([str(bin/'ffprobe'),'-v','error','-show_streams','-show_format','-of','json',str(out/'output.mkv')]))
   decoded=out/'decoded-video.rgb';subprocess.run([str(bin/'ffmpeg'),'-v','error','-y','-i',str(out/'output.mkv'),'-map','0:v','-f','rawvideo','-pix_fmt','rgb24',str(decoded)],check=True);raw=decoded.read_bytes()
   subprocess.run([str(bin/'ffmpeg'),'-v','error','-y','-i',str(out/'output.mkv'),'-map','0:a','-c:a','pcm_s16le',str(out/'decoded-audio.wav')],check=True)
   checks.append(media_fixture.verify(out,config,probe,raw,out/'decoded-audio.wav'))
  assert checks[0]['source_sha256']!=checks[1]['source_sha256'] and checks[0]['output_sha256']!=checks[1]['output_sha256'] and checks[1]['audio_onset_seconds']-checks[0]['audio_onset_seconds']>0.19
  shutil.copy2(n.ROOT/'lib/media_fixture.py',root/'editable-fixture.py')
 result={'id':id,'operation':op,'source_revision':r['revision'],'versions':receipt['versions'],'full_decode':True,'independent_pixel_sample_checks':checks,'changed_source_rerender':True,'editable_source':str(root/'editable-fixture.py'),'limits':'Synthetic local cue fixture; no speech/model, subtitles, camera input or NLE claim.'};n.dump(n.STATE/'checks/P230-media.json',result);return result
