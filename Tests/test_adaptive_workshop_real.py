from pathlib import Path
from PIL import Image
from forgely_workshop_layout import WorkshopLocator


def test_real_workshop_overlapping_quest_panel_does_not_merge_their_headers():
    image = Image.open(Path(__file__).parent/'fixtures/live_20261107/frame_027.png')
    locator = WorkshopLocator()
    locator.normalize(image)
    assert locator.verified
    scale, dx, dy = locator.transform
    assert abs((scale*274+dx)-208) < 18
    assert abs((scale*137+dy)-115) < 12
