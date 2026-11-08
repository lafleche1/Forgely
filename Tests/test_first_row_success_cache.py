from unittest.mock import patch
from PIL import Image
import forgely_jet as jet
import pytest

@pytest.fixture(autouse=True)
def isolate_first_row_caches():
    jet._FIRST_ROW_SUCCESSES.clear()
    jet._FIRST_ROW_FAILURES.clear()
    yield
    jet._FIRST_ROW_SUCCESSES.clear()
    jet._FIRST_ROW_FAILURES.clear()

def test_successful_first_row_reuses_exact_pixels_only():
    jet._FIRST_ROW_SUCCESSES.clear()
    image = Image.new("RGB", (442, 680), "white")
    with patch("pytesseract.image_to_string", return_value="342 Vitalité") as ocr:
        assert jet.read_first_effect_row(image) == "342 Vitalité"
        assert jet.read_first_effect_row(image.copy()) == "342 Vitalité"
        assert ocr.call_count == 1
        image.putpixel((0, 0), (0, 0, 0))
        assert jet.read_first_effect_row(image) == "342 Vitalité"
        assert ocr.call_count == 2

def test_successful_first_row_expires():
    jet._FIRST_ROW_SUCCESSES.clear()
    image = Image.new("RGB", (442, 680), "white")
    with patch("pytesseract.image_to_string", return_value="342 Vitalité") as ocr, patch("time.monotonic", side_effect=[0, 0, 9, 9, 9]):
        jet.read_first_effect_row(image)
        jet.read_first_effect_row(image)
        assert ocr.call_count == 2


@pytest.mark.parametrize("setting", ["command", "tessdata"])
def test_successful_first_row_backend_change_requires_fresh_ocr(monkeypatch, setting):
    import pytesseract
    image = Image.new("RGB", (442, 680), "white")
    with patch("pytesseract.image_to_string", return_value="342 Vitalit\u00e9") as ocr:
        jet.read_first_effect_row(image)
        if setting == "command":
            monkeypatch.setattr(pytesseract.pytesseract, "tesseract_cmd", "different-tesseract")
        else:
            monkeypatch.setenv("TESSDATA_PREFIX", "different-tessdata")
        jet.read_first_effect_row(image)
        assert ocr.call_count == 2
