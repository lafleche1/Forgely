import unittest
from forgely_fm_model import classify, classify_item
from forgely_jet import parse_jet
from forgely_decision import classify as decision_classify

class UniversalJetTests(unittest.TestCase):
    def test_sign_zero_and_over(self):
        jet=parse_jet('-10 Coups Critiques\n0 Tacle\n342 Vitalité\n1 PA')
        self.assertEqual(jet['Coups Critiques'],-10)
        self.assertEqual(jet['Tacle'],0)
        self.assertEqual(jet['Vitalité'],342)
        self.assertEqual(jet['PA'],1)
    def test_negative_natural(self):
        self.assertEqual(classify('Coups Critiques',-10,0,natural_present=True).kind,'naturel')
    def test_over(self):
        self.assertEqual(classify('Vitalité',342,300,natural_present=True).kind,'over')
    def test_exo_verified_profile(self):
        self.assertEqual(classify_item({'PA':1},{'Vitalité':300})[0].kind,'exo')
    def test_partial_profile_never_invents_exo(self):
        self.assertEqual(classify_item({'PA':1},{'Vitalité':300},complete_profile=False)[0].kind,'inconnu')
        self.assertEqual(decision_classify('PA',0,1,None),'inconnu')
    def test_absent_is_not_zero(self):
        self.assertNotIn('Tacle',parse_jet('40 Force'))

if __name__=='__main__':unittest.main()
