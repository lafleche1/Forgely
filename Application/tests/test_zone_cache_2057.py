import unittest
from PIL import Image
from forgely_zone_cache import ZoneCache

class ZoneCacheTests(unittest.TestCase):
    def test_unchanged_pixels_reuse(self):
        cache = ZoneCache(60)
        calls=[]
        def read(image):
            calls.append(1)
            return str(len(calls))
        a=Image.new('RGB',(200,100),'black')
        self.assertEqual(cache.read('effects',a,read),'1')
        self.assertEqual(cache.read('effects',a.copy(),read),'1')
        self.assertEqual(len(calls),1)
        a.putpixel((100,50),(255,255,255))
        self.assertEqual(cache.read('effects',a,read),'2')
        self.assertEqual(cache.hits,1)
        self.assertEqual(cache.misses,2)

    def test_zone_isolation(self):
        cache=ZoneCache(60)
        im=Image.new('RGB',(2,2))
        self.assertEqual(cache.read('effects',im,lambda _: 'effects'),'effects')
        self.assertEqual(cache.read('history',im,lambda _: 'history'),'history')

    def test_expired_cache_forces_revalidation(self):
        cache=ZoneCache(0)
        im=Image.new('RGB',(2,2))
        self.assertEqual(cache.read('a',im,lambda _: 'old'),'old')
        self.assertEqual(cache.read('a',im,lambda _: 'new'),'new')

if __name__=='__main__':unittest.main()
