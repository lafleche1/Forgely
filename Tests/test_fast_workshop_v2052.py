import sys, unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'Application'))
import forgely_atelier as a

class WorkshopFastPath(unittest.TestCase):
    def setUp(self):
        self.im=Image.new('RGB',(1200,700),'black')
        self.cache={}
        self.calls=[]
        def ocr(im):
            self.calls.append(im.size)
            return 'Joaillomage'
        self.ocr=ocr

    def test_reuses_confirmed_title_but_still_reads_zones(self):
        with patch.object(a,'workshop_visual_fallback',return_value=True):
            first=a.read_atelier(self.im,self.ocr,title_cache=self.cache)
            count=len(self.calls)
            second=a.read_atelier(self.im,self.ocr,title_cache=self.cache)
        self.assertTrue(first.active and second.active)
        self.assertEqual(len(self.calls)-count,4)
        self.assertEqual(first.title,second.title)

    def test_disappearing_workshop_invalidates_cache(self):
        with patch.object(a,'workshop_visual_fallback',return_value=False):
            a.read_atelier(self.im,self.ocr,title_cache=self.cache)
            with patch.object(a,'is_workshop_title',return_value=False):
                result=a.read_atelier(self.im,lambda _: '',title_cache=self.cache)
        self.assertFalse(result.active)
        self.assertFalse(self.cache)

    def test_periodic_title_recheck(self):
        with patch.object(a,'workshop_visual_fallback',return_value=True):
            a.read_atelier(self.im,self.ocr,title_cache=self.cache)
            self.cache['checked_at']-=21
            self.calls.clear()
            a.read_atelier(self.im,self.ocr,title_cache=self.cache)
        self.assertEqual(len(self.calls),4)  # visual anchors confirm without title OCR

if __name__=='__main__':unittest.main()
