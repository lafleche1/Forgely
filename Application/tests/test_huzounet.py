import unittest
from forgely_huzounet import classify_attempt,exo_success_reference,reliquat_gain,priority_note,strategic_context
from forgely_probabilites import baseline

class HuzounetGuideTests(unittest.TestCase):
 def test_attempt_kinds(self):
  self.assertEqual(classify_attempt(natural_present=True,current=290,natural_max=300,proposed=295),'fm_classique')
  self.assertEqual(classify_attempt(natural_present=True,current=290,natural_max=300,proposed=310),'over')
  self.assertEqual(classify_attempt(natural_present=False,current=0,natural_max=None,proposed=1),'exo')
  self.assertEqual(classify_attempt(natural_present=None,current=0,natural_max=None,proposed=1),'inconnu')
 def test_exo_density_threshold(self):
  self.assertIsNone(exo_success_reference(natural_present=False,rune_density=20).sc_pct)
  self.assertIsNone(exo_success_reference(natural_present=True,rune_density=100).sc_pct)
  self.assertIsNone(exo_success_reference(natural_present=False,rune_density=None).sc_pct)
  heavy=exo_success_reference(natural_present=False,rune_density=30)
  self.assertEqual((heavy.sc_pct,heavy.sn_pct,heavy.ec_pct),(1,0,99))
  self.assertEqual(baseline('Ra Sa',exotic=True,natural_stat=False)['SC'],1)
  self.assertIsNone(baseline('Ra Sa',exotic=True,natural_stat=True)['SC'])
 def test_reliquat(self):
  self.assertEqual(reliquat_gain(lost_density=30,rune_density=3),27)
  self.assertEqual(reliquat_gain(lost_density=2,rune_density=3,current_reliquat=4),3)
  with self.assertRaises(ValueError): reliquat_gain(lost_density=-1,rune_density=3)
 def test_advice_is_qualitative(self):
  self.assertIn('maximum',priority_note(target_ratio=1.0,rune_density=10,reliquat=5))
  self.assertIn('compromis',strategic_context('concessions'))
if __name__=='__main__': unittest.main()
