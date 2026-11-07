import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Application'))
from forgely_atelier import parse_reliquat, choose_reliquat
from forgely_workshop_readings import WorkshopReadings
class PoolTest(unittest.TestCase):
 def test_negative_ocr(self):
  self.assertIsNone(parse_reliquat('reliquat -0.2.'))
 def test_prefer_effects(self):
  self.assertEqual(choose_reliquat('reliquat : 0,3 & 2s dd','reliquat -0.2.'),.3)
 def test_conflict(self):
  self.assertIsNone(choose_reliquat('reliquat : 0,3','reliquat : 0,2'))
 def test_stable(self):
  w=WorkshopReadings();
  for _ in range(3): w.observe({'Force':40},choose_reliquat('reliquat : 0,3','reliquat -0.2.'))
  self.assertEqual(w.partial_pool,.3)
if __name__=='__main__': unittest.main()
