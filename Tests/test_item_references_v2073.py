import sys, unittest, tempfile, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"Application"))
from forgely_item_references import download_references, parse_effect
from forgely_tools import natural_bounds
class TestAPIShapes(unittest.TestCase):
 def test_dofusdude_int_fields(self):
  self.assertEqual(parse_effect({"type":{"name":"Vitalité"},"int_minimum":301,"int_maximum":400}),("Vitalité",301,400))
 def test_full_import_int_fields(self):
  item={"ankama_id":99,"name":"Anneau test","effects":[{"type":{"name":"Vitalité"},"int_minimum":301,"int_maximum":400}]}
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/"bounds.csv"
   self.assertEqual(download_references(path,fetch=lambda url:json.dumps({"items":[item]}).encode()),(1,1))
   self.assertEqual(natural_bounds("Anneau test",path)["Vitalité"],(301,400))
 def test_failure_keeps_base(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/"bounds.csv";path.write_text("original")
   with self.assertRaisesRegex(ValueError,"aucun effet compatible"):
    download_references(path,fetch=lambda url:b'{"items":[{"ankama_id":1,"name":"X","effects":[]}]}')
   self.assertEqual(path.read_text(),"original")
if __name__=="__main__":unittest.main()
