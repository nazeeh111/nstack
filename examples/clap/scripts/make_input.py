#!/usr/bin/env python3
"""Create an original synthetic PCM16 decay; no recording or external asset."""
import argparse,json,math,pathlib,struct,wave
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--decay',type=float,required=True);p.add_argument('--output',required=True);a=p.parse_args()
if not .25<=a.decay<=1.5:p.error('Use a decay between 0.25 and 1.5 seconds for this bounded fixture')
path=pathlib.Path(a.output)
if path.exists():p.error('Existing input retained; select a new filename')
path.parent.mkdir(parents=True,exist_ok=True);fs=16000
values=[int(24000*math.exp(-3*math.log(10)*i/fs/a.decay)*math.sin(2*math.pi*1000*i/fs)) for i in range(fs*2)]
with path.open('xb') as stream,wave.open(stream,'wb') as output:
 output.setparams((1,2,fs,len(values),'NONE','not compressed'));output.writeframes(struct.pack('<'+'h'*len(values),*values))
print(json.dumps({'synthetic':True,'analytic_rt60_seconds':a.decay,'sample_rate_hz':fs,'seconds':2,'encoding':'mono PCM16','limits':'Decaying 1 kHz tone, not a physical room measurement.'}))
