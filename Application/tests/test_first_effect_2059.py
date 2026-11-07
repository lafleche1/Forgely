import unittest
from PIL import Image, ImageDraw
from forgely_jet import parse_jet, read_first_effect_row

class FirstEffectTests(unittest.TestCase):
    def test_signed_values_are_not_flipped(self):
        self.assertEqual(parse_jet('-10 Coups Critiques')['Coups Critiques'], -10)
        self.assertEqual(parse_jet('0 Tacle')['Tacle'], 0)
        self.assertEqual(parse_jet('342 Vitalité')['Vitalité'], 342)

    def test_unreadable_first_row_is_not_invented(self):
        image=Image.new('RGB',(378,610),(38,40,67))
        self.assertEqual(read_first_effect_row(image),'')

if __name__ == '__main__': unittest.main()
