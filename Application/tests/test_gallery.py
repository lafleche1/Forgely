import tempfile,unittest,json
from pathlib import Path
from forgely_gallery import verify_goal,save_success,list_successes,export_gallery_json
class GalleryTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.db=Path(self.tmp.name)/'test.sqlite'
  self.plan={'item':'Anneau Padgref','stats':{'Vitalité':{'target':300},'Force':{'target':60}}}
 def tearDown(self):self.tmp.cleanup()
 def test_no_unverified(self):
  ok,_=verify_goal(self.plan,'Anneau Padgref',{'Vitalité':300,'Force':60},0,False,True)
  self.assertFalse(ok)
 def test_missing_stat(self):
  ok,_=verify_goal(self.plan,'Anneau Padgref',{'Vitalité':300},0,True,True)
  self.assertFalse(ok)
 def test_target_not_met(self):
  ok,_=verify_goal(self.plan,'Anneau Padgref',{'Vitalité':299,'Force':60},0,True,True)
  self.assertFalse(ok)
 def test_wrong_item(self):
  ok,_=verify_goal(self.plan,'Gelano',{'Vitalité':300,'Force':60},0,True,True)
  self.assertFalse(ok)
 def test_save_unique_export(self):
  d={'Vitalité':305,'Force':61}
  a=save_success(self.plan,'Anneau Padgref',d,0,True,True,self.db)
  b=save_success(self.plan,'Anneau Padgref',d,0,True,True,self.db)
  self.assertEqual(a,b);self.assertEqual(len(list_successes(self.db)),1)
  out=Path(self.tmp.name)/'gallery.json';self.assertEqual(export_gallery_json(out,self.db),1)
  self.assertEqual(json.loads(out.read_text(encoding='utf8'))['reussites'][0]['item'],'Anneau Padgref')
if __name__=='__main__':unittest.main()
