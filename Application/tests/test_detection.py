import unittest
from forgely_detection import HistoryTransitionTracker, newest_history, crop_regions
from PIL import Image

class HistoryTests(unittest.TestCase):
    def test_top_result_only(self):
        self.assertIsNone(newest_history('5 Vitalité\nÉchec'))
        self.assertEqual(newest_history('Échec\n5 Vitalité'), 'EC')
    def test_startup_ignores_history(self):
        tr = HistoryTransitionTracker(('Vi','Pa Vi'))
        self.assertIsNone(tr.observe('Échec\nÉchec', now=0))
        self.assertEqual(tr.saved,0)
    def test_changed_two_frames_and_rune(self):
        tr=HistoryTransitionTracker(('Vi','Pa Vi'))
        tr.observe('Échec\n5 Vitalité\nÉchec', rune_text='Rune Vi', now=1)
        tr.observe('Échec\n5 Vitalité\nÉchec', now=1.5)
        self.assertIsNone(tr.observe('Échec\nÉchec\n5 Vitalité\nÉchec', now=2))
        event=tr.observe('Échec\nÉchec\n5 Vitalité\nÉchec', now=3)
        self.assertEqual((event.rune,event.outcome),('Vi','EC'))
        self.assertIsNone(tr.observe('Échec\nÉchec\n5 Vitalité\nÉchec', now=4))
    def test_unknown_rune_quarantined(self):
        tr=HistoryTransitionTracker(('Vi',))
        tr.observe('Échec\n5 Vitalité\nÉchec', now=1)
        tr.observe('Échec\n5 Vitalité\nÉchec', now=1.5)
        tr.observe('Échec\nÉchec\n5 Vitalité\nÉchec', now=2)
        event=tr.observe('Échec\nÉchec\n5 Vitalité\nÉchec', now=3)
        self.assertIsNone(event.rune)
        self.assertEqual(tr.quarantined,1)
    def test_stale_rune_not_used(self):
        tr=HistoryTransitionTracker(('Vi',), rune_valid_seconds=10)
        tr.observe('Échec\n5 Vitalité\nÉchec', rune_text='Rune Vi', now=1)
        tr.observe('Échec\n5 Vitalité\nÉchec', now=1.5)
        tr.observe('Échec\nÉchec\n5 Vitalité\nÉchec',now=40)
        event=tr.observe('Échec\nÉchec\n5 Vitalité\nÉchec',now=41)
        self.assertIsNone(event.rune)
    def test_crop(self):
        im=Image.new('RGB',(1648,927))
        a,b=crop_regions(im)
        self.assertLess(a.width,400)
        self.assertLess(b.height,150)

if __name__=='__main__': unittest.main()
