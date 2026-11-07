import unittest
from forgely_reference_publique import poids_indicatif, probabilite_sc_sn_ec

class TestReferencePublique(unittest.TestCase):
 def test_poids_pa(self):
  r=poids_indicatif('pa'); self.assertEqual(r['poids'],100); self.assertFalse(r['certifie_dofus3'])
 def test_vita_divergence(self):
  self.assertIn('divergence',poids_indicatif('vitalite')['statut'])
 def test_inconnue(self):
  self.assertIsNone(poids_indicatif('nouvelle_stat'))
 def test_no_fake_probs(self):
  self.assertIsNone(probabilite_sc_sn_ec('ga_pa'))
