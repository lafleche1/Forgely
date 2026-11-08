from forgely_context import FusionPairing
import unittest
import queue
import threading
from types import SimpleNamespace
from unittest.mock import Mock, patch
from PIL import Image, ImageDraw
import forgely_fast_preview as fast
from forgely import Forgely
from forgely_detection import Observation


class FastPreviewTests(unittest.TestCase):
    def setUp(self):
        self.image = Image.new('RGB', (1648, 928), '#38394e')
        self.icon = Image.new('RGB', (32, 32), '#38394e')
        ImageDraw.Draw(self.icon).ellipse((4, 4, 27, 27), fill='gold')
        self.before = 'ANNEAU\nÉchec\n15 Vitalité\nÉchec'
        self.after = 'ANNEAU\nRéussite critique\nÉchec\n15 Vitalité\nÉchec'

    def reader(self, history):
        def ocr(patch):
            self.assertIn(patch.info['forgely_preview_zone'], ('history', 'runes'))
            return history if patch.info['forgely_preview_zone'] == 'history' else 'Rune Ra Vi'
        return ocr

    def test_two_new_reads_display_one_result_without_reading_effects(self):
        preview = fast.FastRunePreview(('Vi', 'Ra Vi'))
        with patch.object(fast, 'workshop_visual_fallback', return_value=True), \
             patch.object(fast, 'current_icon', return_value=self.icon):
            self.assertTrue(preview.read(self.image, 'DOFUS', self.reader(self.before)).needs_confirmation)
            self.assertIsNone(preview.read(self.image, 'DOFUS', self.reader(self.before)).event)
            self.assertTrue(preview.read(self.image, 'DOFUS', self.reader(self.after)).needs_confirmation)
            result = preview.read(self.image, 'DOFUS', self.reader(self.after))
            self.assertEqual((result.event.rune, result.event.outcome), ('Ra Vi', 'SC'))
            self.assertFalse(result.needs_confirmation)
            self.assertIsNone(preview.read(self.image, 'DOFUS', self.reader(self.after)).event)

    def test_missing_workshop_resets_old_history_before_resuming(self):
        preview = fast.FastRunePreview(('Ra Vi',))
        with patch.object(fast, 'current_icon', return_value=self.icon), \
             patch.object(fast, 'workshop_visual_fallback', return_value=True):
            preview.read(self.image, 'A', self.reader(self.before))
            preview.read(self.image, 'A', self.reader(self.before))
        with patch.object(fast, 'workshop_visual_fallback', return_value=False):
            self.assertIsNone(preview.read(self.image, 'A', lambda _: self.fail('OCR outside workshop')).event)
        with patch.object(fast, 'current_icon', return_value=self.icon), \
             patch.object(fast, 'workshop_visual_fallback', return_value=True):
            self.assertIsNone(preview.read(self.image, 'A', self.reader(self.after)).event)
            self.assertIsNone(preview.read(self.image, 'A', self.reader(self.after)).event)

    def test_account_change_creates_new_reference(self):
        preview = fast.FastRunePreview(('Ra Vi',))
        with patch.object(fast, 'current_icon', return_value=self.icon), \
             patch.object(fast, 'workshop_visual_fallback', return_value=True):
            preview.read(self.image, 'A', self.reader(self.before))
            preview.read(self.image, 'A', self.reader(self.before))
            self.assertIsNone(preview.read(self.image, 'B', self.reader(self.after)).event)
            self.assertIsNone(preview.read(self.image, 'B', self.reader(self.after)).event)

    def test_preview_ui_displays_unverified_result_without_database_write(self):
        obj = Mock()
        obj.fusion_pairing=FusionPairing()
        obj.messages = queue.Queue()
        obj.last_full_event_frame_id = 0
        obj.last_displayed_result_frame_id = 0
        obj.fast_preview_performance = Mock()
        obj.messages.put(('fast_preview', (3, 100, Observation('Ra Vi', 'SC', '', 'OCR à vérifier'), 0, 'A', self.icon, obj.frame_mailbox)))
        obj.winfo_exists.return_value = False
        with patch('forgely.forgely_perf_ns', return_value=200), \
             patch('forgely.insert_observation') as insert, \
             patch('forgely.insert_unassigned') as unassigned:
            Forgely.process_messages(obj)
        self.assertIn('Ra Vi', obj.detect_label.configure.call_args.kwargs['text'])
        self.assertIn('à vérifier', obj.detect_label.configure.call_args.kwargs['text'])
        insert.assert_not_called()
        unassigned.assert_not_called()

    def test_late_preview_does_not_replace_fully_processed_result(self):
        obj = Mock()
        obj.fusion_pairing=FusionPairing()
        obj.messages = queue.Queue()
        obj.last_full_event_frame_id = 4
        obj.last_displayed_result_frame_id = 4
        obj.messages.put(('fast_preview', (3, 100, Observation('Ra Vi', 'SC', '', 'OCR à vérifier'), 0, 'A', self.icon, obj.frame_mailbox)))
        obj.winfo_exists.return_value = False
        Forgely.process_messages(obj)
        obj.detect_label.configure.assert_not_called()

    def test_capture_invalidation_rejects_queued_preview(self):
        from forgely import LatestFrameMailbox
        obj = Mock()
        obj.frame_mailbox = LatestFrameMailbox()
        obj.frame_mailbox.publish(self.image, 'A', 100, 0)
        old_generation = obj.frame_mailbox.generation()
        obj.frame_mailbox.invalidate('not foreground')
        self.assertFalse(Forgely.preview_is_current(obj, old_generation, 'A', self.icon))

    def test_stopped_session_cannot_display_a_queued_preview(self):
        from forgely import LatestFrameMailbox
        obj = Mock()
        obj.running = False
        obj.stop_event = threading.Event()
        obj.frame_mailbox = LatestFrameMailbox()
        obj.frame_mailbox.publish(self.image, 'A', 100, 0)
        with patch('forgely_atelier.workshop_visual_fallback', return_value=True), \
             patch('forgely.current_icon', return_value=self.icon):
            self.assertFalse(Forgely.preview_is_current(obj, 0, 'A', self.icon, obj.frame_mailbox))

    def test_restarted_session_rejects_previous_mailbox_even_same_generation(self):
        from forgely import LatestFrameMailbox
        obj = Mock()
        obj.running = True
        obj.stop_event = threading.Event()
        old_mailbox = LatestFrameMailbox()
        obj.frame_mailbox = LatestFrameMailbox()
        obj.frame_mailbox.publish(self.image, 'A', 100, 0)
        with patch('forgely_atelier.workshop_visual_fallback', return_value=True), \
             patch('forgely.current_icon', return_value=self.icon):
            self.assertFalse(Forgely.preview_is_current(obj, 0, 'A', self.icon, old_mailbox))

    def test_old_full_event_is_saved_without_replacing_newer_preview(self):
        obj = Mock()
        obj.fusion_pairing=FusionPairing()
        obj.messages = queue.Queue()
        obj.last_full_event_frame_id = 0
        obj.last_displayed_result_frame_id = 20
        obj.messages.put(('auto_event_frame', (10, Observation('Vi', 'EC', '', 'OCR à vérifier'))))
        obj.live_jet = None
        obj.active_equipment_verified = True
        obj.item.get.return_value = 'Gelano'
        obj.saved_auto = 0
        obj.winfo_exists.return_value = False
        with patch('forgely.insert_observation') as insert:
            Forgely.process_messages(obj)
        insert.assert_called_once()
        obj.detect_label.configure.assert_not_called()


if __name__ == '__main__':
    unittest.main()

