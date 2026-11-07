import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from forgely_events import AutoEventDetector
from forgely_windows import looks_like_dofus, select_window
from forgely_data import connect, insert_observation, stats

class TestWindows(unittest.TestCase):
    def w(self, title, hwnd=1):
        return SimpleNamespace(title=title,width=900,height=700,isMinimized=False,_hWnd=hwnd)

    def test_dofus_character_title(self):
        self.assertTrue(looks_like_dofus('Agglou - Pandawa - 3.7.13.17 - Release'))
        self.assertTrue(looks_like_dofus('DOFUS'))
        self.assertFalse(looks_like_dofus('Forgely • Tableau de bord'))

    def test_one_window(self):
        w=self.w('Agglou - Pandawa - 3.7.13.17 - Release')
        self.assertIs(select_window([w]),w)

    def test_multiple_requires_active(self):
        a=self.w('A - Pandawa - 3.7.13.17 - Release',1)
        b=self.w('B - Iop - 3.7.13.17 - Release',2)
        self.assertIsNone(select_window([a,b]))
        self.assertIs(select_window([a,b],2),b)

class TestEvents(unittest.TestCase):
    def test_only_fresh_complete_action(self):
        d=AutoEventDetector(['Vi','Pa Vi','Ra Vi'])
        txt='Rune Pa Vi\nSuccès critique'
        self.assertIsNone(d.observe(txt))  # Stale at launch
        d.observe('Atelier');d.observe('Atelier')
        e=d.observe(txt)
        self.assertIsNotNone(e)
        self.assertEqual((e.rune,e.outcome),('Pa Vi','SC'))
        self.assertIsNone(d.observe(txt))
        self.assertIsNone(d.observe(txt))
        self.assertEqual(d.saved,1)
        d.observe('');d.observe('')
        self.assertEqual(d.observe(txt).outcome,'SC')
        self.assertEqual(d.saved,2)

    def test_ambiguous_rune_is_discarded(self):
        d=AutoEventDetector(['Vi','Pa Vi'])
        d.observe('');d.observe('')
        self.assertIsNone(d.observe('Succès neutre'))
        self.assertEqual(d.uncertain,1)

class TestDb(unittest.TestCase):
    def test_migrate_existing_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'test.sqlite'
            import sqlite3
            db=sqlite3.connect(path)
            db.execute("CREATE TABLE observations (id INTEGER PRIMARY KEY AUTOINCREMENT, captured_at TEXT NOT NULL, item TEXT NOT NULL, rune TEXT NOT NULL, outcome TEXT NOT NULL CHECK(outcome IN ('SC','SN','EC')),source TEXT NOT NULL CHECK(source IN ('ocr_confirmed','manual')),evidence TEXT NOT NULL DEFAULT '')")
            db.execute("INSERT INTO observations(captured_at,item,rune,outcome,source,evidence) VALUES ('date','Ancien','Vi','SC','manual','')")
            db.commit();db.close()
            connect(path).close()
            insert_observation('Objet non identifié','Vi','EC','ocr_auto',db_file=path)
            n,c=stats(db_file=path)
            self.assertEqual(n,2)
            self.assertEqual((c['SC'],c['EC']),(1,1))

if __name__=='__main__': unittest.main()
