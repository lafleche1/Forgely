import unittest
from forgely_ocr_diagnostic import evaluate

class TestOCRDiagnostic(unittest.TestCase):
    def test_empty(self):
        result=evaluate('',running=False,item_verified=False,jet_verified=False)
        self.assertEqual(result.level,'À VÉRIFIER')
        self.assertTrue(any('Aucune lecture' in r for r in result.reasons))
    def test_complete_is_not_certified(self):
        raw='HISTORIQUE\na\nEFFETS\nb\nRUNES (Pa / Ra)\nc\nRELIQUAT\nd\nVISION\ne'
        result=evaluate(raw,running=True,item_verified=True,jet_verified=True)
        self.assertFalse(result.reasons)
        self.assertIn('non certifiées',result.level)
        self.assertEqual(result.sections['EFFETS'],'b')
    def test_conflict(self):
        raw='VISION\nCONFLIT OCR / icône : vérification nécessaire'
        result=evaluate(raw,running=True,item_verified=True,jet_verified=True)
        self.assertTrue(any('Conflit' in r for r in result.reasons))
