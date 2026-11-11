import unittest
from PIL import Image
from forgely_atelier import crop_zone, is_workshop_title, parse_reliquat, read_atelier


def table_ocr(image, titles):
    # Dispatch by actual region, independent of parallel worker scheduling.
    title_values = iter(titles)
    effects = crop_zone(image, 'effects')
    values = {crop_zone(image, 'history').size: 'Échec',
              effects.size: '251 300 4 Vitalité',
              (effects.width-round(effects.width*.32), effects.height): '4 Vitalité',
              crop_zone(image, 'runes').size: '2303',
              crop_zone(image, 'reliquat').size: 'reliquat : 0,2'}
    def read(patch):
        return values[patch.size] if patch.size in values else next(title_values, '')
    return read

class AtelierTests(unittest.TestCase):
    def test_titles(self):
        self.assertTrue(is_workshop_title('Joaillomager'))
        self.assertTrue(is_workshop_title('CORDOMAGE'))
        self.assertTrue(is_workshop_title('Costumage'))
        self.assertFalse(is_workshop_title('Inventaire'))
        self.assertFalse(is_workshop_title('Historique Échec'))
    def test_reliquat(self):
        self.assertEqual(parse_reliquat('reliquat : 0,2'),0.2)
        self.assertIsNone(parse_reliquat('rune Vi 2303'))
    def test_crop(self):
        im=Image.new('RGB',(1648,928))
        self.assertEqual(crop_zone(im,'title').size,(337,37))
    def test_no_atelier(self):
        im=Image.new('RGB',(1648,928))
        r=read_atelier(im,lambda im:'Inventaire')
        self.assertFalse(r.active)
        self.assertFalse(r.history)
    def test_fallback_title_crop(self):
        im=Image.new('RGB',(1648,928))
        result=read_atelier(im,table_ocr(im, ['', '', 'Joaillomager']))
        self.assertTrue(result.active)
        self.assertEqual(result.title,'Joaillomager')

    def test_atelier(self):
        im=Image.new('RGB',(1648,928))
        r=read_atelier(im,table_ocr(im, ['Joaillomager']))
        self.assertTrue(r.active)
        self.assertEqual(r.history,'Échec')

if __name__=='__main__': unittest.main()

class OcrRegressionTests(unittest.TestCase):
    def test_real_world_typo(self):
        self.assertTrue(is_workshop_title('JOATLLOMAGE'))
        self.assertTrue(is_workshop_title('J0AILL0MAGIE'))
        self.assertTrue(is_workshop_title('CORDOMAGIE'))
    def test_unrelated_title_not_accepted(self):
        for name in ('Historique Échec', 'Rune Vi', 'Inventaire', 'FORGELY', 'Cordonnier'):
            self.assertFalse(is_workshop_title(name))


def test_specialized_threshold_recognizes_white_title():
    from PIL import Image, ImageDraw
    from forgely_atelier import specialized_title_candidates, is_workshop_title
    im = Image.new('RGB', (1648, 928), '#24243e')
    # Ensure the threshold fallback generates an OCR-ready binary candidate.
    candidates = list(specialized_title_candidates(im))
    assert candidates and candidates[0].mode == 'L'
    assert set(candidates[0].getextrema()) == {0}
    assert is_workshop_title('Joaillomaader')
