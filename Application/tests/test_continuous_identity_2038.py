"""Regression: opening Forgely halfway through FM must not require a rune."""
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
from forgely_continuous_identity import (crop_current_item, current_icon,
    effect_signature, signatures_compatible, CurrentSlotTracker,
    remember_provisional, match_current_item, remember_current_item)
from forgely_item_icons import icon_distance
from forgely_items import register_item


def painted_icon(color):
    im=Image.new('RGB',(32,32),'#38394e')
    ImageDraw.Draw(im).ellipse((5,4,26,27),fill=color,outline='#f0d898',width=2)
    return im


class ContinuousIdentityTests(unittest.TestCase):
    def test_slot_visible_without_any_history(self):
        image=Image.new('RGB',(1648,928),'#38394e')
        box=(round(.393*1648),round(.195*928),round(.407*1648),round(.223*928))
        image.paste(painted_icon('#df2835').resize((box[2]-box[0],box[3]-box[1])),box)
        self.assertIsNotNone(current_icon(image))
        self.assertEqual(crop_current_item(image).size,(box[2]-box[0],box[3]-box[1]))

    def test_min_max_stable_despite_current_jet(self):
        a='251 300 ♥ 285 Vitalité\n31 40 36 Force\n7 10 8 Dommages Terre'
        b='251 300 ♥ 299 Vitalité\n31 40 35 Force\n7 10 10 Dommages Terre'
        self.assertEqual(effect_signature(a),effect_signature(b))
        self.assertGreaterEqual(len(effect_signature(a)),2)
        self.assertFalse(signatures_compatible(effect_signature(a),effect_signature('251 350 299 Vitalité')))

    def test_slot_change_invalidates_previous_identity(self):
        tracker=CurrentSlotTracker(frames=3)
        ring=painted_icon('#df2835')
        amulet=painted_icon('#22d050')
        for i in range(3):
            stable, changed=tracker.observe(ring)
        self.assertTrue(stable)
        stable, changed=tracker.observe(amulet)
        self.assertTrue(changed)
        self.assertFalse(stable)
        self.assertEqual(tracker.count,1)

    def test_unknown_stays_anonymous_until_named(self):
        with tempfile.TemporaryDirectory() as directory:
            db=Path(directory)/'test.db'
            icon=painted_icon('#df2835')
            sig=(('vitalite',251,300),)
            provisional=remember_provisional(icon,sig,db)
            self.assertEqual(provisional,remember_provisional(icon,sig,db))
            self.assertIsNone(match_current_item(icon,sig,db))
            register_item('Objet universel de test',db)
            remember_current_item('Objet universel de test',icon,sig,db)
            self.assertEqual(match_current_item(icon,sig,db),'Objet universel de test')
            self.assertIsNone(match_current_item(icon,(('vitalite',1,2),),db))

    def test_different_icons_do_not_share_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            db=Path(directory)/'test.db'
            ring=painted_icon('#df2835')
            amulet=painted_icon('#22d050')
            register_item('Objet A',db)
            remember_current_item('Objet A',ring,(),db)
            self.assertIsNone(match_current_item(amulet,(),db))


if __name__=='__main__':
    unittest.main()
