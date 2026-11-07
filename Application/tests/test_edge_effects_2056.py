import unittest
from pathlib import Path
from PIL import Image
from forgely_atelier import crop_zone
from forgely_jet import read_effects_ocr, parse_jet

class EdgeEffectsTest(unittest.TestCase):
    def test_edge_rows_with_mocked_targeted_ocr(self):
        patch = Image.new('RGB', (320, 460), (42, 42, 70))
        def ocr(_):
            return '31 40 40 Force\n31 40 40 Intelligence\n201 300 270 Initiative'
        # The edge-row fallback is exercised with Tesseract in real captures;
        # this test ensures the existing rows remain intact on a blank image.
        parsed = parse_jet(read_effects_ocr(patch, ocr))
        self.assertEqual(parsed['Force'], 40)
        self.assertNotIn('Vitalité', parsed)
        self.assertNotIn('Tacle', parsed)

    def test_signed_values_and_zero(self):
        parsed = parse_jet('−10 Coups Critiques\n0 Tacle\n342 Vitalité')
        self.assertEqual(parsed['Coups Critiques'], -10)
        self.assertEqual(parsed['Tacle'], 0)
        self.assertEqual(parsed['Vitalité'], 342)
