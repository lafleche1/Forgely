from forgely_sqlite import database_connection
import json,sqlite3,tempfile,time,unittest
from pathlib import Path
from forgely_labo_live import LiveLaboratory,compute_snapshot

class TestLiveLabo(unittest.TestCase):
    def test_empty(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(compute_snapshot(Path(d)/'missing.db')['observations'],0)
    def test_update_and_filter(self):
        with tempfile.TemporaryDirectory() as d:
            db=Path(d)/'test.db'
            with database_connection(db) as conn:
                conn.execute('CREATE TABLE fusion_contexts(item TEXT,rune TEXT,outcome TEXT,before_json TEXT,source TEXT)')
                before=json.dumps({'jet':{'Vitalité':100},'pool':5})
                for i in range(30):conn.execute('INSERT INTO fusion_contexts VALUES(?,?,?,?,?)',('Anneau','Ra Vi','SC' if i<12 else 'EC',before,'local_screen'))
                conn.execute('INSERT INTO fusion_contexts VALUES(?,?,?,?,?)',('Anneau','Ra Vi','SC',before,'simulation'))
            labo=LiveLaboratory(db,interval=.05,minimum=30);labo.start()
            try:
                for _ in range(40):
                    result=labo.estimate('Anneau','Ra Vi',{'Vitalité':100},5)
                    if result:break
                    time.sleep(.02)
                self.assertTrue(result['usable']);self.assertEqual(result['n'],30)
                self.assertEqual(result['percentages']['SC'],40.)
                self.assertIsNone(labo.estimate('Anneau','Ra Vi',{'Vitalité':100,'Force':1},5))
            finally:labo.stop()
