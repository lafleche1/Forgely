import tempfile
from pathlib import Path
import unittest
from forgely_context import normalize_snapshot,snapshot_diff,save_transition,context_rates

class ContextTests(unittest.TestCase):
 def test_incomplete_readings_never_masquerade_as_full_jet(self):
  self.assertIsNone(normalize_snapshot({'Force':10},None))
  self.assertIsNone(snapshot_diff({'jet':{'Force':10},'pool':0},{'jet':{'Force':11,'Sagesse':5},'pool':0}))
 def test_store_and_context_query(self):
  with tempfile.TemporaryDirectory() as d:
   db=Path(d)/'test.sqlite'
   pre={'jet':{'Force':40},'pool':10}
   post={'jet':{'Force':43},'pool':10}
   for _ in range(30):save_transition('Anneau','Pa Fo','SC',pre,post,db)
   x=context_rates('Anneau','Pa Fo','Force',40,10,db)
   self.assertEqual(x['n'],30);self.assertTrue(x['usable']);self.assertEqual(x['percentages']['SC'],100)
   self.assertFalse(context_rates('Anneau','Pa Fo','Force',100,10,db)['usable'])
 def test_reject_same_snapshot(self):
  with tempfile.TemporaryDirectory() as d:
   pre={'jet':{'Force':40},'pool':0}
   with self.assertRaises(ValueError): save_transition('Anneau','Fo','EC',pre,pre,Path(d)/'test.sqlite')
if __name__=='__main__': unittest.main()
