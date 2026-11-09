"""Read-only in-editor capability probe, run by retained ue_run job protocol.

No engine pass is inferred from import or offline execution. An actual Unreal
Editor project and verified target version are prerequisites.
"""
import pathlib,sys

def main(args=None):
    here=pathlib.Path(__file__).resolve().parent
    for root in (here,here.parent.parent/'scenario-unreal-expert/scripts'):
        if str(root) not in sys.path:sys.path.insert(0,str(root))
    import unreal
    import ue_anim
    report=ue_anim.probe()
    version=str(unreal.SystemLibrary.get_engine_version())
    if report.get('engine') != version:
        raise RuntimeError('Animation probe engine identity mismatch')
    return {'actual_editor':True,'engine':version,'probe':report,
            'acceptance':'API presence only; retarget, deformation, root motion, Control Rig and MRQ remain separate fixtures'}
