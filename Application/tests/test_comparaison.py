import unittest
from comparer_probabilites import wilson, report

class ComparisonTest(unittest.TestCase):
    def test_empty_range(self):
        self.assertEqual(wilson(0,0),(0.,1.))
    def test_interval(self):
        lo,hi=wilson(5,10)
        self.assertLess(lo,.5)
        self.assertGreater(hi,.5)
    def test_no_fabricated_data(self):
        self.assertIn('uniquement de votre CSV',report({}))
