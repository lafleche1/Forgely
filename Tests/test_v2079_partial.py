import unittest
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Application'))
from forgely_workshop_readings import WorkshopReadings
from forgely_atelier import parse_reliquat

class TestPartial(unittest.TestCase):
    def test_partial_jet_no_pool_never_authorizes_snapshot(self):
        r=WorkshopReadings()
        for _ in range(3):self.assertFalse(r.observe({'Force':40,'Tacle':0},None))
        self.assertEqual(r.partial_jet,{'Force':40,'Tacle':0})
        self.assertIsNone(r.snapshot())
        self.assertIsNone(r.partial_pool)
    def test_pool_separate(self):
        r=WorkshopReadings()
        for _ in range(3):self.assertFalse(r.observe({},0.3))
        self.assertEqual(r.partial_pool,0.3)
        self.assertIsNone(r.snapshot())
    def test_atomic_stable(self):
        r=WorkshopReadings()
        for _ in range(3):r.observe({'Force':40},0.3)
        self.assertEqual(r.snapshot(),({'Force':40},0.3))
    def test_changed_jet_invalidates_atomic(self):
        r=WorkshopReadings()
        for _ in range(3):r.observe({'Force':40},0.3)
        self.assertFalse(r.observe({'Force':39},0.3))
        self.assertIsNone(r.snapshot())
    def test_effects_pool(self):
        self.assertEqual(parse_reliquat('reliquat : 0,3 & 2s dd'),0.3)
        self.assertIsNone(parse_reliquat('reliauat : 02'))
if __name__=='__main__':unittest.main()
