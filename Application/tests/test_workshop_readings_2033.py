"""0.20.33: provisional OCR jet and pool before first item-name visibility."""
import unittest
from forgely_workshop_readings import WorkshopReadings


class WorkshopReadings2033Tests(unittest.TestCase):
    def test_jet_and_zero_pool_stabilize_without_item(self):
        t=WorkshopReadings(3)
        for i in range(2):
            self.assertFalse(t.observe({'Vitalité': 300}, 0))
            self.assertIsNone(t.snapshot())
        self.assertTrue(t.observe({'Vitalité': 300}, 0))
        self.assertEqual(t.snapshot(), ({'Vitalité': 300}, 0))

    def test_does_not_use_a_missing_or_unreadable_pool(self):
        t=WorkshopReadings(3)
        for _ in range(4):
            self.assertFalse(t.observe({'Vitalité': 300}, None))
        self.assertIsNone(t.snapshot())
        for _ in range(4):
            self.assertFalse(t.observe({}, 0))
        self.assertIsNone(t.snapshot())

    def test_changed_jet_revokes_stability_until_three_new_frames(self):
        t=WorkshopReadings(3)
        for _ in range(3): t.observe({'Vitalité': 300}, 0)
        self.assertFalse(t.observe({'Vitalité': 299}, 0))
        self.assertIsNone(t.snapshot())
        self.assertFalse(t.observe({'Vitalité': 299}, 0))
        self.assertTrue(t.observe({'Vitalité': 299}, 0))
        self.assertEqual(t.snapshot(), ({'Vitalité': 299}, 0))

    def test_rune_event_resets_pre_item_snapshot(self):
        t=WorkshopReadings(3)
        for _ in range(3): t.observe({'Chance': 1}, 5)
        self.assertIsNotNone(t.snapshot())
        t.reset()  # called when history reports a rune, or workshop disappears
        self.assertIsNone(t.snapshot())
        self.assertEqual(t.streak, 0)

    def test_snapshot_is_a_copy(self):
        t=WorkshopReadings(3)
        jet={'Vitalité': 300}
        for _ in range(3): t.observe(jet, 0)
        jet['Vitalité']=1
        snapshot=t.snapshot()
        snapshot[0]['Vitalité']=2
        self.assertEqual(t.snapshot(), ({'Vitalité': 300}, 0))

    def test_never_stabilizes_from_nonconsecutive_frames(self):
        t=WorkshopReadings(3)
        self.assertFalse(t.observe({'Vitalité': 300}, 0))
        self.assertFalse(t.observe({'Vitalité': 301}, 0))
        self.assertFalse(t.observe({'Vitalité': 300}, 0))
        self.assertEqual(t.streak,1)
        self.assertIsNone(t.snapshot())

    def test_requires_multiple_frames(self):
        with self.assertRaises(ValueError):
            WorkshopReadings(1)


if __name__ == '__main__':
    unittest.main()

class WorkshopOverlay2033Tests(unittest.TestCase):
    def test_waiting_message_before_first_rune(self):
        from types import SimpleNamespace
        from forgely import Forgely
        state=SimpleNamespace(running=True, workshop_active=True,
                              active_equipment_verified=False, last_item_candidate='',
                              current_slot_tracker=SimpleNamespace(count=0),provisional_slot_id=None)
        self.assertEqual(Forgely.waiting_for_item_label(state), 'Lecture de l’objet')
        state.last_item_candidate='ANNEAU DU CYCLOIDE'
        self.assertEqual(Forgely.waiting_for_item_label(state), 'Objet à confirmer')
        state.active_equipment_verified=True
        self.assertIsNone(Forgely.waiting_for_item_label(state))
        state.active_equipment_verified=False
        state.workshop_active=False
        self.assertIsNone(Forgely.waiting_for_item_label(state))
