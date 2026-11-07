import unittest
from types import SimpleNamespace
from unittest.mock import patch
from forgely_windows import is_game_window, auto_game_window

class TitleFallbackRegressionTests(unittest.TestCase):
    def make(self, title, handle=42):
        return SimpleNamespace(title=title, _hWnd=handle, width=1648, height=928, isMinimized=False)

    @patch('forgely_windows.process_executable', return_value='unknownlauncher.exe')
    def test_character_title_even_if_exe_mismatch(self, _):
        w=self.make('Agglou - Pandawa - 3.7.13.17 - Release')
        self.assertTrue(is_game_window(w))
        self.assertIs(auto_game_window([w]), w)

    @patch('forgely_windows.process_executable', return_value='python.exe')
    def test_reject_forgely_and_unrelated_window(self, _):
        self.assertFalse(is_game_window(self.make('Forgely - 3.7.13.17 - Release')))
        self.assertFalse(is_game_window(self.make('Navigateur - documentation')))

if __name__ == '__main__': unittest.main()
