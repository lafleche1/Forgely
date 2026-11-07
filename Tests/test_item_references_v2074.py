import sys, unittest, json, tempfile
from pathlib import Path
from urllib.parse import urlparse,parse_qs
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Application'))
from forgely_item_references import fetch_page,download_references
from forgely_tools import natural_bounds
class TestPagination(unittest.TestCase):
 def test_query_requests_effects_and_page(self):
  seen=[]
  def fetch(url):
   seen.append(parse_qs(urlparse(url).query))
   return json.dumps({'items':[{'ankama_id':42,'name':'Anneau test','effects':[{'type':{'name':'Vitalité'},'int_minimum':301,'int_maximum':400}]}]}).encode()
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'bounds.csv'
   self.assertEqual(download_references(path,fetch=fetch),(1,1))
   self.assertEqual(natural_bounds('Anneau test',path)['Vitalité'],(301,400))
  self.assertEqual(seen[0]['fields[item]'],['effects'])
  self.assertEqual(seen[0]['page[number]'],['1'])
  self.assertEqual(seen[0]['page[size]'],['100'])
 def test_second_page(self):
  urls=[]
  fetch_page(100,fetch=lambda url:(urls.append(url) or b'{"items":[]}'))
  self.assertEqual(parse_qs(urlparse(urls[0]).query)['page[number]'],['2'])
if __name__=='__main__':unittest.main()
