import pathlib,sys,unittest,math
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'lib'));import voltage_check as v
class Voltage(unittest.TestCase):
 def test_known_loaded_negative_zero_and_false_percent(self):
  m={'kind':'resistive-divider','high_volts':5,'low_volts':0,'top_ohms':1000,'bottom_ohms':1000}
  self.assertEqual(v.evaluate(m,2.5)['status'],'pass');self.assertEqual(v.evaluate(m|{'load_ohms':1000},5/3)['status'],'pass');self.assertEqual(v.evaluate(m|{'high_volts':0,'low_volts':-5},-2.5)['status'],'pass')
  zero=m|{'high_volts':1,'low_volts':-1};self.assertEqual(v.evaluate(zero,1e-7)['status'],'pass');self.assertEqual(v.evaluate(zero,0.01)['status'],'fail');self.assertIsNone(v.evaluate(zero,0)['relative_error_percent'])
  self.assertEqual(v.evaluate(m,1,reported_error=0)['status'],'unknown');self.assertEqual(v.evaluate(m,math.nan)['status'],'unknown');self.assertEqual(v.evaluate({},2.5)['status'],'unknown')
