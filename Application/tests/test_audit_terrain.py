import csv
import tempfile
import unittest
from pathlib import Path
from forgely_data import insert_observation, insert_unassigned
from forgely_audit_terrain import audit, export

class AuditTerrainTests(unittest.TestCase):
    def test_audit_and_export_are_read_only(self):
        with tempfile.TemporaryDirectory() as temp:
            db=Path(temp)/'db.sqlite3'
            insert_observation('Test','Vi','SC','ocr_auto',db_file=db)
            insert_observation('Test','Vi','EC','manual',db_file=db)
            insert_unassigned('SN',db_file=db)
            report=audit(db)
            self.assertEqual(report['total'],2)
            self.assertEqual(report['auto_to_review'],1)
            self.assertEqual(report['unassigned'],1)
            out=Path(temp)/'export'
            export(db,out)
            with (out/'tentatives_a_verifier.csv').open(encoding='utf-8-sig',newline='') as f:
                rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),2)
            self.assertEqual(rows[0]['verification_humaine'],'')
            self.assertEqual(audit(db)['total'],2)
    def test_missing_db_does_not_create_one(self):
        with tempfile.TemporaryDirectory() as temp:
            db=Path(temp)/'missing.sqlite3'
            with self.assertRaises(FileNotFoundError): audit(db)
            self.assertFalse(db.exists())
