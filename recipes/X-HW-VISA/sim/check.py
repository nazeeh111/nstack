"""Simulator-only VISA check. Literal @sim ensures no physical backend is opened."""
import json,importlib.metadata
import pyvisa

def check():
 manager=pyvisa.ResourceManager('@sim')
 try:
  assert manager.visalib.__class__.__module__.startswith('pyvisa_sim')
  with manager.open_resource('GPIB0::8::INSTR',read_termination='\n',write_termination='\n',timeout=1000) as instrument:
   identity=instrument.query('?IDN');assert identity=='LSG Serial #1234'
   assert instrument.query('!FREQ 321.25')=='OK'
   assert float(instrument.query('?FREQ'))==321.25
   negative=instrument.query('!FREQ 100001.00');assert negative=='FREQ_ERROR'
   assert float(instrument.query('?FREQ'))==321.25
 finally:manager.close()
 return {'versions':{p:importlib.metadata.version(p) for p in ('PyVISA','PyVISA-py','PyVISA-sim')},'backend':'@sim','identity':identity,'set_readback':321.25,'out_of_range_refused':True,'scope':'Simulator only. No real device, transport enumeration, voltage/output action or vendor backend tested.'}
if __name__=='__main__':print(json.dumps(check(),indent=2))
