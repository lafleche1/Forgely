from PIL import Image
from forgely_jet import parse_jet, read_effects_ocr
from forgely_continuous_identity import effect_signature


def test_current_column_is_read_independently_from_natural_bounds(monkeypatch):
    import forgely_jet
    monkeypatch.setattr(forgely_jet, 'read_first_effect_row', lambda _: '')
    monkeypatch.setattr('pytesseract.image_to_string', lambda *a, **k: '')
    image = Image.new('RGB', (400, 500), 'white')
    # Full table OCR loses the current number; Min/Max cannot fill that gap.
    def ocr(patch):
        return '7 10 Dommages Neutre' if patch.width == 400 else '4 Dommages Neutre'
    text = read_effects_ocr(image, ocr)
    assert parse_jet(text) == {'Dommages Neutre': 4}
    assert ('dommages neutre', 7, 10) in effect_signature(text)


def test_missing_current_column_does_not_fall_back_to_maximum(monkeypatch):
    import forgely_jet
    monkeypatch.setattr(forgely_jet, 'read_first_effect_row', lambda _: '')
    monkeypatch.setattr('pytesseract.image_to_string', lambda *a, **k: '')
    image = Image.new('RGB', (400, 500), 'white')
    text = read_effects_ocr(image, lambda p: '7 10 Dommages Neutre' if p.width == 400 else '')
    assert 'Dommages Neutre' not in parse_jet(text)


def test_conflicting_readings_cannot_become_valid_by_repetition():
    assert 'Force' not in parse_jet('38 Force\n39 Force\n39 Force')
