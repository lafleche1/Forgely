import unittest
from unittest.mock import patch
from PIL import Image
from forgely_jet import parse_jet, read_effects_ocr

class Jet2054Tests(unittest.TestCase):
    def test_negative_and_zero_and_over(self):
        values=parse_jet('251 300 342 Vitalité\n4 6 0 Tacle\n-10 Coups Critiques\n−3 Force')
        self.assertEqual(values['Vitalité'],342)
        self.assertEqual(values['Tacle'],0)
        self.assertEqual(values['Coups Critiques'],-10)
        self.assertEqual(values['Force'],-3)
    def test_sign_cannot_be_assumed(self):
        self.assertNotIn('Coups Critiques',parse_jet('− Coups Critiques'))
    def test_row_fallback_reads_color_and_border(self):
        patch_img=Image.new('RGB',(350,430),(40,40,65))
        responses=iter(['342 Vitalité','0 Tacle'])
        with patch('pytesseract.image_to_string',side_effect=lambda *a,**k:next(responses)):
            result=read_effects_ocr(patch_img,lambda im:'40 Force\n6% Résistance Eau')
        self.assertEqual(parse_jet(result)['Vitalité'],342)
        self.assertEqual(parse_jet(result)['Tacle'],0)
if __name__=='__main__':unittest.main()
