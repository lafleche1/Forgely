import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from laboratoire_walkyrip import audit

class WalkyripTests(unittest.TestCase):
 def test_catalogue_no_invented_observations(self):
  r=audit(Path(__file__).resolve().parents[1]/"walkyrip_sources.csv")
  self.assertEqual(r["sources_reperees"],7)
  self.assertEqual(r["tentatives_verifiees"],0)
  self.assertFalse(r["probas_exploitables"])
 def test_duplicate_sources_rejected(self):
  with TemporaryDirectory() as d:
   p=Path(d)/"c.csv";p.write_text("id\na\na\n",encoding="utf-8")
   with self.assertRaises(ValueError):audit(p)
