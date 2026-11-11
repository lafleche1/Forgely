from types import SimpleNamespace
from unittest.mock import patch

import unittest
from PIL import Image, ImageDraw

from forgely import GameCapture, workshop_change_signature, workshop_significantly_changed
from forgely_atelier import (title_candidates, specialized_title_candidates,
                             focus_workshop, workshop_visual_fallback)


def test_capture_discards_unrelated_pixels_but_preserves_workshop(size=(1648, 928)):
    image = Image.new('RGB', size, 'white')
    window = SimpleNamespace(_hWnd=42, title='DOFUS', width=size[0],
                             height=size[1], isMinimized=False)
    capture = GameCapture()
    with patch('forgely.foreground_handle', return_value=42), \
         patch('forgely.list_dofus_windows', return_value=[window]), \
         patch('forgely.foreground_belongs_to_game', return_value=True), \
         patch.object(capture, '_foreground_image', return_value=image):
        focused, _ = capture.capture()
    assert focused.getpixel((int(.85*size[0]), int(.5*size[1]))) == (0, 0, 0)
    for x, y in ((.22, .4), (.4, .4), (.55, .32), (.35, .21), (.4, .21)):
        assert focused.getpixel((int(x*size[0]), int(y*size[1]))) == (255, 255, 255)
    assert focused.size == image.size
    assert image.getpixel((0, 0)) == (255, 255, 255)


def test_expanded_title_search_cannot_read_unrelated_text():
    image = Image.new('RGB', (1648, 928))
    ImageDraw.Draw(image).rectangle((410, 112, 440, 130), fill='white')
    assert all(candidate.getbbox() is None for candidate in title_candidates(image))
    assert all(candidate.getbbox() is None for candidate in specialized_title_candidates(image))


def test_focus_preserves_structural_checks_and_rejects_closed_workshop():
    from test_workshop_layout import workshop_scene
    image = workshop_scene()
    assert workshop_visual_fallback(image)
    assert workshop_visual_fallback(focus_workshop(image))
    assert not workshop_visual_fallback(focus_workshop(Image.new('RGB', image.size)))


def test_chat_and_map_changes_do_not_wake_ocr_but_history_does():
    image = Image.new('RGB', (1648, 928))
    changed = image.copy()
    draw = ImageDraw.Draw(changed)
    draw.rectangle((0, 800, 1647, 927), fill='white')
    draw.rectangle((1100, 0, 1647, 799), fill='white')
    assert not workshop_significantly_changed(workshop_change_signature(image),
                                              workshop_change_signature(changed))
    draw.rectangle((300, 350, 400, 390), fill='white')
    assert workshop_significantly_changed(workshop_change_signature(image),
                                          workshop_change_signature(changed))


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for size in ((1648, 928), (1280, 720), (1920, 1080)):
        suite.addTest(unittest.FunctionTestCase(
            lambda size=size: test_capture_discards_unrelated_pixels_but_preserves_workshop(size),
            description=f"focused capture {size}"))
    for test in (test_expanded_title_search_cannot_read_unrelated_text,
                 test_focus_preserves_structural_checks_and_rejects_closed_workshop,
                 test_chat_and_map_changes_do_not_wake_ocr_but_history_does):
        suite.addTest(unittest.FunctionTestCase(test))
    return suite
