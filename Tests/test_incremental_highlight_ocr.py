from PIL import ImageDraw
from test_highlight_zoom_recovery import outlined_column
from forgely_jet import read_current_jet_ocr, parse_jet
from forgely_zone_cache import ZoneCache
from unittest.mock import patch


def test_unchanged_highlight_reuses_both_variants_after_another_row_changes():
    image = outlined_column()
    cache = ZoneCache()
    calls = []
    def ocr(patch):
        calls.append(patch.size)
        return '180 Vitalité' if patch.height < 100 else '40 Intelligence'
    assert parse_jet(read_current_jet_ocr(image, ocr, row_cache=cache))['Vitalité'] == 180
    before = len(calls)
    changed = image.copy()
    ImageDraw.Draw(changed).rectangle((20, 200, 30, 210), fill='white')
    assert parse_jet(read_current_jet_ocr(changed, ocr, row_cache=cache))['Vitalité'] == 180
    assert len(calls) - before == 1
    # Even one changed pixel inside the selected row requires both rereads.
    changed.putpixel((20, 50), (255, 0, 0))
    before = len(calls)
    read_current_jet_ocr(changed, ocr, row_cache=cache)
    assert len(calls) - before == 3

    cache.clear()
    before = len(calls)
    read_current_jet_ocr(changed, ocr, row_cache=cache)
    assert len(calls) - before == 3


def test_highlight_cache_expires_and_never_turns_disagreement_into_confirmation():
    image = outlined_column()
    cache = ZoneCache(refresh_seconds=1)
    calls = []
    def ocr(current):
        calls.append(current.size)
        if current.height == image.height:
            return '40 Intelligence'
        return '180 Vitalité' if len(calls) % 2 == 0 else '130 Vitalité'
    with patch('forgely_zone_cache.monotonic', return_value=0):
        assert 'Vitalité' not in parse_jet(read_current_jet_ocr(image, ocr, row_cache=cache))
    before = len(calls)
    with patch('forgely_zone_cache.monotonic', return_value=2):
        assert 'Vitalité' not in parse_jet(read_current_jet_ocr(image, ocr, row_cache=cache))
    assert len(calls) - before == 5
