import unittest, sys
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"Application"))
from forgely_jet import read_effects_ocr,parse_jet
class EffectsRegression(unittest.TestCase):
    def test_real_capture_recovers_vitality_342_and_zero_tackle(self):
        import pytesseract
        image=Image.open(Path(__file__).parent/"fixtures"/"effects_vitalite_342.png")
        raw=read_effects_ocr(image,lambda im:pytesseract.image_to_string(im,config="--psm 6"))
        jet=parse_jet(raw)
        self.assertEqual(jet.get("Vitalité"),342)
        self.assertEqual(jet.get("Tacle"),0)
    def test_no_invention_if_blank(self):
        from unittest.mock import patch
        from forgely_jet import _FIRST_ROW_FAILURES
        _FIRST_ROW_FAILURES.clear()
        with patch("pytesseract.image_to_string",return_value=""):
            self.assertNotIn("Vitalité",parse_jet(read_effects_ocr(Image.new("RGB",(380,480),"white"),lambda im:"40 Force")))
