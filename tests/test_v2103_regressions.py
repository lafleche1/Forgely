"""Regression tests derived from field diagnostics; run once the Application sources are imported."""
import unittest
from forgely_atelier import choose_reliquat, parse_reliquat
from forgely_history_delta import HistoryDeltaMonitor

class ReliquatRegression(unittest.TestCase):
    def test_lost_decimal_separator(self):
        self.assertEqual(choose_reliquat('reliquat : 4,5', 'reliauat : 45'), 4.5)
        self.assertEqual(choose_reliquat('reliquat : 3,1', 'reliauat : 31'), 3.1)
    def test_conflicting_decimals(self):
        self.assertIsNone(choose_reliquat('reliquat : 0,1', 'reliquat : 0.17'))
    def test_negative_not_accepted(self):
        self.assertIsNone(parse_reliquat('reliquat : -0,2'))

class HistoryRegression(unittest.TestCase):
    def test_repeated_changes_preserved(self):
        monitor = HistoryDeltaMonitor()
        old = '+1 Force\n-1 Intelligence\n-1 Force'
        new = old + '\n-1 Intelligence\n-1 Intelligence'
        monitor.observe(old)
        self.assertEqual(monitor.observe(new)['status'], 'extension_a_confirmer')
        self.assertEqual(monitor.observe(new)['new_changes'], [('Intelligence', -1), ('Intelligence', -1)])
    def test_ambiguous_change_not_certified(self):
        monitor = HistoryDeltaMonitor()
        monitor.observe('+1 Force\n-1 Agilité')
        result = monitor.observe('-2 Tacle\n-1 Intelligence')
        self.assertFalse(result['certified'])
        self.assertEqual(result['new_changes'], [])

if __name__ == '__main__':
    unittest.main()

