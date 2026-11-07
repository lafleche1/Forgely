import unittest
from forgely_probabilites import baseline,reference,empirical,summary,wilson
class ProbabilitesTest(unittest.TestCase):
 def test_weights(self):
  self.assertEqual(reference('Ra Vi').weight,10)
  self.assertEqual(reference('Pa Sa').weight,9)
  self.assertEqual(reference('Ga Pa').weight,100)
  self.assertIsNone(reference('rune inconnue').weight)
 def test_no_invented_rate(self):
  self.assertIsNone(baseline('Ra Vi')['SC'])
  self.assertIsNone(baseline('Ga Pa')['SC'])
  self.assertIsNone(baseline('Ga Pa',exotic=True,natural_stat=True)['SC'])
 def test_exo_benchmark(self):
  self.assertEqual(baseline('Ga Pa',exotic=True,natural_stat=False)['SC'],1.)
  self.assertEqual(baseline('Ga Pa',exotic=True,natural_stat=False)['EC'],99.)
 def test_zero(self):
  result=empirical({'SC':0,'SN':0,'EC':0})
  self.assertIsNone(result['levels']['SC']['percentage'])
 def test_wilson(self):
  lo,hi=wilson(1,1)
  self.assertLess(lo,.5)
  self.assertEqual(hi,1)
 def test_rates(self):
  o=empirical({'SC':3,'SN':2,'EC':5})
  self.assertEqual(o['n'],10)
  self.assertAlmostEqual(o['levels']['SC']['percentage'],30)
  self.assertEqual(o['quality'],'insuffisant')
if __name__=='__main__':unittest.main()
