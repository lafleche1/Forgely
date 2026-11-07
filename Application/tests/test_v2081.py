import unittest
from forgely_history_summary import summarize_history
from forgely_jet import parse_jet, read_first_effect_row

class V2081(unittest.TestCase):
    def test_history(self):
        result = summarize_history('ANNEAU DU CYCLOÏDE\n© -1 Vitalité\n@ -1 Intelligence\n+ reliquat')
        self.assertEqual(result['recent_changes'], [('Vitalité', -1), ('Intelligence', -1)])
        self.assertFalse(result['rune_attempt_confirmed'])
    def test_no_fake_history(self):
        self.assertEqual(summarize_history('341 Vitalité\n39 Intelligence')['recent_changes'], [])
    def test_first_row_ocr(self):
        from pathlib import Path
        from PIL import Image
        image = Path('/mnt/data/work2081/effects_crop.png')
        if image.exists():
            self.assertEqual(read_first_effect_row(Image.open(image)), '341 Vitalité')

if __name__ == '__main__': unittest.main()
