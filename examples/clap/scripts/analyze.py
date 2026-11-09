#!/usr/bin/env python3
"""Independent calculation and data-linked editable figure. See README.md."""
import argparse
import csv
import hashlib
import json
import os
import platform
import shutil
import sys
import wave
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR', str(Path(os.environ.get('TMPDIR','/tmp'))/'nstack-clap-matplotlib'))
import numpy as np
import scipy
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
MODULE_SHA = 'c066a78677371003818123efe3b8e1a7dbd75c8a21de6404ab94ea95c0e2c1f3'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def write_json(p, obj):
    Path(p).write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')

def read_audio(path):
    with wave.open(str(path)) as w:
        if (w.getnchannels(), w.getsampwidth(), w.getcomptype()) != (1, 2, 'NONE'):
            raise ValueError('Expected uncompressed mono PCM16 WAV; do not silently convert.')
        fs = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype='<i2').astype(np.float64) / 32768
    if len(x) < 10 or not np.any(x):
        raise ValueError('Empty, too short, or silent input.')
    return x, fs

def decay(x):
    energy = np.cumsum((x*x)[::-1])[::-1]
    db = np.full(len(x), np.nan)
    db[energy > 0] = 10*np.log10(energy[energy > 0]/energy[0])
    return energy, db

def fit(db, fs, depth):
    # Match the pinned estimator's exact strict threshold and exclusive endpoint.
    start = int(np.flatnonzero(db < -5)[0])
    stop = int(np.flatnonzero(db < db[start]-depth)[0])
    t = np.arange(start, stop)/fs
    y = db[start:stop]
    tc, yc = t-t.mean(), y-y.mean()
    slope = float(np.dot(tc, yc)/np.dot(tc, tc))
    intercept = float(y.mean()-slope*t.mean())
    residual = y-(slope*t+intercept)
    return dict(start_sample=start, stop_sample_exclusive=stop,
                start_seconds=start/fs, last_sample_seconds=(stop-1)/fs,
                stop_seconds_exclusive=stop/fs, sample_count=stop-start,
                start_db=float(y[0]), last_sample_db=float(y[-1]),
                depth_requested_db=depth, threshold_stop_db=float(db[start]-depth),
                slope_db_per_second=slope, intercept_db=intercept,
                rt60_seconds=-60/slope,
                residual_rms_db=float(np.sqrt(np.mean(residual**2))),
                r_squared=float(1-np.dot(residual,residual)/np.dot(yc,yc)))

