import unittest
from forgely_fm_model import classify, classify_item, extra_weight_total, check_budget, simulate_distribution, chance_independent_chain
from forgely_probabilites import baseline

class FMModelTests(unittest.TestCase):
 def test_natural_and_over(self):
  self.assertEqual(classify('Vitalité',300,300,natural_present=True).kind,'naturel')
  self.assertEqual(classify('Vitalité',320,300,natural_present=True).kind,'over')
  self.assertEqual(classify('Vitalité',320,300,natural_present=True).extra_weight,4)
 def test_exo_general(self):
  x=classify_item({'PA':1,'Résistance Feu':3,'Vitalité':305},{'Vitalité':300})
  self.assertEqual([s.kind for s in x],['exo','exo','over'])
 def test_two_pa_impossible(self):
  self.assertFalse(check_budget({'PA':2},{})['valid'])
 def test_multi_exo_possible_under_limit(self):
  self.assertTrue(check_budget({'PA':1,'Force':1},{})['valid'])
 def test_unknown_weights_do_not_pass(self):
  self.assertIsNone(check_budget({'stat inconnue':1},{})['valid'])
 def test_community_only_heavy(self):
  self.assertEqual(baseline('Po',exotic=True,natural_stat=False)['SC'],1)
  self.assertIsNone(baseline('Ra Vi',exotic=True,natural_stat=False)['SC'])
  self.assertIsNone(baseline('Po',exotic=True,natural_stat=True)['SC'])
 def test_chain_is_not_universal(self):
  self.assertAlmostEqual(chance_independent_chain([.01,.01]),.0001)
 def test_synthetic_separation(self):
  x=simulate_distribution({'SC':.01,'SN':0.,'EC':.99},1000)
  self.assertEqual(x['source'],'simulation_hypothetique_non_observation')
  self.assertEqual(sum(x['counts'].values()),1000)
 def test_invalid_sim(self):
  with self.assertRaises(ValueError):simulate_distribution({'SC':.3,'SN':.3,'EC':.3})
if __name__=='__main__':unittest.main()
