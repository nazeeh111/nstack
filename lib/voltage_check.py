"""Independent accepted resistive-divider oracle; output-provided expected/error is untrusted."""
import math

def evaluate(model,reading,reported_error=None,absolute_tolerance=1e-6,relative_tolerance=0.001):
 try:
  if model['kind']!='resistive-divider':raise ValueError('Unsupported accepted circuit model')
  high,low,top,bottom=(float(model[k]) for k in ('high_volts','low_volts','top_ohms','bottom_ohms'))
  measured=float(reading);atol=float(absolute_tolerance);rtol=float(relative_tolerance)
  if not all(math.isfinite(x) for x in (high,low,top,bottom,measured,atol,rtol)) or min(top,bottom)<=0 or min(atol,rtol)<0:raise ValueError('Non-finite or invalid circuit/tolerance input')
  load=model.get('load_ohms')
  if load is not None:
   load=float(load)
   if not math.isfinite(load) or load<=0:raise ValueError('Invalid accepted load')
   bottom=1/(1/bottom+1/load)
  expected=low+(high-low)*bottom/(top+bottom)
  absolute=abs(measured-expected);percent=absolute/abs(expected)*100 if expected else None
  if reported_error is not None:
   reported=float(reported_error)
   if percent is None or not math.isfinite(reported) or abs(reported-percent)>max(1e-6,abs(percent)*1e-6):raise ValueError('Output-reported percent is inconsistent with the independent target')
  return {'status':'pass' if absolute<=atol+rtol*abs(expected) else 'fail','expected_volts':expected,'measured_volts':measured,'absolute_error_volts':absolute,'relative_error_percent':percent,'oracle':'Accepted rail/resistance/load model; independent of output expected/error fields','limits':'Circuit identity, physical applicability, simulator and output must be bound to the same actual run before report acceptance.'}
 except (KeyError,TypeError,ValueError,OverflowError) as error:return {'status':'unknown','reason':str(error)}
