import unittest
from forgely_detection import HistoryTransitionTracker, new_row_shift, newest_history

class TrackerTests(unittest.TestCase):
    def tracker(self):
        return HistoryTransitionTracker(('Vi', 'Pa Vi'),rune_valid_seconds=8)

    def test_initial_existing_failures_not_counted(self):
        t=self.tracker()
        for _ in range(4): self.assertIsNone(t.observe('Échec\nÉchec\n5 Vitalité', now=1))
        self.assertEqual(t.saved,0)

    def test_new_failure_with_fresh_rune(self):
        t=self.tracker()
        t.observe('Échec\n5 Vitalité\nÉchec',now=1)
        t.observe('Échec\n5 Vitalité\nÉchec',now=2)
        t.remember_rune('Rune Vi',now=3)
        new='Échec\nÉchec\n5 Vitalité\nÉchec'
        self.assertIsNone(t.observe(new,now=4))
        e=t.observe(new,now=5)
        self.assertIsNotNone(e)
        self.assertEqual((e.rune,e.outcome),('Vi','EC'))
        self.assertIsNone(t.observe(new,now=6))

    def test_unknown_rune_not_saved(self):
        t=self.tracker()
        t.observe('Échec\n5 Vitalité\nÉchec',now=1)
        t.observe('Échec\n5 Vitalité\nÉchec',now=2)
        x='Échec\nÉchec\n5 Vitalité\nÉchec'
        t.observe(x,now=4)
        event=t.observe(x,now=5)
        self.assertEqual(event.outcome,'EC')
        self.assertIsNone(event.rune)
        self.assertEqual(t.quarantined,1)
        self.assertEqual(t.saved,0)

    def test_top_line_stat_is_not_success(self):
        t=self.tracker()
        t.observe('Échec\n5 Vitalité\nÉchec',now=1)
        t.observe('Échec\n5 Vitalité\nÉchec',now=2)
        x='5 Vitalité\nÉchec\n5 Vitalité\nÉchec'
        t.observe(x,now=4)
        self.assertIsNone(t.observe(x,now=5))
        self.assertEqual(t.saved,0)
        self.assertEqual(t.ignored_changes,1)

    def test_ocr_jitter_does_not_count(self):
        t=self.tracker()
        t.observe('Échec\n5 Vitalité\nÉchec',now=1)
        t.observe('Échec\n5 Vitalité\nÉchec',now=2)
        x='Échec\n6 Vitalité\nÉchec'
        t.observe(x,now=4)
        self.assertIsNone(t.observe(x,now=5))
        self.assertEqual(t.seen_changes,0)

    def test_rune_expiry(self):
        t=self.tracker()
        t.observe('Échec\n5 Vitalité\nÉchec',now=1)
        t.observe('Échec\n5 Vitalité\nÉchec',now=2)
        t.remember_rune('Rune Vi',now=3)
        x='Échec\nÉchec\n5 Vitalité\nÉchec'
        t.observe(x,now=20)
        self.assertIsNone(t.observe(x,now=21).rune)

    def test_repeated_same_history_no_new_count(self):
        t=self.tracker()
        for n in range(10): t.observe('Échec\nÉchec\n5 Vitalité',now=n)
        self.assertEqual(t.seen_changes,0)

    def test_multi_insert(self):
        self.assertEqual(new_row_shift(('echec','5 vitalite','echec'),('echec','echec','echec','5 vitalite','echec')),2)
        self.assertEqual(newest_history('5 Vitalité\nÉchec'),None)
