#!/usr/bin/env python3
"""Reopen artifacts, reject stale dependencies, audit CSV and actual SVG paths."""
import argparse
import csv
import hashlib
import json
import re
import wave
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from PIL import Image

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def verify(run, archived=False, current_input=None):
    run=Path(run).resolve()
    manifest=json.loads((run/'manifest.json').read_text())
    if current_input is not None and sha(current_input)!=manifest['input_sha256']:
        raise ValueError('Stale accepted input: regenerate the number and figure for the current input')
    for name,digest in manifest['files'].items():
        if sha(run/name)!=digest:
            raise ValueError('Artifact changed: '+name)
    if not archived:
        for name,digest in manifest['dependencies'].items():
            if sha(name)!=digest:
                raise ValueError('Stale dependency: '+name)
    result=json.loads((run/'result.json').read_text()); f=result['fit']
    with wave.open(str(run/'input.wav')) as w:
        fs=w.getframerate();x=np.frombuffer(w.readframes(w.getnframes()),'<i2').astype(float)/32768
    assert fs==result['sample_rate_hz']
    with (run/'decay.csv').open() as stream:
        rows=list(csv.DictReader(stream))
    assert len(rows)==len(x)
    t=np.array([float(r['time_seconds']) for r in rows]); amp=np.array([float(r['amplitude_full_scale']) for r in rows])
    e=np.array([float(r['backward_energy_full_scale_squared_samples']) for r in rows])
    db=np.array([float(r['energy_db_re_total']) if r['energy_db_re_total'] else np.nan for r in rows])
    used=np.array([int(r['used_in_fit']) for r in rows],bool)
    assert np.array_equal(amp,x) and np.allclose(t,np.arange(len(x))/fs,rtol=0,atol=1e-15)
    # Recompute energy with a scalar loop, then independently fit with polyfit.
    direct=np.empty(len(x)); total=0.
    for i in range(len(x)-1,-1,-1):
        total+=float(x[i])**2;direct[i]=total
    assert np.array_equal(direct,e)
    finite=direct>0
    assert np.array_equal(finite,np.isfinite(db))
    assert np.allclose(db[finite],10*np.log10(direct[finite]/direct[0]),rtol=0,atol=1e-11)
    indices=np.flatnonzero(used)
    assert np.array_equal(indices,np.arange(f['start_sample'],f['stop_sample_exclusive']))
    assert indices[0]==np.flatnonzero(db < -5)[0]
    assert f['stop_sample_exclusive']==np.flatnonzero(db < db[indices[0]]-30)[0]
    m,b=np.polyfit(t[used],db[used],1)
    assert abs(-60/m-f['rt60_seconds'])<1e-10
    assert abs(b-f['intercept_db'])<1e-9
    ref=json.loads((run/'nstack-rt60.json').read_text())
    assert ref['input_sha256']==sha(run/'input.wav')==manifest['input_sha256']
    assert abs(ref['rt60_seconds']-f['rt60_seconds'])<1e-9
    figure=json.loads((run/'figure-inputs.json').read_text())
    svg=ET.parse(run/'decay.svg').getroot();ns={'s':'http://www.w3.org/2000/svg'}
    audits={}
    for name,series in figure['series'].items():
        group=svg.find(f'.//s:g[@id="{name}"]',ns)
        path=group.find('s:path',ns)
        d=path.attrib['d']
        commands=re.findall('[A-Za-z]',d)
        assert set(commands) <= {'M','L'}, 'Unexpected SVG path encoding'
        points=np.array([float(v) for v in re.findall(r'[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?',d)]).reshape(-1,2)
        data=np.array(series['data']);expected=np.array(series['svg_points'])
        assert points.shape==expected.shape
        assert np.max(abs(points-expected))<1e-5
        # Verify the data-to-page transform, not just the saved expected points.
        left,bottom,width,height=series['axis_bbox_points']; xmin,xmax=series['xlim'];ymin,ymax=series['ylim']
        independent=np.column_stack([left+(data[:,0]-xmin)/(xmax-xmin)*width,
            504-(bottom+(data[:,1]-ymin)/(ymax-ymin)*height)])
        assert np.max(abs(points-independent))<1e-5
        if name=='energy-series':
            assert np.array_equal(data,np.column_stack([t[finite],db[finite]]))
        elif name=='waveform-series':
            assert np.array_equal(data,np.column_stack([t,amp]))
        else:
            assert np.max(abs(data[:,1]-(m*data[:,0]+b)))<1e-9
        assert np.all((data[:,0]>=xmin)&(data[:,0]<=xmax)&(data[:,1]>=ymin)&(data[:,1]<=ymax)), 'Clipped data'
        audits[name]={'vertices':len(points),'max_error_points':float(np.max(abs(points-independent)))}
    assert len(svg.findall('.//s:text',ns))>10, 'SVG text is not editable'
    assert not svg.findall('.//s:image',ns), 'Unexpected raster in editable SVG'
    with Image.open(run/'decay.png') as im:
        im.load();assert im.size==(1800,1260)
        assert im.mode in ('RGB','RGBA')
        if im.mode=='RGBA':assert im.getextrema()[3]==(255,255)
    assert (run/'decay.pdf').read_bytes().startswith(b'%PDF-')
    report={'status':'passed','current_dependencies_checked':not archived,
            'csv_rows':len(rows),'svg_path_audit':audits,'svg_editable_text':True,
            'no_series_clipping':True,'png_pixels':[1800,1260],
            'rt60_seconds':f['rt60_seconds'],
            'limits':'PDF header checked here; PDF reopening, font metadata, and visual inspection are recorded separately. Hash checks are not scientific validation.'}
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run');p.add_argument('--archived',action='store_true',help='verify frozen run only, without current external dependency checks')
    p.add_argument('--current-input',help='accepted current WAV; detects a handoff to a changed file')
    args=p.parse_args();print(json.dumps(verify(args.run,args.archived,args.current_input),indent=2))
