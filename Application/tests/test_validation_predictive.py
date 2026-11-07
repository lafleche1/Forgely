import csv,tempfile,unittest
from pathlib import Path
from forgely_probabilites_conditionnelles import FIELDS
from forgely_validation_predictive import validate_temporal
class PredictiveValidationTests(unittest.TestCase):
    def test_chronological_split_and_no_simulations(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'data.csv'
            with path.open('w',newline='',encoding='utf8') as f:
                w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader()
                for i in range(100):
                    w.writerow(dict(date_utc=f'2026-01-{i//24+1:02d}T{i%24:02d}:00:00',equipement='Anneau',rune='Ra Vi',resultat='SC' if i%2 else 'EC',source='manual',jet_avant='Vi:100',puits_avant=15,type_fm='fm_classique',poids_rune=10))
                w.writerow(dict(date_utc='2026-05-01T00:00:00',equipement='Anneau',rune='Ra Vi',resultat='SC',source='simulation',jet_avant='Vi:100',puits_avant=15,type_fm='fm_classique',poids_rune=10))
            report=validate_temporal(path,minimum=50)
            self.assertEqual(report['entrainement'],80)
            self.assertEqual(report['test_couvert'],20)
            self.assertEqual(report['rejets']['source_non_verifiee'],1)
            self.assertTrue(0<=report['brier_multiclasse']<=2)
    def test_no_data_no_probability(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'data.csv'
            with path.open('w',newline='',encoding='utf8') as f:
                w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader()
            report=validate_temporal(path)
            self.assertIsNone(report['brier_multiclasse'])
            self.assertFalse(report['validation_suffisante'])
    def test_reject_invalid_config(self):
        with self.assertRaises(ValueError):validate_temporal('missing.csv',train_fraction=1)
if __name__=='__main__':unittest.main()
