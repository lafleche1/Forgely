import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
from forgely_vision import RuneLibrary, icon_patch


def sample(color, shape='diamond'):
    im=Image.new('RGB',(36,36),(21,20,31)); dr=ImageDraw.Draw(im)
    if shape=='diamond':dr.polygon([(18,2),(32,18),(18,34),(4,18)],fill=color)
    else:dr.ellipse((3,3,33,33),fill=color)
    return im

class VisionTests(unittest.TestCase):
    def test_known_and_unrecognized(self):
        with tempfile.TemporaryDirectory() as temp:
            lib=RuneLibrary(Path(temp),('Vi','Pa Vi'))
            self.assertIsNone(lib.predict(sample((140,20,210))).rune)
            lib.add('Vi',sample((140,20,210)))
            lib.add('Pa Vi',sample((20,230,40),'round'))
            self.assertEqual(lib.predict(sample((140,20,210))).rune,'Vi')
            self.assertEqual(lib.predict(sample((20,230,40),'round')).rune,'Pa Vi')
            self.assertIsNone(lib.predict(sample((220,220,220))).rune)
            self.assertEqual(set(RuneLibrary(Path(temp),('Vi','Pa Vi')).labels()),{'Vi','Pa Vi'})

    def test_crop_and_invalid(self):
        img=Image.new('RGB',(200,100),'black')
        self.assertEqual(icon_patch(img,15,15).size,(36,36))
        with self.assertRaises(ValueError):icon_patch(img,-1,20)

    def test_reject_similar_runes(self):
        with tempfile.TemporaryDirectory() as temp:
            lib=RuneLibrary(Path(temp),('Vi','Pa Vi'))
            lib.add('Vi',sample((140,20,210)))
            lib.add('Pa Vi',sample((141,20,210)))
            self.assertIsNone(lib.predict(sample((140,20,210))).rune)

if __name__=='__main__':unittest.main()