def build(input_path, output, config, reference):
    input_path, output, config, reference = map(lambda p: Path(p).resolve(), (input_path, output, config, reference))
    if output.exists():
        raise ValueError('Use a fresh output directory; existing results are never overwritten.')
    params=json.loads(config.read_text())
    if params['fit_start_db'] != -5 or params['energy_fraction'] != 1 or params['fit_decay_db'] != 30:
        raise ValueError('This implementation supports the audited -5 dB / 30 dB fit, full energy only.')
    ref=json.loads(reference.read_text())
    if ref['input_sha256'] != sha(input_path) or ref['source_module_sha256'] != MODULE_SHA:
        raise ValueError('Stale input/reference or unexpected pinned source hash.')
    x,fs=read_audio(input_path)
    if ref['sample_rate_hz'] != fs:
        raise ValueError('Reference sample rate mismatch.')
    energy,db=decay(x)
    f=fit(db,fs,30)
    if abs(f['rt60_seconds']-ref['rt60_seconds']) > 1e-9:
        raise ValueError('Independent calculation disagrees with pinned nstack estimator.')
    sensitivity=[fit(db,fs,d) for d in (20,30,40)]
    time=np.arange(len(x))/fs
    finite=np.isfinite(db)
    output.mkdir(parents=True)
    (output/'source').mkdir()
    for p in (ROOT/'scripts').glob('*.py'):
        shutil.copy2(p,output/'source'/p.name)
    shutil.copy2(ROOT/'regenerate.sh',output/'source'/'regenerate.sh')
    shutil.copy2(config,output/'source'/'parameters.json')
    shutil.copy2(input_path,output/'input.wav')
    shutil.copy2(reference,output/'nstack-rt60.json')
    in_fit=(np.arange(len(x))>=f['start_sample']) & (np.arange(len(x))<f['stop_sample_exclusive'])
    with (output/'decay.csv').open('w',newline='') as stream:
        w=csv.writer(stream)
        w.writerow(['sample','time_seconds','amplitude_full_scale','backward_energy_full_scale_squared_samples','energy_db_re_total','used_in_fit','fitted_db'])
        for i in range(len(x)):
            w.writerow([i,format(time[i],'.17g'),format(x[i],'.17g'),format(energy[i],'.17g'),
                        format(db[i],'.17g') if finite[i] else '',int(in_fit[i]),
                        format(f['slope_db_per_second']*time[i]+f['intercept_db'],'.17g')])
    res={
        'input':str(input_path),'input_sha256':sha(input_path),'sample_rate_hz':fs,
        'samples':len(x),'duration_seconds':len(x)/fs,'channels':1,'encoding':'PCM16 little endian',
        'signal_units':params['signal_units'],'filtering':params['filtering'],
        'energy_definition':'E[n] = sum(x[k]^2 for k=n..N-1); dB[n] = 10 log10(E[n]/E[0])',
        'estimator':'OLS on Schroeder energy in dB; RT60 = -60 / slope',
        'fit':f,'interval_sensitivity':sensitivity,
        'uncertainty':'Single deterministic synthetic file (n=1). No physical-room or statistical confidence interval. Fit-window sensitivity is diagnostic only; integrated samples are correlated.',
        'sensitivity_range_seconds':[min(v['rt60_seconds'] for v in sensitivity),max(v['rt60_seconds'] for v in sensitivity)],
        'first_sample_below_minus60_seconds':float(time[np.flatnonzero(db < -60)[0]]),
        'last_nonzero_sample_seconds':float(time[np.flatnonzero(x)[-1]]),
        'zero_energy_samples':int(np.sum(~finite)),
        'peak_amplitude_full_scale':float(max(abs(x))),
        'clipped_pcm_samples':int(np.sum((x>=32767/32768)|(x<=-1))),
        'exclusions':'All samples retained in CSV. Fit excludes early energy above -5 dB and tail after a further 30 dB. No noise subtraction, calibration, filtering, onset trimming, or band averaging. Zero energy has undefined dB and is blank in CSV / absent from energy curve.',
        'reference_difference_seconds':f['rt60_seconds']-ref['rt60_seconds'],
        'source_revision':ref['source_revision'],'source_module_sha256':MODULE_SHA,
        'versions':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__},
    }
    write_json(output/'result.json',res)
    plt.rcParams.update({'svg.fonttype':'none','pdf.fonttype':42,'path.simplify':False,
                         'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
    fig,(ax0,ax)=plt.subplots(2,1,figsize=(10,7),sharex=True,
                            gridspec_kw={'height_ratios':[1,2.3]})
    fig.subplots_adjust(left=.12,right=.975,top=.84,bottom=.14,hspace=.10)
    fig.suptitle('Synthetic clap decay',fontsize=19,fontweight='bold',ha='left',x=.12,y=.97)
    ax0.set_title(f'RT60 = {f["rt60_seconds"]:.3f} s  |  {fs/1000:g} kHz mono  |  broadband energy fit',loc='left',fontsize=12,pad=10)
    ax0.plot(time,x,color='#555555',lw=.6,gid='waveform-series')
    ax0.set(ylabel='Amplitude\n(full scale)',ylim=(-1,1))
    ax0.text(.98,.85,f'{len(x)/fs:.3f} s synthetic record',transform=ax0.transAxes,ha='right',fontsize=10)
    ax.axvspan(f['start_seconds'],f['stop_seconds_exclusive'],color='#ededed',label='Fit interval (shaded)')
    edc,=ax.plot(time[finite],db[finite],color='#00689d',lw=1.6,label='Integrated energy (solid)',gid='energy-series')
    ft=time[in_fit]; fy=f['slope_db_per_second']*ft+f['intercept_db']
    ax.plot(ft,fy,color='#af4400',lw=2.0,ls='--',label='Linear fit (dashed)',gid='fit-series')
    end=(-60-f['intercept_db'])/f['slope_db_per_second']
    ext=np.array([ft[-1],end]); ey=f['slope_db_per_second']*ext+f['intercept_db']
    ax.plot(ext,ey,color='#af4400',lw=1.5,ls=':',label='Extrapolation to -60 dB (dotted)',gid='extrapolation-series')
    ax.axhline(-60,color='#777777',lw=.9,ls='--')
    ax.text(len(x)/fs*.985,-58.5,'-60 dB',ha='right',fontsize=10,color='#444444')
    ax.text(.98,.94,f'Fit: {f["start_seconds"]:.5f}–{f["stop_seconds_exclusive"]:.7f} s (end excluded)\n'
            f'Energy: about -5 to -35 dB\nSlope: {f["slope_db_per_second"]:.5f} dB/s\nRT60 = -60 / slope',
            transform=ax.transAxes,ha='right',va='top',fontsize=10,linespacing=1.5)
    ax.text(.98,.60,f'Zero-energy tail: dB undefined\nAll {len(x):,} samples retained in CSV',
            transform=ax.transAxes,ha='right',fontsize=10,color='#444444')
    floor=float(np.floor(np.nanmin(db)/10)*10)
    ax.set(xlabel='Time from file start (s)',ylabel='Backward-integrated energy\n10 log10(E / E₀), dB',xlim=(0,len(x)/fs),ylim=(floor,3))
    ax.set_xticks(np.linspace(0,len(x)/fs,9))
    ax.grid(axis='y',color='#e2e2e2',lw=.7)
    ax.set_axisbelow(True)
    ax.legend(loc='lower left',frameon=False,fontsize=9)
    fig.text(.12,.025,'One synthetic signal; fit-window sensitivity is not a confidence interval. No physical-room calibration.',fontsize=8.5,color='#444444')
    fig.canvas.draw()
    fig.set_layout_engine(None)
    plot_arrays={'energy-series':(time[finite],db[finite]),'fit-series':(ft,fy),'extrapolation-series':(ext,ey),'waveform-series':(time,x)}
    figure_inputs={'page_inches':[10,7],'svg_points_per_inch':72,'source_data':'decay.csv',
                   'series':{},'png_dpi':180,'xlim':list(ax.get_xlim()),'ylim':list(ax.get_ylim())}
    for name,(xx,yy) in plot_arrays.items():
        # SVG uses points and a top-left origin; capture expected rendered vertices.
        series_ax=ax0 if name=='waveform-series' else ax
        screen=series_ax.transData.transform(np.column_stack([xx,yy]))*72/fig.dpi
        screen[:,1]=7*72-screen[:,1]
        figure_inputs['series'][name]={'data':np.column_stack([xx,yy]).tolist(),'svg_points':screen.tolist(),
             'axis_bbox_points':(series_ax.bbox.bounds*np.array([72/fig.dpi]*4)).tolist(),
             'xlim':list(series_ax.get_xlim()),'ylim':list(series_ax.get_ylim())}
    write_json(output/'figure-inputs.json',figure_inputs)
    fig.savefig(output/'decay.svg',facecolor='white',metadata={'Date':None,'Description':'Synthetic clap backward-energy decay; editable text and vector paths. Source: decay.csv and result.json.'})
    fig.savefig(output/'decay.pdf',facecolor='white',metadata={'CreationDate':None,'ModDate':None,'Title':'Synthetic clap decay'})
    fig.savefig(output/'decay.png',facecolor='white',dpi=180)
    plt.close(fig)
    description=(f'Waveform above a backward-integrated energy decay plot. The fitted energy interval is '
                 f'{f["start_seconds"]:.5f} to {f["stop_seconds_exclusive"]:.5f} seconds, end excluded, approximately -5 to -35 dB. '
                 f'The fitted slope is {f["slope_db_per_second"]:.6f} dB/s, implying RT60 {f["rt60_seconds"]:.9f} seconds. '
                 'A solid blue energy curve, dashed brown fit, dotted brown extrapolation and shaded interval give redundant cues. '
                 'Zero-energy tail values have undefined dB. No physical room claim is made.\n')
    (output/'description.txt').write_text(description)
    dependencies={str(input_path):sha(input_path),str(config):sha(config)}
    for p in list((ROOT/'scripts').glob('*.py'))+[ROOT/'regenerate.sh',ROOT.parents[1]/'recipes/P318/requirements.lock',ROOT.parents[1]/'registry/manifest.json']:
        dependencies[str(p)]=sha(p)
    manifest={'input_sha256':sha(input_path),'dependencies':dependencies,
              'files':{str(p.relative_to(output)):sha(p) for p in sorted(output.rglob('*')) if p.is_file()},
              'link':'input.wav -> source/parameters.json + source/analyze.py -> decay.csv + result.json -> figure-inputs.json -> decay.svg/pdf/png',
              'limits':'Hashes establish file identity; numeric and SVG path audits are separate. No CI or physical calibration.'}
    write_json(output/'manifest.json',manifest)
    print(json.dumps({'output':str(output),'rt60_seconds':f['rt60_seconds'],'fit_seconds':[f['start_seconds'],f['stop_seconds_exclusive']], 'sensitivity':res['sensitivity_range_seconds']}))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--input',required=True);p.add_argument('--output',required=True)
    p.add_argument('--config',default=str(ROOT/'parameters.json'));p.add_argument('--reference',required=True)
    a=p.parse_args();build(a.input,a.output,a.config,a.reference)
