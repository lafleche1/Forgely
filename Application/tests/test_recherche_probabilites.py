import unittest
from forgely_recherche_probabilites import *

class RechercheTests(unittest.TestCase):
    def test_catalogue_provenance(self):
        self.assertGreaterEqual(len(catalogue()), 6)
        self.assertTrue(all(e['url'].startswith('https://') for e in catalogue()))
    def test_zero(self):
        self.assertEqual(probabilite_au_moins_un_succes(.01,0),0)
        self.assertEqual(probabilite_au_moins_un_succes(0,100),0)
        self.assertEqual(probabilite_au_moins_un_succes(1,2),1)
    def test_geometrique(self):
        self.assertAlmostEqual(probabilite_au_moins_un_succes(.01,100),1-.99**100)
        self.assertEqual(tentatives_pour_chance(.01,.5),69)
    def test_pas_de_taux_invente(self):
        self.assertFalse(exemple_exo_lourd()['estimation_dofus3'])
        self.assertEqual(tentatives_pour_chance(0,.5),None)
    def test_invalides(self):
        for args in ((-1,10),(1.1,10),(.1,-1)):
            with self.assertRaises(ValueError): probabilite_au_moins_un_succes(*args)
