import json, os, tempfile, unittest, uuid
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app
class TestAPI(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.original=app.DB; app.DB=Path(self.tmp.name)/'test.sqlite3'
    def tearDown(self): app.DB=self.original; self.tmp.cleanup()
    def test_valid_event(self):
        x=json.loads((Path(__file__).parents[1]/'example_event.json').read_text()); self.assertEqual(app.validate(x),x)
    def test_reject_unverified(self):
        x=json.loads((Path(__file__).parents[1]/'example_event.json').read_text()); x['verification']='ocr_auto'
        with self.assertRaises(ValueError): app.validate(x)
    def test_reject_extra_personal_data(self):
        x=json.loads((Path(__file__).parents[1]/'example_event.json').read_text()); x['account_name']='test'
        with self.assertRaises(ValueError): app.validate(x)
    def test_schema_creation(self):
        with app.connect() as c:
            self.assertEqual(c.execute("SELECT name FROM sqlite_master WHERE name='attempts'").fetchone()[0],'attempts')
if __name__=='__main__': unittest.main()
