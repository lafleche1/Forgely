import unittest
from forgely_rune_icons import rune_icon_path

class RuneIconTests(unittest.TestCase):
    def test_real_ra_vi(self):
        self.assertEqual(rune_icon_path('Ra Vi ×1').name, 'rune_officielle_1554_78054.png')
        self.assertTrue(rune_icon_path('Ra Vi ×1').is_file())
    def test_unknown_is_not_guessed(self):
        self.assertIsNone(rune_icon_path('Rune inventée'))
    def test_stop_has_no_fake_icon(self):
        self.assertIsNone(rune_icon_path('STOP'))

if __name__ == '__main__':
    unittest.main()
