"""Regression tests for the exported DOFUS reliquat crop."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Application'))
from forgely_atelier import parse_reliquat, read_reliquat_ocr

class TestReliquat(unittest.TestCase):
    def test_explicit_decimal(self):
        self.assertEqual(parse_reliquat('reliquat : 0,9'), 0.9)
        self.assertIsNone(parse_reliquat('reliquat -0.9'))
        self.assertEqual(parse_reliquat('reliquat > 4.6'), 4.6)
        self.assertEqual(parse_reliquat('reliquat : 0'), 0.0)
    def test_no_guessed_decimal(self):
        self.assertIsNone(parse_reliquat('reliauat : 09'))
        self.assertIsNone(parse_reliquat('nimporte quoi 09'))
    def test_exported_crop(self):
        from PIL import Image
        crop = Path('/mnt/data/reliquat_20261106_220504.png')
        if not crop.exists(): self.skipTest('User OCR crop not present')
        text = read_reliquat_ocr(Image.open(crop), lambda _: 'reliauat : 09')
        self.assertEqual(parse_reliquat(text), 0.9)

if __name__ == '__main__': unittest.main()
