import csv,tempfile,unittest
from pathlib import Path
from forgely_probabilites_conditionnelles import audit_conditional,estimate,FIELDS
class ConditionalTests(unittest.TestCase):
    def test_separation_and_threshold(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'obs.csv'
            with path.open('w',newline='',encoding='utf8') as f:
                writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader()
                for i in range(60):
                    writer.writerow(dict(date_utc=str(i),equipement='Anneau',rune='Ra Vi',resultat='SC' if i<30 else 'EC',source='video_verified',jet_avant='Vi:100',puits_avant=15,type_fm='fm_classique',poids_rune=10))
                writer.writerow(dict(date_utc='x',equipement='Anneau',rune='Ra Vi',resultat='SC',source='simulation',jet_avant='Vi:100',puits_avant=15,type_fm='fm_classique',poids_rune=10))
                writer.writerow(dict(date_utc='y',equipement='Anneau',rune='Ra Vi',resultat='SC',source='manual',jet_avant='Vi:100',puits_avant=0,type_fm='fm_classique',poids_rune=10))
            report=audit_conditional(path,minimum=50)
            self.assertEqual(report['rejets']['non_verifie'],1)
            self.assertEqual(len(report['groupes']),2)
            group=estimate(report,equipement='Anneau',rune='Ra Vi',type_fm='fm_classique',puits=15,poids=10)
            self.assertEqual(group['n'],60)
            self.assertEqual(group['frequences']['SC'],.5)
            self.assertIsNone(estimate(report,equipement='Anneau',rune='Ra Vi',type_fm='fm_classique',puits=0,poids=10))
            self.assertIsNone(estimate(report,equipement='Anneau',rune='Ra Vi',type_fm='exo',puits=15,poids=10))
if __name__=='__main__':unittest.main()
