"""Reproduce actual diagnostic text and the expensive incomplete-jet recovery path."""
import unittest
from unittest.mock import patch
from PIL import Image,ImageDraw
import forgely_jet as jet

class DiagnosticTests(unittest.TestCase):
    def setUp(self):jet._LIVE_RECOVERY_CACHE.clear()

    def test_singular_damage_from_player_diagnostic_is_not_lost(self):
        text='7 10 @ 1 Dommage Feu\n7 10 & 5 Dommages Air\n43 Force'
        self.assertEqual(jet.parse_jet(text),{'Dommages Feu':1,'Dommages Air':5,'Force':43})
        self.assertEqual(jet.parse_jet('-1 Dommage Feu'),{'Dommages Feu':-1})

    def test_recovery_bounds_ocr_per_frame_and_eventually_reaches_later_strips(self):
        image=Image.new('RGB',(160,100),'#291f40')
        outputs=['']*9+['1 Dommage Feu']
        with patch('pytesseract.image_to_string',side_effect=outputs) as ocr:
            result={}
            for _ in range(4):
                before=ocr.call_count
                result,detail=jet.recover_missing_effects_live(image,{'Force':43})
                self.assertLessEqual(ocr.call_count-before,3)
            self.assertEqual(result,{'Dommages Feu':1})
            self.assertEqual(ocr.call_count,10)

    def test_current_pixel_change_discards_incomplete_recovery_progress(self):
        image=Image.new('RGB',(160,100),'#291f40')
        with patch('pytesseract.image_to_string',return_value='') as ocr:
            jet.recover_missing_effects_live(image,{'Force':43})
            first=ocr.call_count
            image.putpixel((80,40),(30,20,60))
            jet.recover_missing_effects_live(image,{'Force':43})
            self.assertLessEqual(ocr.call_count-first,3)

    def test_already_read_highlight_does_not_trigger_strip_sweep(self):
        image=Image.new('RGB',(300,300),'#291f40')
        draw=ImageDraw.Draw(image)
        for y in (100,119):draw.line((72,y,284,y),fill='white',width=2)
        with patch('pytesseract.image_to_string',return_value='43 Force') as ocr:
            found,detail=jet.recover_missing_effects_live(image,{'Force':43})
        self.assertEqual(found,{})
        self.assertEqual(detail['status'],'ligne_encadree_deja_lue')
        self.assertEqual(ocr.call_count,1)

    def test_atelier_surfaces_pending_recovery_and_phase_timings(self):
        from forgely_atelier import read_atelier
        image=Image.new('RGB',(1648,928),'#291f40')
        with patch('forgely_atelier.workshop_visual_fallback',return_value=True), \
             patch.object(jet,'read_effects_ocr',return_value='290 Vitalité\n2 Tacle'), \
             patch.object(jet,'recover_missing_effects_live',return_value=({}, {'status':'recuperation_en_cours'})):
            result=read_atelier(image,lambda patch:'reliquat : 47',title_cache={})
        self.assertTrue(result.recovery_pending)
        self.assertTrue({'titre_atelier','historique','effets','recuperation_lignes','runes','reliquat'}<=result.timings.keys())
