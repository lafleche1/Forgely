"""Regression tests for item OCR from the CURRENT workshop item row."""
import unittest
from PIL import Image
from forgely_item_vision import (crop_item_header, parse_item_header,
                                 recognize_item_header, identify_known)
from forgely_jet import parse_jet
from forgely_atelier import parse_reliquat
from forgely_copilote import player_signal
from types import SimpleNamespace


class ItemHeader2031Tests(unittest.TestCase):
    def test_crop_targets_first_history_row_not_character_header(self):
        image = Image.new('RGB', (1920, 1080))
        crop = crop_item_header(image)
        self.assertEqual(crop.size, (192, 32))

    def test_decorative_icon_glyph_is_removed(self):
        self.assertEqual(parse_item_header('t ANNEAU DU CYCLOÏDE'), 'ANNEAU DU CYCLOÏDE')
        self.assertEqual(parse_item_header('% ANNEAU DU CYCLOIDE'), 'ANNEAU DU CYCLOIDE')
        self.assertEqual(parse_item_header('GELANO'), 'GELANO')

    def test_history_or_unrelated_labels_are_not_equipment(self):
        for value in ('reliquat : 0', 'Échec', 'Joaillomager',
                      '300 Vitalité', 'rune PA', 'ANNEAU DU CYCLOIDE\nGELANO'):
            with self.subTest(value=value):
                self.assertIsNone(parse_item_header(value))

    def test_unknown_requires_two_agreeing_ocr_views(self):
        image = Image.new('RGB', (1920, 1080))
        readings = iter(('t ANNEAU DU CYCLOÏDE', '% ANNEAU DU CYCLOIDE'))
        known, candidate, _ = recognize_item_header(image, lambda _: next(readings), [])
        self.assertIsNone(known)
        self.assertEqual(candidate, 'ANNEAU DU CYCLOÏDE')

    def test_unknown_with_conflicting_ocr_is_rejected(self):
        image = Image.new('RGB', (1920, 1080))
        readings = iter(('ANNEAU DU CYCLOÏDE', 'ANNEAU DU CYCLOPS'))
        known, candidate, _ = recognize_item_header(image, lambda _: next(readings), [])
        self.assertIsNone(known)
        self.assertIsNone(candidate)

    def test_registered_equipment_keeps_canonical_name(self):
        image = Image.new('RGB', (1920, 1080))
        known, candidate, _ = recognize_item_header(
            image, lambda _: '% ANNEAU DU CYCLOIDE', [(7, 'Anneau du Cycloïde')])
        self.assertEqual(known, 'Anneau du Cycloïde')
        self.assertIsNone(candidate)

    def test_confirmed_jet_without_goal_is_not_lecture_en_attente(self):
        signal = player_signal(SimpleNamespace(rune=None, summary='Aucun objectif'),
                               {'Vitalité': 300}, {}, 0.0, True, False)
        self.assertEqual(signal.title, 'Jet lu · cible à définir')
        self.assertFalse(signal.stop)

    def test_user_supplied_jet_and_reliquat(self):
        self.assertEqual(parse_jet('Min Max Effets / Carac. M\n251 300 @ 300 Vitalité'),
                         {'Vitalité': 300})
        self.assertEqual(parse_reliquat('SS\nreliquat : 0'), 0.0)


if __name__ == '__main__':
    unittest.main()
