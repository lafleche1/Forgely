from pathlib import Path
from PIL import Image
from unittest.mock import patch
from forgely_atelier import workshop_visual_fallback
from forgely_workshop_layout import WorkshopLocator,header_bands


def test_already_valid_workshop_is_not_invalidated_by_another_header_search():
    # Real capture used to alternate "verified" while retaining the same pixels.
    fixture=Path(__file__).parent/'fixtures/history_unity_20261109/video_185054_20s.png'
    im=Image.open(fixture).convert('RGB');assert workshop_visual_fallback(im)
    locator=WorkshopLocator()
    with patch('forgely_workshop_layout.header_bands',wraps=header_bands) as search:
        for _ in range(3):
            out=locator.normalize(im,'same window')
            assert locator.verified
            assert locator.transform is not None
        assert search.call_count==1
