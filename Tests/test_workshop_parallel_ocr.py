"""Independent workshop regions must not wait for effects OCR."""
import threading
from unittest.mock import patch
from PIL import Image
from forgely_atelier import read_atelier


def test_workshop_regions_start_together_and_keep_frame_results():
    barrier = threading.Barrier(4)
    image = Image.new('RGB', (1648, 928))

    def read(patch_image):
        # Four independent readers must have entered before any can finish.
        barrier.wait(timeout=2)
        return str(patch_image.size)

    with patch('forgely_atelier.workshop_visual_fallback', return_value=True), \
         patch('forgely_jet.read_effects_ocr', side_effect=lambda im, ocr: ocr(im)), \
         patch('forgely_atelier.read_reliquat_ocr', side_effect=lambda im, ocr: ocr(im)), \
         patch('forgely_jet.recover_missing_effects_live', return_value=({}, {})):
        result = read_atelier(image, read, title_cache={})
    assert result.active
    assert len({result.history, result.effects, result.runes, result.reliquat}) == 4
    assert set(result.timings) >= {'historique', 'effets', 'runes', 'reliquat'}
