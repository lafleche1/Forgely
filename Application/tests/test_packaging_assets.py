from pathlib import Path
import re
import unittest


class PackagingAssetsTests(unittest.TestCase):
    def test_both_builders_include_ocr_and_fm_reference_assets(self):
        root = Path(__file__).resolve().parents[1]
        required = {'assets', 'catalogue_dofus3', 'catalogue_objets_noms_fr.csv',
                    'catalogue_objets_icones.csv', 'references'}
        for filename in ('fabriquer_exe.bat', 'fabriquer_installateur_windows.bat'):
            with self.subTest(builder=filename):
                source = (root / filename).read_text(encoding='utf-8')
                packaged = {m.split(';', 1)[0] for m in re.findall(r'--add-data "([^"]+)"', source)}
                self.assertTrue(required.issubset(packaged), required-packaged)
                for asset in required:
                    self.assertTrue((root / asset).exists(), asset)
                self.assertIn('preparer_reference_dofocus.py', source)
