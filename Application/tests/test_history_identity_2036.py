"""Regression: name/logo comes from the current history block above rune results."""
import unittest
from pathlib import Path
from PIL import Image
from forgely_history_identity import first_history_item, resolve_history_identity, names_agree
from forgely_detection import HistoryTransitionTracker, explicit_outcome, new_row_shift


class HistoryIdentity2036Tests(unittest.TestCase):
    def test_real_ocr_header_with_delete_icon_artifact(self):
        result=first_history_item('2 ANNEAU DU CYCLOÏDE D\n=) -reliquat\nÉchec')
        self.assertEqual(result.name,'ANNEAU DU CYCLOÏDE')
        self.assertEqual(result.outcome,'echec')

    def test_current_name_above_critical_success(self):
        text='ANNEAU DU CYCLOÏDE\nRéussite critique\nÉchec\nGELANO\nÉchec'
        result=first_history_item(text)
        self.assertEqual(result.name,'ANNEAU DU CYCLOÏDE')
        self.assertIn('reussite critique',result.outcome)

    def test_classic_success_and_failure_are_both_valid(self):
        for result in ('Réussite classique','Réussite critique','Échec'):
            with self.subTest(result=result):
                self.assertEqual(first_history_item('GELANO\n'+result+'\nAutre objet\nÉchec').name,'GELANO')
        self.assertEqual(explicit_outcome('Réussite classique'),'SN')
        self.assertEqual(explicit_outcome('Réussite critique'),'SC')
        self.assertEqual(explicit_outcome('Échec'),'EC')

    def test_old_item_result_not_attributed_to_current(self):
        text='ANNEAU DU CYCLOÏDE\n- reliquat\n15 Vitalité\n- reliquat\nGELANO\nÉchec'
        result=first_history_item(text)
        self.assertEqual(result.name,'ANNEAU DU CYCLOÏDE')
        self.assertIsNone(result.outcome)

    def test_no_guess_when_first_heading_unreadable(self):
        text='- reliquat\n15 Vitalité\nGELANO\nÉchec'
        self.assertIsNone(first_history_item(text).name)

    def test_icon_prefix_ocr_does_not_veto_independent_name_reading(self):
        image=Image.new('RGB',(1920,1080))
        for noisy in ('Bar ANNEAU DU CYCLOÏDE D',
                      'Ban) ANNEAU DU CYCLOÏDE D',
                      '2 ANNEAU DU CYCLOÏDE D'):
            with self.subTest(noisy=noisy):
                readings=iter(('t ANNEAU DU CYCLOÏDE', 'ANNEAU DU CYCLOÏDE'))
                known,candidate,raw,evidence=resolve_history_identity(
                    image, noisy+'\n=) -reliquat', lambda _: next(readings), [])
                self.assertEqual(candidate, 'ANNEAU DU CYCLOÏDE')
                self.assertNotEqual(evidence.source, 'conflit en-tête / historique')

    def test_reference_frames_confirm_name_and_logo_together(self):
        from forgely_item_icons import ItemVisualTracker, crop_item_icon, normalize_icon
        from runeforge_observer import extract_text
        from forgely_atelier import crop_zone
        tracker=ItemVisualTracker()
        for index, clock in enumerate(('183624','185548','190438','190438'),1):
            path=Path(f"/mnt/data/Capture d'écran 2026-11-06 {clock}.png")
            if not path.exists():
                self.skipTest('reference screenshot not available')
            with Image.open(path) as image:
                history=extract_text(crop_zone(image,'history'))
                known,candidate,_,_=resolve_history_identity(
                    image,history,extract_text,[])
                icon=normalize_icon(crop_item_icon(image))
                self.assertEqual(tracker.observe(known or candidate,icon),index)

    def test_other_item_cannot_be_disguised_as_icon_artifact(self):
        image=Image.new('RGB',(1920,1080))
        for noisy in ('GELANO ANNEAU DU CYCLOÏDE',
                      'ANNEAU DU CYCLOÏDE GELANO',
                      'GELANO'):
            with self.subTest(noisy=noisy):
                readings=iter(('ANNEAU DU CYCLOÏDE', 'ANNEAU DU CYCLOÏDE'))
                known,candidate,_,evidence=resolve_history_identity(
                    image, noisy+'\nÉchec', lambda _: next(readings), [])
                self.assertIsNone(known)
                self.assertIsNone(candidate)
                self.assertEqual(evidence.source, 'conflit en-tête / historique')

    def test_real_screens_with_noisy_history_icon(self):
        from runeforge_observer import extract_text
        from forgely_atelier import crop_zone
        for clock in ('183624','185548','190438'):
            path=Path(f"/mnt/data/Capture d'écran 2026-11-06 {clock}.png")
            if not path.exists():
                self.skipTest('reference screenshot not available')
            with self.subTest(clock=clock), Image.open(path) as image:
                history=extract_text(crop_zone(image,'history'))
                known,candidate,_,evidence=resolve_history_identity(
                    image,history,extract_text,[])
                self.assertEqual(candidate,'ANNEAU DU CYCLOÏDE')
                self.assertNotEqual(evidence.source,'conflit en-tête / historique')

    def test_two_distinct_names_cannot_agree(self):
        self.assertTrue(names_agree('Anneau du Cycloïde','ANNEAUDUCYCLOIDE'))
        self.assertFalse(names_agree('Anneau du Cycloïde','Gelano'))

    def test_history_fallback_when_header_ocr_is_blank(self):
        image=Image.new('RGB',(1920,1080))
        readings=iter(('', ''))
        known, candidate, raw, evidence=resolve_history_identity(image,
            'ANNEAU DU CYCLOÏDE\nÉchec\nGELANO\nÉchec',
            lambda _: next(readings), [])
        self.assertEqual(candidate,'ANNEAU DU CYCLOÏDE')
        self.assertIsNone(known)

    def test_history_fallback_does_not_take_previous_item(self):
        image=Image.new('RGB',(1920,1080))
        readings=iter(('', ''))
        known, candidate, *_=resolve_history_identity(image,
            '- reliquat\n15 Vitalité\nGELANO\nÉchec',
            lambda _: next(readings), [])
        self.assertEqual((known,candidate),(None,None))

    def test_conflicting_history_and_header_refused(self):
        image=Image.new('RGB',(1920,1080))
        readings=iter(('ANNEAU DU CYCLOÏDE','ANNEAU DU CYCLOÏDE'))
        known, candidate, *_=resolve_history_identity(image,
            'GELANO\nÉchec',lambda _: next(readings), [])
        self.assertEqual((known,candidate),(None,None))

    def test_insert_below_stationary_heading(self):
        before=('anneau du cycloide','echec','15 vitalite','echec')
        after=('anneau du cycloide','reussite critique','echec','15 vitalite','echec')
        self.assertEqual(new_row_shift(before,after),1)
        t=HistoryTransitionTracker(('Vi',))
        t.observe('\n'.join(before),rune_text='Rune Vi',now=1)
        t.observe('\n'.join(before),now=2)
        self.assertIsNone(t.observe('\n'.join(after),now=3))
        event=t.observe('\n'.join(after),now=4)
        self.assertEqual((event.rune,event.outcome),('Vi','SC'))
        self.assertIsNone(t.observe('\n'.join(after),now=5))

    def test_static_existing_result_not_new_event(self):
        t=HistoryTransitionTracker(('Vi',))
        history='ANNEAU DU CYCLOÏDE\nÉchec\nÉchec\nGELANO\nÉchec'
        for n in range(6):
            self.assertIsNone(t.observe(history,rune_text='Rune Vi',now=n))
        self.assertEqual(t.saved,0)

    def test_reference_screen_header_still_readable(self):
        path=Path("/mnt/data/Capture d'écran 2026-11-06 190438.png")
        if not path.is_file():
            self.skipTest('reference screenshot not available')
        from runeforge_observer import extract_text
        with Image.open(path) as image:
            known,candidate,_,_=resolve_history_identity(image,'',extract_text,[])
        self.assertEqual(candidate,'ANNEAU DU CYCLOÏDE')


if __name__=='__main__':unittest.main()
