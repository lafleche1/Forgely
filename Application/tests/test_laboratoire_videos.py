import csv,tempfile,unittest
from pathlib import Path
from laboratoire_videos import init_review,validate_review,export_review,FIELDS
class VideoLabTests(unittest.TestCase):
 def test_empty(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'review.csv';init_review(p)
   self.assertEqual(validate_review(p),([],[]))
   result=export_review(p,Path(d)/'out.csv')
   self.assertEqual(result['tentatives_verifiees'],0)
 def test_verified_only_and_duplicates(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'review.csv';init_review(p)
   row=dict.fromkeys(FIELDS,'')
   row.update(video_id='test',horodatage_video_s='30',date_utc='2026-01-01T00:00:00Z',equipement='Anneau',rune='Ra Vi',resultat='SC',jet_avant='Vi 100',puits_avant='0',type_fm='fm_classique',poids_rune='10',reviseur='Alice',statut='verifie')
   with p.open('a',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=FIELDS);w.writerow(row);w.writerow(row);w.writerow(dict(row,statut='a_revoir',horodatage_video_s='40'))
   accepted,errors=validate_review(p)
   self.assertEqual(len(accepted),1);self.assertEqual(len(errors),1)
   self.assertEqual(accepted[0]['source'],'video_verified')
   with self.assertRaises(ValueError):export_review(p,Path(d)/'out.csv')
 def test_no_fake_verification(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'review.csv';init_review(p)
   with p.open('a',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=FIELDS);w.writerow(dict.fromkeys(FIELDS,''))
   self.assertEqual(validate_review(p),([],[]))
if __name__=='__main__':unittest.main()
