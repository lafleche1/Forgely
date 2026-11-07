import unittest
from types import SimpleNamespace
from unittest.mock import patch
from forgely_windows import is_game_window, auto_game_window

class ProcessWindowTests(unittest.TestCase):
    def window(self, title, handle=10):
        return SimpleNamespace(title=title, _hWnd=handle, width=1600, height=900, isMinimized=False)

    @patch('forgely_windows.process_executable', return_value='dofus.exe')
    def test_character_name_independent(self, _):
        w=self.window('NimporteQuelNom - Pandawa')
        self.assertTrue(is_game_window(w))
        self.assertIs(auto_game_window([w]), w)

    @patch('forgely_windows.process_executable', return_value='chrome.exe')
    def test_reject_other_process_even_if_title_looks_like_game(self, _):
        self.assertFalse(is_game_window(self.window('Chrome - Browser')))
        self.assertTrue(is_game_window(self.window('Agglou - Pandawa - 3.7.13.17 - Release')))

    @patch('forgely_windows.process_executable', return_value='')
    def test_fallback_when_windows_blocks_process_read(self, _):
        self.assertTrue(is_game_window(self.window('Agglou - Pandawa - 3.7.13.17 - Release')))

if __name__ == '__main__': unittest.main()
