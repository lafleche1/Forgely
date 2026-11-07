import csv
import tempfile
import unittest
from pathlib import Path
from forgely_profile_guidance import compare, profiles

class TestProfileGuidance(unittest.TestCase):
    def test_missing_and_outside_are_not_filled(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'ref.csv'
            with path.open('w',encoding='utf8',newline='') as f:
                w=csv.writer(f);w.writerow(['equipement','statistique','min','max'])
                w.writerow(['Anneau du Cycloïde','Vitalité',201,300])
                w.writerow(['Anneau du Cycloïde','Tacle',4,6])
            actual={'Tacle':0,'PA':1}
            result=compare('ANNEAU DU CYCLOÏDE',actual,path)
            self.assertEqual(result['missing'],['Vitalité'])
            self.assertEqual(result['outside'],[('Tacle',0,4,6)])
            self.assertEqual(result['extra'],['PA'])
            self.assertEqual(actual,{'Tacle':0,'PA':1})
            self.assertEqual(len(profiles(path)),1)
    def test_missing_reference(self):
        self.assertFalse(compare('inconnu',{},Path('/nonexistent/forgely.csv'))['available'])
