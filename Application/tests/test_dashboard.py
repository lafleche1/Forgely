import unittest

from forgely_dashboard import stat_rows


class DashboardRowsTests(unittest.TestCase):
    def test_empty_reading_does_not_invent_stats(self):
        self.assertEqual(stat_rows({}, {}, verified=False), [])

    def test_target_is_not_an_observation(self):
        rows = stat_rows({}, {'Force': 40}, verified=False)
        self.assertEqual(rows, [('Force', '—', '40', 'À lire', 'unknown')])

    def test_provisional_values_never_claim_target_achieved(self):
        self.assertEqual(stat_rows({'Force': 40}, {'Force': 40}, verified=False),
                         [('Force', '40', '40', 'Stabilisation automatique', 'pending')])

    def test_confirmed_values_compare_to_target(self):
        rows = stat_rows({'Force': 40, 'Agilité': 29}, {'Force': 40, 'Agilité': 40}, verified=True)
        self.assertIn(('Force', '40', '40', 'Atteint', 'success'), rows)
        self.assertIn(('Agilité', '29', '40', 'À compléter', 'pending'), rows)

    def test_zero_and_negative_values_remain_visible(self):
        rows = stat_rows({'Tacle': 0, 'Force': -3}, {}, verified=True)
        self.assertIn(('Tacle', '0', '—', 'Lu', 'normal'), rows)
        self.assertIn(('Force', '-3', '—', 'Lu', 'normal'), rows)


if __name__ == '__main__':
    unittest.main()
