#!/usr/bin/env python3
"""Independent stdlib numeric comparator for the known synthetic fixture."""
import argparse,hashlib,json,math,pathlib,struct,wave
p=argparse.ArgumentParser(description=__doc__);p.add_argument('input');p.add_argument('result');p.add_argument('--expected',type=float,required=True);a=p.parse_args()
with wave.open(a.input,'rb') as wav:
 if (wav.getnchannels(),wav.getsampwidth(),wav.getcomptype())!=(1,2,'NONE'):raise ValueError('Expected mono PCM16 fixture')
 fs=wav.getframerate();raw=wav.readframes(wav.getnframes())
values=[x[0]/32768 for x in struct.iter_unpack('<h',raw)];energy=[0.]*len(values);total=0.
for i in range(len(values)-1,-1,-1):total+=values[i]**2;energy[i]=total
if total<=0:raise ValueError('Silent signal')
db=[10*math.log10(x/total) if x>0 else float('-inf') for x in energy];start=next(i for i,x in enumerate(db) if x<-5);stop=next(i for i in range(start,len(db)) if db[i]<db[start]-30)
times=[i/fs for i in range(start,stop)];ys=db[start:stop];tx=math.fsum(times)/len(times);yy=math.fsum(ys)/len(ys)
slope=math.fsum((x-tx)*(y-yy) for x,y in zip(times,ys))/math.fsum((x-tx)**2 for x in times);rt60=-60/slope
result=json.loads(pathlib.Path(a.result).read_text());observed=result['fit']['rt60_seconds']
assert result['input_sha256']==hashlib.sha256(pathlib.Path(a.input).read_bytes()).hexdigest()
assert math.isfinite(rt60) and abs(rt60-a.expected)<=.004 and abs(rt60-observed)<1e-9
print(json.dumps({'stdlib_comparator_passed':True,'expected_seconds':a.expected,'measured_seconds':rt60,'absolute_error_seconds':abs(rt60-a.expected),'tolerance_seconds':.004,'limits':'Known synthetic tone only; not physical-room or statistical uncertainty validation.'},indent=2))
