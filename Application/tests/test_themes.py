import json
import tempfile
import unittest
from pathlib import Path
from forgely_themes import THEMES, DEFAULT, load_theme, save_theme

class ThemeTests(unittest.TestCase):
    def test_only_obsidian_is_available(self):
        self.assertEqual(list(THEMES), ['Obsidienne'])
        self.assertEqual(DEFAULT, 'Obsidienne')
    def test_palettes_complete(self):
        for theme in THEMES.values():
            self.assertTrue(all(theme[k].startswith('#') and len(theme[k]) == 7 for k in ('BG','PANEL','PANEL2','ACCENT','GOLD','FG','MUTED','GREEN','RED','HOVER','BUTTON_HOVER','BUTTON_FG')))
    def test_persist(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'config'/'appearance.json'
            self.assertEqual(load_theme(path), DEFAULT)
            save_theme('Obsidienne', path)
            self.assertEqual(load_theme(path), 'Obsidienne')
    def test_removed_themes_migrate(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'appearance.json'
            for old in ('Atelier Émeraude', 'DOFUS classique', 'Minimal épuré', 'Sombre immersif', 'Fantaisie turquoise'):
                path.write_text(json.dumps({'theme':old,'design_version':22}), encoding='utf8')
                self.assertEqual(load_theme(path), 'Obsidienne')
                with self.assertRaises(ValueError):
                    save_theme(old, path)
    def test_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                save_theme('inconnu', Path(d)/'prefs.json')
