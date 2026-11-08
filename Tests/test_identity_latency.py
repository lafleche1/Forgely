import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Application'))
from PIL import Image
from forgely_item_vision import recognize_item_header


def test_verified_visual_name_skips_both_ocr_passes():
    def forbidden_ocr(image):
        raise AssertionError('A verified icon must not wait for name OCR')
    assert recognize_item_header(Image.new('RGB', (400, 300)), forbidden_ocr, [],
                                 visual_name='Anneau du Cycloïde')[:2] == ('Anneau du Cycloïde', None)


def test_unknown_visual_identity_still_requires_name_ocr():
    calls = []
    def ocr(image):
        calls.append(image.size)
        return 'ANNEAU DU CYCLOÏDE'
    result = recognize_item_header(Image.new('RGB', (400, 300)), ocr,
                                  [(1, 'Anneau du Cycloïde')], visual_name=None)
    assert result[0] == 'Anneau du Cycloïde'
    assert len(calls) == 2

# Exercise the real UI message handler with real temporal trackers.
import queue
import unittest
from unittest.mock import Mock, patch
from PIL import ImageDraw
from forgely import Forgely
from forgely_continuous_identity import CurrentSlotTracker
from forgely_item_icons import ItemVisualTracker

class ConcurrentIdentityTests(unittest.TestCase):
    def test_exact_name_and_slot_confirm_on_third_frame(self):
        obj = Mock()
        obj.messages = queue.Queue()
        obj.current_slot_tracker = CurrentSlotTracker()
        obj.item_visual_tracker = ItemVisualTracker()
        obj.active_equipment_verified = False
        obj.item.get.return_value = ''
        obj.winfo_exists.return_value = False
        obj.workshop_readings.snapshot.return_value = None
        icon = Image.new('RGB', (32,32), '#38394e')
        ImageDraw.Draw(icon).ellipse((4,4,27,27), fill='#df2835')
        with patch('forgely.match_current_item', return_value=None), \
             patch('forgely.register_item', return_value=(1, 'Objet test')), \
             patch('forgely.remember_current_item'), \
             patch('forgely.item_icon', return_value=icon):
            for frame in range(3):
                obj.messages.put(('item_visual', ('Objet test', None, '', icon,
                                 None, None, (), [], None, None)))
                Forgely.process_messages(obj)
                self.assertEqual(obj.active_equipment_verified, frame == 2)
        self.assertEqual(obj.item_visual_tracker.count, 3)

class HeaderLatencyTests(unittest.TestCase):
    def test_known_icon_avoids_ocr(self):
        test_verified_visual_name_skips_both_ocr_passes()

    def test_unknown_icon_keeps_name_ocr(self):
        test_unknown_visual_identity_still_requires_name_ocr()
