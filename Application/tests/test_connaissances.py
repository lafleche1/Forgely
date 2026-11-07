import unittest
from forgely_connaissances import FACTS, CONFLICTS, SOURCES, advice_context, sources_for

class TestConnaissances(unittest.TestCase):
    def test_every_source_exists(self):
        for f in FACTS:
            self.assertTrue(f.sources)
            for s in f.sources:self.assertTrue(SOURCES[s].startswith('https://'))
    def test_no_brisage_in_fm_probability(self):
        self.assertEqual(next(f for f in FACTS if f.key=='focus').scope,'brisage')
    def test_risk_context(self):
        notes=advice_context(natural_max_known=False,pool_confirmed=False,kind='exo',rune_weight=100)
        self.assertEqual(len(notes),4)
        self.assertNotIn('1 %',' '.join(notes))
    def test_conflicts_explicit(self):
        self.assertIn('puit_estime',CONFLICTS)
        self.assertTrue(sources_for('weight'))
