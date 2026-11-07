import sys,unittest,tempfile,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Application'))
from forgely_item_references import extract_item,download_references
from forgely_tools import natural_bounds
class TestReferenceImport(unittest.TestCase):
 def test_extract(self):
  obj={'name':'Anneau test','effects':[{'type':{'name':'Vitalité'},'min':301,'max':400},{'type':{'name':'Force'},'min':31,'max':40}]}
  self.assertEqual(len(extract_item(obj)),2)
 def test_no_guess(self):
  self.assertEqual(extract_item({'name':'X','effects':[{'type':{'name':'Vitalité'},'min':301}]}),[])
 def test_import(self):
  obj={'ankama_id':1,'name':'Anneau test','effects':[{'type':{'name':'Vitalité'},'min':301,'max':400}]}
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'bounds.csv'
   count=download_references(path,fetch=lambda url:json.dumps({'items':[obj]}).encode())
   self.assertEqual(count,(1,1));self.assertEqual(natural_bounds('Anneau test',path)['Vitalité'],(301,400))
 def test_failure_keeps_previous(self):
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'bounds.csv';path.write_text('original')
   with self.assertRaises(ValueError):download_references(path,fetch=lambda url:b'{"items":[]}')
   self.assertEqual(path.read_text(),'original')
if __name__=='__main__':unittest.main()
