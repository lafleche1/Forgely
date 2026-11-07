"""Local automatic item/icon learning regression tests (no network)."""
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
from forgely_item_icons import crop_item_icon, normalize_icon, icon_distance, ItemVisualTracker
from forgely_items import (register_item_with_icon, find_item, item_icon,
                           item_list, IconIdentityConflict)


def fake_icon(color, variant=0):
    im=Image.new('RGB',(32,32),'#353850')
    d=ImageDraw.Draw(im)
    if variant==0:
        d.ellipse((4,4,27,27),fill=color,outline='white',width=2)
    else:
        d.rectangle((5,5,26,26),fill=color,outline='white',width=2)
    return im


class ItemIcons2032Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.db=Path(self.temp.name)/'forgely.db'

    def tearDown(self):
        self.temp.cleanup()

    def test_crop_icon_on_user_screen_reference(self):
        im=Image.new('RGB',(1920,1080))
        self.assertIsNone(crop_item_icon(im))
        self.assertEqual(crop_item_icon(im, row_y=300).size,(27,28))

    def test_blank_crop_is_not_an_item(self):
        self.assertIsNone(normalize_icon(Image.new('RGB',(24,24),'#353850')))
        self.assertIsNone(ItemVisualTracker().observe('GELANO',Image.new('RGB',(24,24),'#353850')) or None)

    def test_stable_name_and_icon_required(self):
        track=ItemVisualTracker()
        a=fake_icon('gold')
        b=fake_icon('cyan',1)
        self.assertEqual([track.observe('GELANO',a) for _ in range(4)], [1,2,3,4])
        self.assertEqual(track.observe('ANNEAU DU CYCLOIDE',a),1)
        self.assertEqual(track.observe('ANNEAU DU CYCLOIDE',b),1)
        self.assertEqual(track.observe(None,a),0)

    def test_local_register_and_reuse_no_duplicates(self):
        a=fake_icon('gold')
        item=register_item_with_icon('Anneau du Cycloïde',a,self.db)
        again=register_item_with_icon('ANNEAU DU CYCLOIDE',a,self.db)
        self.assertEqual(item[0],again[0])
        self.assertEqual(len(item_list(self.db)),1)
        path=item_icon('anneau du cycloide',self.db)
        self.assertTrue(path.is_file())
        with Image.open(path) as stored:
            self.assertLess(icon_distance(stored,a),1)

    def test_refuse_duplicate_icon_for_different_name(self):
        a=fake_icon('gold')
        register_item_with_icon('GELANO',a,self.db)
        with self.assertRaises(IconIdentityConflict):
            register_item_with_icon('ANNEAU DU CYCLOIDE',a,self.db)
        self.assertIsNone(find_item('ANNEAU DU CYCLOIDE',self.db))

    def test_refuse_different_icon_for_same_name(self):
        register_item_with_icon('GELANO',fake_icon('gold'),self.db)
        with self.assertRaises(IconIdentityConflict):
            register_item_with_icon('GELANO',fake_icon('cyan',1),self.db)
        self.assertEqual(len(item_list(self.db)),1)

    def test_reference_icon_crop_has_visual_detail(self):
        reference=Path('/mnt/data/Capture d\'écran 2026-11-06 190438.png')
        if reference.is_file():
            with Image.open(reference) as frame:
                self.assertIsNotNone(normalize_icon(crop_item_icon(frame)))

if __name__=='__main__':
    unittest.main()
