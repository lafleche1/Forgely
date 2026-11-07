"""Regression for DOFUS icon glyphs in OCR and accurate waiting state."""
import unittest
from types import SimpleNamespace
from PIL import Image
from forgely_item_vision import parse_item_header, recognize_item_header
from forgely import Forgely


class ItemVision2034Tests(unittest.TestCase):
    def test_enhanced_ocr_numeric_icon_prefix(self):
        self.assertEqual(parse_item_header('73 ANNEAU DU CYCLOIDE'), 'ANNEAU DU CYCLOIDE')
        self.assertEqual(parse_item_header('319 ANNEAU DU CYCLOÏDE'), 'ANNEAU DU CYCLOÏDE')

    def test_two_views_agree_despite_icon_artifact(self):
        readings=iter(('> ANNEAU DU CYCLOIDE', '73 ANNEAU DU CYCLOIDE'))
        known, candidate, raw=recognize_item_header(Image.new('RGB',(1920,1080)),
            lambda _: next(readings), [])
        self.assertIsNone(known)
        self.assertEqual(candidate,'ANNEAU DU CYCLOIDE')
        self.assertIn('73 ANNEAU',raw)

    def test_do_not_treat_effects_as_equipment(self):
        for value in ('300 VITALITE', '15 RÉSISTANCE', '73 ÉCHEC', '73 RELIQUAT'):
            with self.subTest(value=value):
                self.assertIsNone(parse_item_header(value))

    def test_overlay_uses_current_slot_not_history_attempts(self):
        obj=SimpleNamespace(running=True, workshop_active=True,
            active_equipment_verified=False, last_item_candidate='',
            history_has_attempts=True,
            current_slot_tracker=SimpleNamespace(count=0), provisional_slot_id=None)
        self.assertEqual(Forgely.waiting_for_item_label(obj), 'Lecture de l’objet')
        obj.current_slot_tracker.count=3
        obj.provisional_slot_id=7
        self.assertEqual(Forgely.waiting_for_item_label(obj), 'Objet détecté · identification du nom en cours')
        obj.last_item_candidate='GELANO'
        self.assertEqual(Forgely.waiting_for_item_label(obj), 'Objet à confirmer')

if __name__=='__main__':
    unittest.main()
