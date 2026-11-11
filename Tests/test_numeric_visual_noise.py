from pathlib import Path
from PIL import Image, ImageDraw
import pytest

from forgely_copilot_continuity import ConfirmedAtelierRead, numeric_frame_signature


def reading(image):
    context = ('mailbox', 'DOFUS', 123, image.size)
    return ConfirmedAtelierRead(context, (), None, ({'Force': -15}, 0),
        numeric_signature=numeric_frame_signature(image))


@pytest.mark.parametrize('mode', ['RGB', 'RGBA'])
def test_same_numeric_pixels_do_not_depend_on_capture_color_mode(mode):
    image = Image.open(Path(__file__).parent/'fixtures/workshop_tetriste_20261110.png')
    source = reading(image)
    assert source.matches_numeric(source.context, image.convert(mode))


def test_small_background_and_icon_shading_changes_do_not_reset_all_confirmations():
    image = Image.new('RGB', (1648, 928), '#38394e')
    draw = ImageDraw.Draw(image)
    draw.text((620, 300), '-15 Force', fill=(220, 70, 70))
    draw.text((540, 190), 'reliquat : 0', fill=(180, 180, 180))
    draw.ellipse((651, 183, 665, 203), fill=(240, 180, 40))
    source = reading(image)
    changed = image.copy()
    # RGB changes in otherwise blank panel pixels do not change a digit.
    ImageDraw.Draw(changed).rectangle((610, 550, 700, 580), fill=(58, 59, 80))
    changed.putpixel((656, 190), (235, 175, 40))
    assert source.matches_numeric(source.context, changed)


@pytest.mark.parametrize('box', [(620, 300, 623, 301), (602, 190, 606, 191)])
def test_a_changed_minus_sign_or_pool_digit_is_not_background_noise(box):
    image = Image.new('RGB', (1648, 928), '#38394e')
    draw = ImageDraw.Draw(image)
    draw.text((620, 300), '-15 Force', fill=(220, 70, 70))
    draw.text((540, 190), 'reliquat : 0', fill=(180, 180, 180))
    source = reading(image)
    changed = image.copy()
    ImageDraw.Draw(changed).rectangle(box, fill='white')
    assert not source.matches_numeric(source.context, changed)
