import unittest
from types import SimpleNamespace
from forgely_windows import looks_like_dofus, select_window, window_by_handle

class WindowSelectionTests(unittest.TestCase):
    def test_character_title(self):
        self.assertTrue(looks_like_dofus('Agglou - Pandawa - 3.7.13.17 - Release'))
    def test_manual_handle(self):
        windows=[SimpleNamespace(_hWnd=23,title='Agglou - Pandawa - 3.7.13.17 - Release')]
        self.assertIs(window_by_handle(23,windows),windows[0])
        self.assertIsNone(window_by_handle(42,windows))
    def test_automatic_does_not_select_unrelated(self):
        w=SimpleNamespace(_hWnd=10,title='Chrome',width=1200,height=800,isMinimized=False)
        self.assertIsNone(select_window([w],10))
if __name__=='__main__': unittest.main()
