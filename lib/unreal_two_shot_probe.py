"""Run only inside a disposable owned Unreal project after target-version/API review.

NSTACK_UE_PROBE_PLAN/SPECS/RECEIPT are explicit local files. This queues, but does
not start, two owned jobs. Actual render callbacks/output are a separate gate.
"""
import json,os,pathlib,sys
P=pathlib.Path

def main():
 import unreal as u
 import ue_cine as c
 plan=json.loads(P(os.environ['NSTACK_UE_PROBE_PLAN']).read_text());specs=json.loads(P(os.environ['NSTACK_UE_PROBE_SPECS']).read_text())
 if len(plan['shots'])!=2 or len(specs)!=2:raise ValueError('Require exactly two disposable shots and render specs')
 root=plan['root']
 if not root.startswith('/Game/NstackProbe_') or '..' in root:raise ValueError('Probe assets must have a unique owned root')
 if u.EditorAssetLibrary.does_directory_exist(root):raise ValueError('Probe root already exists; preserve it and choose a fresh root')
 subsystem=u.get_editor_subsystem(u.MoviePipelineQueueSubsystem);queue=subsystem.get_queue()
 if list(queue.get_jobs()):raise ValueError('Existing render jobs must remain untouched; use a disposable empty queue')
 if subsystem.is_rendering():raise ValueError('Another render is active')
 report=c.build_from_plan(plan)
 if report.get('refused') or report.get('soft'):raise ValueError('Actual engine build refused or had unresolved API calls')
 master=u.load_asset(report['master']);audit=c.audit_sequence(master,plan)
 if audit['summary'].get('fail',0):raise ValueError('Sequence/camera audit failed in target engine')
 sections=[s for track in master.find_tracks_by_type(u.MovieSceneCinematicShotTrack) for s in track.get_sections()]
 if len(sections)!=2:raise ValueError('Actual master does not contain two shot sections')
 cameras=[]
 for section in sections:
  seq=section.get_sequence();names=[str(b.get_display_name()) for b in seq.get_bindings() if str(b.get_display_name()).startswith('CAM_')]
  if len(names)!=1:raise ValueError('Each shot needs exactly its selected camera binding')
  cameras.extend(names)
 expected={'CAM_'+shot['name'] for shot in plan['shots']}
 if set(cameras)!=expected:raise ValueError('Actual selected cameras differ from plan')
 for spec in specs:
  if not spec['sequence'].startswith(root) or not spec['job_name'].startswith('nstack-probe-'):raise ValueError('Render specs escaped owned probe identity')
 queued=c.queue_render_jobs(specs,clear=False,author='nstack-two-shot-probe')
 if len(queued)!=2 or any(missing for _,missing in queued):raise ValueError('Queue construction or variable readback failed')
 jobs=list(queue.get_jobs())
 if len(jobs)!=2:raise ValueError('Actual queue job count differs')
 names=[str(j.get_editor_property('job_name')) for j in jobs]
 if set(names)!={s['job_name'] for s in specs}:raise ValueError('Actual render queue identity differs')
 receipt={'assets':report['assets'],'master':report['master'],'cameras':cameras,'audit':audit,'queue_job_names':names,'render_status':c.render_status(),'limits':'Actual engine sequence/camera/queued-job probe only. Render callbacks, completed frames and decoded output remain separate target checks.'}
 P(os.environ['NSTACK_UE_PROBE_RECEIPT']).write_text(json.dumps(receipt,indent=2)+'\n')
if __name__=='__main__':main()
