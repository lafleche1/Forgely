from PIL import Image
from unittest.mock import patch
from forgely_workshop_layout import WorkshopLocator
from forgely_atelier import read_atelier
from forgely_zone_cache import ZoneCache
from test_workshop_layout import workshop_scene


def test_structural_color_match_does_not_skip_header_alignment():
    scene=workshop_scene()
    moved=scene.transform(scene.size,Image.Transform.AFFINE,(1,0,25,0,1,0))
    from forgely_atelier import workshop_visual_fallback
    assert workshop_visual_fallback(moved)
    locator=WorkshopLocator();locator.normalize(moved)
    assert locator.verified
    assert locator.transform is not None
    assert abs(locator.transform[1]+25)<5


def test_recognized_title_with_unreadable_effects_and_pool_is_not_a_reading():
    scene=workshop_scene()
    with patch('forgely_jet.read_effects_ocr',return_value='PSE xe'),patch('forgely_jet.recover_missing_effects_live',return_value=({},{})):
        result=read_atelier(scene,lambda image:'joaillomager',ZoneCache(),{})
    assert not result.readable
    assert 'illisible' in result.reason.lower()
