import unittest
from unittest.mock import patch
from PIL import Image
from forgely_jet import parse_jet, read_effects_ocr

class FastJetTests(unittest.TestCase):
    def setUp(self):
        from forgely_jet import _FIRST_ROW_FAILURES
        _FIRST_ROW_FAILURES.clear()
    def test_overmax_and_zero_are_values(self):
        self.assertEqual(parse_jet('251 300 ♥342 Vitalité\n4 6 0 Tacle'), {'Vitalité':342,'Tacle':0})

    def test_no_extra_ocr_when_complete(self):
        with patch('pytesseract.image_to_string', side_effect=AssertionError('extra OCR')):
            text=read_effects_ocr(Image.new('RGB',(330,420)), lambda _: '342 Vitalité\n0 Tacle')
        self.assertEqual(parse_jet(text)['Vitalité'],342)

    def test_missing_stat_not_invented(self):
        with patch('pytesseract.image_to_string', return_value='illisible'):
            text=read_effects_ocr(Image.new('RGB',(330,420)), lambda _: '40 Force')
        self.assertNotIn('Vitalité',parse_jet(text))

    def test_targeted_ocr_can_recover_vitality(self):
        with patch('pytesseract.image_to_string', side_effect=['342 Vitalité','illisible']):
            text=read_effects_ocr(Image.new('RGB',(330,420)), lambda _: '40 Force')
        self.assertEqual(parse_jet(text)['Vitalité'],342)

if __name__=='__main__':unittest.main()
