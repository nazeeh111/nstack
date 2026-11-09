"""Editable, deterministic frame/audio cue fixture and independent decoded checks."""
import hashlib,json,math,pathlib,struct,wave,zlib
P=pathlib.Path

def make(root,cue):
 root=P(root);root.mkdir(parents=True,exist_ok=True);frames=root/'frames';frames.mkdir(exist_ok=True)
 config={'fps':30,'frames':60,'width':160,'height':96,'sample_rate':48000,'cue_frame':cue,'tone_hz':800,'tone_seconds':0.05}
 if not 0<=cue<config['frames']-3:raise ValueError('Cue outside fixture')
 for i in range(config['frames']):
  color=bytes((255,160,0)) if cue<=i<cue+3 else bytes((0,32,64))
  (frames/f'{i:03}.ppm').write_bytes(f"P6\n{config['width']} {config['height']}\n255\n".encode()+color*(config['width']*config['height']))
 fs=config['sample_rate'];length=config['frames']*fs//config['fps'];start=cue*fs//config['fps'];duration=int(fs*config['tone_seconds'])
 values=[int(16000*math.sin(2*math.pi*config['tone_hz']*(i-start)/fs)) if start<=i<start+duration else 0 for i in range(length)]
 with wave.open(str(root/'audio.wav'),'wb') as f:f.setparams((1,2,fs,len(values),'NONE','not compressed'));f.writeframes(struct.pack('<'+'h'*len(values),*values))
 (root/'source.json').write_text(json.dumps(config,indent=2)+'\n');return config

def verify(root,config,probe,rawvideo,audio):
 root=P(root);v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio')
 assert (v['width'],v['height'],v['r_frame_rate'])==(config['width'],config['height'],'30/1')
 assert int(a['sample_rate'])==config['sample_rate'] and a['channels']==1
 assert abs(float(probe['format']['duration'])-config['frames']/config['fps'])<1/config['fps']
 stride=config['width']*config['height']*3;assert len(rawvideo)==stride*config['frames']
 colors=[tuple(rawvideo[i*stride:i*stride+3]) for i in range(config['frames'])]
 first=next(i for i,c in enumerate(colors) if c==(255,160,0));assert first==config['cue_frame']
 assert all(c==((255,160,0) if config['cue_frame']<=i<config['cue_frame']+3 else (0,32,64)) for i,c in enumerate(colors))
 with wave.open(str(audio),'rb') as f:
  assert (f.getnchannels(),f.getsampwidth(),f.getframerate())==(1,2,config['sample_rate']);samples=struct.unpack('<'+'h'*f.getnframes(),f.readframes(f.getnframes()))
 start=next(i for i,x in enumerate(samples) if x);expected=config['cue_frame']*config['sample_rate']//config['fps'];assert abs(start-expected)<=1
 assert max(abs(x) for x in samples)<=16000
 # A current decoded-frame strip, not a source-only preview.
 chosen=[max(0,first-1),first,first+3];w=config['width']*3;h=config['height'];rows=[]
 for y in range(h):
  rows.append(b'\0'+b''.join(rawvideo[k*stride+y*config['width']*3:k*stride+(y+1)*config['width']*3] for k in chosen))
 def chunk(kind,data):return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
 png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(rows)))+chunk(b'IEND',b'')
 (root/'decoded-strip.png').write_bytes(png)
 return {'first_cue_frame':first,'audio_onset_seconds':start/config['sample_rate'],'frame_time_seconds':first/config['fps'],'sample_alignment_error':start-expected,'frames_checked':len(colors),'source_sha256':hashlib.sha256((root/'source.json').read_bytes()).hexdigest(),'output_sha256':hashlib.sha256((root/'output.mkv').read_bytes()).hexdigest(),'decoded_strip':str(root/'decoded-strip.png')}
