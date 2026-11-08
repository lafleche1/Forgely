import unittest
from forgely_detection import Observation


class LearningTransitionTests(unittest.TestCase):
    def test_keeps_before_snapshot_when_new_jet_is_already_visible(self):
        from forgely_learning import FusionContextTracker
        tracker = FusionContextTracker()
        for _ in range(2):
            tracker.observe('item', 'item\nEchec\n-1 Force\nEchec', {'Force': 10}, 0, None)
        tracker.observe('item', 'item\nReussite critique\nEchec\n-1 Force\nEchec', {'Force': 11}, 0, None)
        event = Observation('Fo', 'SC', '', 'confirmed')
        result = tracker.observe('item', 'item\nReussite critique\nEchec\n-1 Force\nEchec', {'Force': 11}, 0, event)
        self.assertEqual(result['before']['jet'], {'Force': 10})
        self.assertEqual(result['after']['jet'], {'Force': 11})

    def test_confirmed_failure_with_no_stat_change_is_preserved(self):
        from forgely_learning import FusionContextTracker
        from forgely_context import save_transition
        import tempfile
        from pathlib import Path
        tracker = FusionContextTracker()
        for _ in range(2):
            tracker.observe('item', 'item\nEchec\n-1 Force\nEchec', {'Force': 10}, 0, None)
        tracker.observe('item', 'item\nReussite critique\nEchec\n-1 Force\nEchec', {'Force': 10}, 0, None)
        result = tracker.observe('item', 'item\nReussite critique\nEchec\n-1 Force\nEchec', {'Force': 10}, 0,
                                 Observation('Fo', 'EC', '', 'confirmed'))
        with tempfile.TemporaryDirectory() as directory:
            saved = save_transition('item', 'Fo', 'EC', result['before'], result['after'],
                                    Path(directory) / 'ctx.db', event_confirmed=True)
        self.assertEqual(saved['changes'], {})

    def test_different_account_or_item_cannot_reuse_before(self):
        from forgely_learning import FusionContextTracker
        tracker = FusionContextTracker()
        for _ in range(2):
            tracker.observe('item A', 'item\nEchec\n-1 Force\nEchec', {'Force': 10}, 0, None)
        self.assertIsNone(tracker.observe('item B', 'item\nReussite critique\nEchec\n-1 Force\nEchec', {'Force': 11}, 0,
                                          Observation('Fo', 'SC', '', 'confirmed')))

    def test_nonfinite_and_boolean_values_are_not_learned(self):
        from forgely_context import normalize_snapshot
        for bad in (True, float('nan'), float('inf')):
            self.assertIsNone(normalize_snapshot({'Force': bad}, 0))
            self.assertIsNone(normalize_snapshot({'Force': 1}, bad))

    def test_multiple_new_rows_are_not_one_training_attempt(self):
        from forgely_learning import FusionContextTracker
        tracker = FusionContextTracker()
        old = 'item\nEchec\n-1 Force\nEchec'
        new = 'item\nReussite critique\n+1 Force\nEchec\n-1 Force\nEchec'
        for _ in range(2):
            tracker.observe('item', old, {'Force': 10}, 0, None)
        tracker.observe('item', new, {'Force': 12}, 0, None)
        self.assertIsNone(tracker.observe('item', new, {'Force': 12}, 0,
                                          Observation('Fo', 'SC', '', 'confirmed')))

    def test_early_stat_update_does_not_replace_pre_fusion_state(self):
        from forgely_learning import FusionContextTracker
        tracker = FusionContextTracker()
        old = 'item\nEchec\n-1 Force\nEchec'
        new = 'item\nReussite critique\nEchec\n-1 Force\nEchec'
        for _ in range(2):
            tracker.observe('item', old, {'Force': 10}, 0, None)
        for _ in range(2):
            tracker.observe('item', old, {'Force': 11}, 0, None)
        tracker.observe('item', new, {'Force': 11}, 0, None)
        result = tracker.observe('item', new, {'Force': 11}, 0,
                                 Observation('Fo', 'SC', '', 'confirmed'))
        self.assertEqual(result['before']['jet'], {'Force': 10})

    def test_accepted_event_waits_for_stable_post_fusion_snapshot(self):
        from forgely_learning import FusionContextTracker
        tracker = FusionContextTracker()
        old = 'item\nEchec\n-1 Force\nEchec'
        new = 'item\nReussite critique\nEchec\n-1 Force\nEchec'
        for _ in range(2):
            tracker.observe('item', old, {'Force': 10}, 0, None)
        tracker.observe('item', new, {'Force': 10}, 0, None)
        self.assertIsNone(tracker.observe('item', new, {'Force': 11}, 0,
                                          Observation('Fo', 'SC', '', 'confirmed')))
        result = tracker.observe('item', new, {'Force': 11}, 0, None)
        self.assertEqual(result['before']['jet'], {'Force': 10})
        self.assertEqual(result['after']['jet'], {'Force': 11})
        self.assertIsNone(tracker.observe('item', new, {'Force': 11}, 0, None))
