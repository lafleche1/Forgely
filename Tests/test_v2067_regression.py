import sys, unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"Application"))
import forgely_jet
class RegressionTests(unittest.TestCase):
    def test_missing_first_row_is_throttled(self):
        image=Image.new("RGB",(380,480),"white")
        forgely_jet._FIRST_ROW_FAILURES.clear()
        with patch("pytesseract.image_to_string",return_value="no readable row") as ocr:
            self.assertEqual(forgely_jet.read_first_effect_row(image),"")
            self.assertEqual(ocr.call_count,10)  # RGB and mask for five possible rows
            self.assertEqual(forgely_jet.read_first_effect_row(image),"")
            self.assertEqual(ocr.call_count,10)  # unchanged pixels reuse the failed result
    def test_jet_never_invents_vitality(self):
        self.assertNotIn("Vitalité",forgely_jet.parse_jet("31 40 40 Force"))
if __name__=="__main__": unittest.main()
