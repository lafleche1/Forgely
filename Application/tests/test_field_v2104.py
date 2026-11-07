"""Regressions derived from stat-only DOFUS history (no player identity)."""
import unittest
import queue
from unittest.mock import Mock, patch
from PIL import Image, ImageDraw
import forgely_fast_preview as fast
from forgely_ocr_diagnostic import evaluate
from forgely import Forgely
from forgely_detection import HistoryTransitionTracker

OLD = '+ ANNEAU DU CYCLOÏDE\n-2 Dommages Feu\n-3 Force\n-2 Dommages Air\n+3 Force'
NEW = OLD + '\n-7 Force'
RAW = 'HISTORIQUE\n' + NEW + '\nEFFETS\n290 Vitalité\nRUNES (Pa / Ra)\nAodif. Pa Ra\n2277 1) 265\nRELIQUAT\nreliauat :05\nVISION\nVision non calibrée'


class FieldRegressions(unittest.TestCase):
    def setUp(self):
        self.image = Image.new('RGB', (1648, 928), '#38394e')
        self.icon = Image.new('RGB', (32, 32), '#38394e')
        ImageDraw.Draw(self.icon).ellipse((4, 4, 27, 27), fill='gold')

    def test_stat_only_history_displays_additions_without_inventing_outcome(self):
        reader = fast.FastRunePreview(('Fo',))
        with patch.object(fast, 'workshop_visual_fallback', return_value=True), \
             patch.object(fast, 'current_icon', return_value=self.icon):
            initial = reader.read(self.image, 'DOFUS', lambda _: OLD)
            self.assertEqual(initial.changes, ())
            first = reader.read(self.image, 'DOFUS', lambda _: NEW)
            self.assertEqual(first.changes, (('Force', -7),))
            self.assertFalse(first.changes_stable)
            self.assertIsNone(first.event)
            second = reader.read(self.image, 'DOFUS', lambda _: NEW)
            self.assertEqual(second.changes, (('Force', -7),))
            self.assertTrue(second.changes_stable)
            self.assertIsNone(second.event)

    def test_stat_only_history_never_launches_useless_rune_ocr(self):
        reader = fast.FastRunePreview(('Fo',))
        zones = []
        def ocr(patch):
            zones.append(patch.info['forgely_preview_zone'])
            return OLD
        with patch.object(fast, 'workshop_visual_fallback', return_value=True), \
             patch.object(fast, 'current_icon', return_value=self.icon):
            reader.read(self.image, 'DOFUS', ocr)
            reader.read(self.image, 'DOFUS', ocr)
        self.assertEqual(zones, ['history', 'history'])

    def test_health_does_not_treat_numbers_as_a_recognized_rune(self):
        report = evaluate(RAW, running=True, item_verified=True, jet_verified=True)
        self.assertTrue(any('Rune non reconnue' in r for r in report.reasons))
        self.assertTrue(any('SC/SN/EC' in r for r in report.reasons))

    def test_slow_observation_is_a_reported_problem(self):
        report = evaluate(RAW, running=True, item_verified=True, jet_verified=True,
                          observation_delay_ms=5760)
        self.assertTrue(any('5760' in r for r in report.reasons))

    def test_stat_only_history_does_not_request_outcome_confirmations(self):
        tracker = HistoryTransitionTracker(('Fo',))
        for text in (OLD, OLD, NEW):
            self.assertIsNone(tracker.observe(text))
            self.assertEqual(tracker.pending_count, 0)
            self.assertEqual(tracker._init_count, 0)
        self.assertIn('SC/SN/EC', tracker.reason)

    def test_explicit_outcome_reuses_only_identical_rune_pixels(self):
        reader = fast.FastRunePreview(('Fo',))
        rune_calls = []
        def ocr(patch):
            if patch.info['forgely_preview_zone'] == 'runes':
                rune_calls.append(1)
                return 'Rune Fo'
            return 'Échec\n-3 Force\nÉchec'
        with patch.object(fast, 'workshop_visual_fallback', return_value=True), \
             patch.object(fast, 'current_icon', return_value=self.icon):
            reader.read(self.image, 'DOFUS', ocr)
            reader.read(self.image, 'DOFUS', ocr)
            self.assertEqual(len(rune_calls), 1)
            self.image.putpixel((round(.55 * self.image.width), round(.30 * self.image.height)), (255, 0, 0))
            reader.read(self.image, 'DOFUS', ocr)
            self.assertEqual(len(rune_calls), 2)

    def test_variation_preview_never_writes_or_invalidates_current_jet(self):
        obj = Mock()
        obj.messages = queue.Queue()
        obj.last_full_event_frame_id = 0
        obj.last_displayed_result_frame_id = 0
        obj.live_jet = {'Force': 33}
        obj.live_pool = .5
        obj.messages.put(('fast_changes', (3, 100, ((('Force', -7),), False), 0, 'A', self.icon, obj.frame_mailbox)))
        obj.winfo_exists.return_value = False
        with patch('forgely.forgely_perf_ns', return_value=200), \
             patch('forgely.insert_observation') as insert, \
             patch('forgely.insert_unassigned') as unassigned:
            Forgely.process_messages(obj)
        self.assertEqual(obj.detect_label.configure.call_args.kwargs['text'], '-7 Force · à vérifier')
        self.assertIn('Lecture à confirmer', obj.detect_help.configure.call_args.kwargs['text'])
        self.assertEqual(obj.live_jet, {'Force': 33})
        self.assertEqual(obj.live_pool, .5)
        insert.assert_not_called()
        unassigned.assert_not_called()


if __name__ == '__main__':
    unittest.main()
