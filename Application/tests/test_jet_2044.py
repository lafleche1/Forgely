import unittest
from forgely_jet import parse_jet

class Jet2044Tests(unittest.TestCase):
    def test_complete_workshop_sample(self):
        text="""297 Vitalité
39 Force
38 Intelligence
37 Agilité
9 Dommages Neutre
9 Dommages Terre
9 Dommages Feu
7 Dommages Air
285 Initiative
6% Résistance Eau
1 Tacle"""
        jet=parse_jet(text)
        self.assertEqual(jet['Dommages Neutre'],9)
        self.assertEqual(jet['Dommages Terre'],9)
        self.assertEqual(jet['Dommages Feu'],9)
        self.assertEqual(jet['Dommages Air'],7)
        self.assertEqual(jet['% Résistance Eau'],6)
        self.assertEqual(jet['Tacle'],1)
        self.assertEqual(jet['Vitalité'],297)
    def test_no_invented_stats(self):
        self.assertEqual(parse_jet('Rune Pa Fo 12\nEchec\n4,6 reliquat'),{})
    def test_conflicting_readings_are_discarded(self):
        self.assertNotIn('Force',parse_jet('10 Force\n11 Force'))
