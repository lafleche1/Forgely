import csv
import tempfile
import unittest
from pathlib import Path
from forgely_validation import validate_rows, wilson, export_report


class AuditTest(unittest.TestCase):
    def make_csv(self, rows):
        d = tempfile.TemporaryDirectory()
        path = Path(d.name) / 'obs.csv'
        with path.open('w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['date_utc', 'equipement', 'rune', 'resultat', 'source'])
            writer.writerows(rows)
        self.addCleanup(d.cleanup)
        return path

    def test_wilson(self):
        self.assertEqual(wilson(0, 0), None)
        self.assertEqual(wilson(0, 100)[0], 0)
        self.assertEqual(wilson(100, 100)[1], 1)
        self.assertLess(wilson(10, 20)[0], .5)

    def test_excludes_ocr_auto_and_duplicates(self):
        path = self.make_csv([
            ('1', 'Anneau', 'Vi', 'SC', 'manual'),
            ('1', 'Anneau', 'Vi', 'SC', 'manual'),
            ('2', 'Anneau', 'Vi', 'EC', 'ocr_auto'),
            ('3', 'Anneau', 'Vi', 'SN', 'video_verified'),
            ('4', 'Anneau', 'Vi', 'EC', 'simulation'),
        ])
        result = validate_rows(path, min_samples=2)
        self.assertEqual(result['lignes_acceptees'], 2)
        self.assertEqual(result['lignes_exclues']['source_non_verifiee'], 2)
        self.assertEqual(result['lignes_exclues']['doublon_exact'], 1)
        self.assertEqual(result['groupes'][0]['frequences']['SC'], .5)
        self.assertFalse(result['taux_dofus_certifies'])

    def test_small_samples_hidden(self):
        result = validate_rows(self.make_csv([('1', 'Anneau', 'Vi', 'SC', 'manual')]))
        self.assertIsNone(result['groupes'][0]['frequences'])

    def test_bad_schema(self):
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        path = Path(d.name) / 'bad.csv'; path.write_text('a,b\n1,2\n')
        with self.assertRaises(ValueError):
            validate_rows(path)

    def test_export(self):
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        path = Path(d.name) / 'audit.json'
        report = export_report(self.make_csv([('1', 'Anneau', 'Vi', 'SC', 'manual')]), path)
        self.assertTrue(path.exists())
        self.assertEqual(report['lignes_acceptees'], 1)


if __name__ == '__main__':
    unittest.main()
