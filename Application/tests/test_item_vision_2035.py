"""0.20.35: intermittent OCR, cross-view recovery, stable visual identity."""
import unittest
from pathlib import Path
from PIL import Image
from forgely_item_vision import recognize_item_header
from forgely_item_icons import ItemVisualTracker


class ItemVision2035Tests(unittest.TestCase):
    def setUp(self):
        self.image=Image.new('RGB',(1920,1080))
        self.icon=Image.new('RGB',(32,32),'#353850')
        from PIL import ImageDraw
        ImageDraw.Draw(self.icon).ellipse((4,4,27,27),fill='gold',outline='white',width=2)

    def test_enhanced_view_recovers_unreadable_first_view(self):
        readings=iter(('', 'ANNEAU DU CYCLOÏDE'))
        known,candidate,raw=recognize_item_header(self.image, lambda _: next(readings), [])
        self.assertIsNone(known)
        self.assertEqual(candidate,'ANNEAU DU CYCLOÏDE')

    def test_first_view_recovers_unreadable_second_view(self):
        readings=iter(('ANNEAU DU CYCLOÏDE', ''))
        known,candidate,raw=recognize_item_header(self.image, lambda _: next(readings), [])
        self.assertIsNone(known)
        self.assertEqual(candidate,'ANNEAU DU CYCLOÏDE')

    def test_two_conflicting_views_never_create_candidate(self):
        readings=iter(('ANNEAU DU CYCLOÏDE', 'ANNEAU DU CYCLOPS'))
        self.assertEqual(recognize_item_header(self.image,lambda _: next(readings),[])[0:2],(None,None))

    def test_tracker_tolerates_short_ocr_gaps_but_requires_four_good_frames(self):
        t=ItemVisualTracker()
        self.assertEqual(t.observe('ANNEAU DU CYCLOÏDE',self.icon),1)
        self.assertEqual(t.observe(None,self.icon),0)
        self.assertEqual(t.observe('ANNEAU DU CYCLOÏDE',self.icon),2)
        self.assertEqual(t.observe(None,self.icon),0)
        self.assertEqual(t.observe('ANNEAU DU CYCLOÏDE',self.icon),3)
        self.assertEqual(t.observe('ANNEAU DU CYCLOÏDE',self.icon),4)

    def test_tracker_forgets_after_three_misses(self):
        t=ItemVisualTracker()
        for _ in range(3):t.observe('GELANO',self.icon)
        for _ in range(3):t.observe(None,None)
        self.assertEqual(t.observe('GELANO',self.icon),1)

    def test_real_saved_header_and_icon(self):
        raw=Path('/mnt/data/raw_test33.png')
        enhanced=Path('/mnt/data/enhanced_test33.png')
        if not raw.exists() or not enhanced.exists():
            self.skipTest('reference capture not available')
        from runeforge_observer import extract_text
        from forgely_item_vision import parse_item_header
        self.assertEqual(parse_item_header(extract_text(Image.open(raw))), 'ANNEAU DU CYCLOÏDE')
        self.assertEqual(parse_item_header(extract_text(Image.open(enhanced))), 'ANNEAU DU CYCLOÏDE')

if __name__ == '__main__':unittest.main()
