"""Exact-pixel recovery reuse must never hide a changed selected row."""
import sys
from pathlib import Path
from unittest.mock import patch

from PIL import Image
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Application'))
import forgely_jet as jet


@pytest.fixture(autouse=True)
def clear_recovery_cache():
    jet._LIVE_RECOVERY_CACHE.clear()
    yield
    jet._LIVE_RECOVERY_CACHE.clear()


def test_unchanged_frames_do_not_repeat_targeted_ocr():
    image = Image.new('RGB', (160, 100), '#291f40')
    with patch.object(jet, '_recover_missing_effects_live', return_value=({}, {'status': 'empty'})) as read:
        for _ in range(30):
            assert jet.recover_missing_effects_live(image.copy(), {'Force': 40})[0] == {}
    assert read.call_count == 1


def test_changed_highlight_or_existing_values_require_current_read():
    image = Image.new('RGB', (160, 100), '#291f40')
    with patch.object(jet, '_recover_missing_effects_live', return_value=({}, {'status': 'empty'})) as read:
        jet.recover_missing_effects_live(image, {'Force': 40})
        image.putpixel((60, 30), (240, 240, 240))
        jet.recover_missing_effects_live(image, {'Force': 40})
        jet.recover_missing_effects_live(image, {'Force': 41})
    assert read.call_count == 3


def test_errors_retry_and_recovery_results_are_not_mutable_cache_aliases():
    image = Image.new('RGB', (160, 100))
    with patch.object(jet, '_recover_missing_effects_live', side_effect=[RuntimeError('OCR'), ({'Tacle': 0}, {'status': 'read'})]) as read:
        with pytest.raises(RuntimeError):
            jet.recover_missing_effects_live(image, {})
        found, diagnostic = jet.recover_missing_effects_live(image, {})
        found['Tacle'] = 99
        diagnostic['status'] = 'mutated'
        assert jet.recover_missing_effects_live(image, {}) == ({'Tacle': 0}, {'status': 'read'})
    assert read.call_count == 2


def test_recovery_retries_after_bounded_ttl():
    image = Image.new('RGB', (160, 100))
    with patch.object(jet, 'monotonic', side_effect=[0, 0, 7, 8, 8]), patch.object(jet, '_recover_missing_effects_live', return_value=({}, {})) as read:
        for _ in range(3):
            jet.recover_missing_effects_live(image, {})
    assert read.call_count == 2


def test_native_green_mask_matches_exact_integer_thresholds():
    import random
    pixels = [(r, g, b) for r in range(256) for g in (73, 74, 75, 150, 254, 255)
              for b in (0, 69, 70, 140, 239, 240, 255)]
    rng = random.Random(7)
    pixels += [tuple(rng.randrange(256) for _ in range(3)) for _ in range(20000)]
    image = Image.new('RGB', (len(pixels), 1))
    image.putdata(pixels)
    assert jet.green_effect_mask(image).tobytes() == bytes([
        0 if g >= 74 and g * 100 > r * 117 and g * 100 > b * 106 else 255
        for r, g, b in pixels])


def test_stable_empty_panel_launches_only_one_strip_scan():
    image = Image.new('RGB', (160, 100), '#291f40')
    with patch('pytesseract.image_to_string', return_value='') as ocr:
        for _ in range(30):
            assert jet.recover_missing_effects_live(image, {'Force': 40})[0] == {}
    # Nine strips with two independent variants, once for all 30 frames.
    assert ocr.call_count == 18


def test_recovery_cache_is_bounded():
    with patch.object(jet, '_recover_missing_effects_live', return_value=({}, {})):
        for value in range(12):
            jet.recover_missing_effects_live(Image.new('RGB', (160, 100), (value, 0, 0)), {})
    assert len(jet._LIVE_RECOVERY_CACHE) == 4
