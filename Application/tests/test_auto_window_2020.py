import unittest
from types import SimpleNamespace
from unittest.mock import patch
from forgely_windows import auto_game_window

class AutoWindowTests(unittest.TestCase):
    def test_automatic_single(self):
        w=SimpleNamespace(_hWnd=12,title='Perso - Pandawa - 3.7.13.17 - Release',width=1100,height=700,isMinimized=False)
        self.assertIs(auto_game_window([w],None,None),w)
    def test_last_window_when_overlay_foreground(self):
        a=SimpleNamespace(_hWnd=12,title='Perso - Pandawa - 3.7.13.17 - Release',width=1100,height=700,isMinimized=False)
        b=SimpleNamespace(_hWnd=13,title='Perso2 - Iop - 3.7.13.17 - Release',width=1100,height=700,isMinimized=False)
        self.assertIs(auto_game_window([a,b],999,13),b)
    def test_ambiguous_never_guesses(self):
        a=SimpleNamespace(_hWnd=12,title='Perso - Pandawa - 3.7.13.17 - Release',width=1100,height=700,isMinimized=False)
        b=SimpleNamespace(_hWnd=13,title='Perso2 - Iop - 3.7.13.17 - Release',width=1100,height=700,isMinimized=False)
        self.assertIsNone(auto_game_window([a,b],999,None))
