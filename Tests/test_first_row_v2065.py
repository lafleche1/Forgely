import unittest,sys
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Application'))
from forgely_jet import first_row_candidates,parse_jet
class FirstRowTests(unittest.TestCase):
 def test_multiple_vertical_offsets(self):
  im=Image.new('RGB',(381,484))
  self.assertEqual(len(list(first_row_candidates(im))),5)
 def test_never_guess_missing_vitality(self):
  self.assertNotIn('Vitalité',parse_jet('251 300 40 Force'))
