import tempfile
import unittest
from pathlib import Path
from forgely_themes import THEMES, DEFAULT, load_theme, save_theme

class ThemeTests(unittest.TestCase):
    def test_palettes_complete(self):
        self.assertEqual(len(THEMES),4)
        for theme in THEMES.values():
            self.assertTrue(all(theme[k].startswith('#') and len(theme[k])==7 for k in ('BG','PANEL','PANEL2','ACCENT','GOLD','FG','MUTED','GREEN','RED','HOVER','BUTTON_HOVER','BUTTON_FG')))
    def test_persist(self):
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'config'/'appearance.json'
            self.assertEqual(load_theme(file),DEFAULT)
            save_theme('Minimal épuré',file)
            self.assertEqual(load_theme(file),'Minimal épuré')
    def test_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):save_theme('inconnu',Path(d)/'prefs.json')
