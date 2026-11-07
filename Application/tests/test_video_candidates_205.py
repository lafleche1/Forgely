import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from laboratoire_videos import detect_candidates

class CandidateTests(unittest.TestCase):
    def test_invalid_parameters(self):
        with self.assertRaises(ValueError):detect_candidates('none.mp4','out.csv',sample_step=0)
        with self.assertRaises(ValueError):detect_candidates('none.mp4','out.csv',threshold=2)
    def test_missing_file(self):
        try:import cv2
        except ImportError:self.skipTest('opencv absent')
        with TemporaryDirectory() as d:
            with self.assertRaises(FileNotFoundError):detect_candidates(Path(d)/'missing.mp4',Path(d)/'out.csv')
