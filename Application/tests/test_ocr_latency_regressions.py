import queue
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PIL import Image
import forgely_jet
from forgely import Forgely
from forgely_item_vision import match_truncated_official_name


class OcrLatencyRegressions(unittest.TestCase):
    def test_complete_unregistered_name_is_not_a_truncated_match(self):
        self.assertIsNone(match_truncated_official_name('ANNEAU DU CYCLOÏDE'))

    def test_real_truncated_name_can_still_use_unique_catalogue_suffix(self):
        self.assertEqual(match_truncated_official_name('AU DU CYCLOÏDE'), 'Anneau du Cycloïde')

    def test_failed_first_row_is_not_read_again_until_pixels_change(self):
        image = Image.new('RGB', (380, 480), 'white')
        forgely_jet._FIRST_ROW_FAILURES.clear()
        with patch('pytesseract.image_to_string', return_value='no readable row') as ocr:
            self.assertEqual(forgely_jet.read_first_effect_row(image), '')
            first_calls = ocr.call_count
            self.assertGreater(first_calls, 0)
            self.assertEqual(forgely_jet.read_first_effect_row(image), '')
            self.assertEqual(ocr.call_count, first_calls)
            image.putpixel((140, 100), (0, 255, 0))
            forgely_jet.read_first_effect_row(image)
            self.assertGreater(ocr.call_count, first_calls)

    def test_unknown_item_message_keeps_anonymous_slot_without_name_error(self):
        obj = Mock()
        obj.messages = queue.Queue()
        obj.messages.put(('item_visual', (None, None, '', Image.new('RGB', (32, 32)),
                                         None, None, (), [], None, None)))
        obj.current_slot_tracker = SimpleNamespace(
            observe=lambda *_: (True, False), signature=(), count=3)
        obj.item.get.return_value = ''
        obj.active_equipment_verified = False
        obj.provisional_slot_id = None
        obj.winfo_exists.return_value = False
        with patch('forgely.match_current_item', return_value=None), \
             patch('forgely.remember_provisional', return_value=7):
            Forgely.process_messages(obj)
        self.assertEqual(obj.provisional_slot_id, 7)


class CaptureConfirmationTests(unittest.TestCase):
    def test_requested_confirmation_publishes_unchanged_current_capture(self):
        obj = SimpleNamespace(
            stop_event=threading.Event(), confirmation_requested=threading.Event(),
            capture=Mock(), frame_mailbox=Mock(), _capture_interval=0,
            _capture_gate_reference='same', _capture_gate_last_sent_ns=100,
            _capture_gate_force_ns=12_000_000_000, _visual_changes_seen=0,
            _capture_gate_changes=0, _unchanged_frames_skipped=0)
        obj.confirmation_requested.set()
        obj.capture.capture.return_value = ('current pixels', 'DOFUS')
        obj.frame_mailbox.publish.side_effect = lambda *_: obj.stop_event.set()
        # Stop after a single iteration even if the implementation ignores the request.
        with patch('forgely.workshop_change_signature', return_value='same'), \
             patch('forgely.workshop_significantly_changed', return_value=False), \
             patch('forgely.forgely_perf_ns', return_value=200), \
             patch.object(obj.stop_event, 'wait', side_effect=lambda *_: obj.stop_event.set()):
            Forgely.capture_worker(obj)
        obj.frame_mailbox.publish.assert_called_once_with('current pixels', 'DOFUS', 200, 0)
        self.assertFalse(obj.confirmation_requested.is_set())


if __name__ == '__main__':
    unittest.main()
