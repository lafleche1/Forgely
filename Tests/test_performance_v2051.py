import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Application'))
from forgely_performance import PerformanceTracker
from forgely_zone_cache import ZoneCache
from PIL import Image

class PerformanceTests(unittest.TestCase):
    def test_bounded_samples(self):
        p=PerformanceTracker(capacity=3)
        for x in (1,2,3,4):p.record('ocr',x*1_000_000)
        self.assertEqual(p.snapshot()['ocr']['count'],3)
        self.assertEqual(p.snapshot()['ocr']['max'],4)
    def test_cache_change_and_refresh(self):
        c=ZoneCache(refresh_seconds=100)
        a=Image.new('RGB',(10,10),'white')
        self.assertTrue(c.should_read('history',a))
        self.assertEqual(c.read('history',a,lambda im:'one'),'one')
        self.assertFalse(c.should_read('history',a))
        b=a.copy();b.putpixel((0,0),(0,0,0))
        self.assertTrue(c.should_read('history',b))
        self.assertEqual(c.read('history',b,lambda im:'two'),'two')
        self.assertEqual(c.get('history'),'two')
        c.clear()
        self.assertTrue(c.should_read('history',b))
    def test_cache_reuses_ocr(self):
        c=ZoneCache()
        im=Image.new('RGB',(10,10))
        called=[]
        def read(im):called.append(1);return 'hello'
        self.assertEqual(c.read('effects',im,read),'hello')
        self.assertEqual(c.read('effects',im,read),'hello')
        self.assertEqual(len(called),1)

if __name__=='__main__':unittest.main()
