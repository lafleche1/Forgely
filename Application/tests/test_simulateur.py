import unittest
from forgely_simulateur import simulate_target

class TestSimulateur(unittest.TestCase):
    def test_all_success(self):
        r=simulate_target('Vi',0,10,0,100,1,0,0,trials=100,max_attempts=5)
        self.assertEqual(r.completed,100)
        self.assertEqual(r.mean_attempts,2)
        self.assertFalse(hasattr(r,'mean_cost'))
        self.assertEqual(r.sc,200)
    def test_no_pool_failure(self):
        r=simulate_target('Vi',0,10,0,100,0,0,1,trials=100,max_attempts=5)
        self.assertEqual(r.completed,0)
        self.assertFalse(hasattr(r,'mean_cost'))
    def test_sn_uses_pool(self):
        r=simulate_target('Vi',0,10,2,100,0,1,0,trials=10)
        self.assertEqual(r.completed,10)
        self.assertEqual(r.mean_pool_left,0)
    def test_invalid_odds(self):
        with self.assertRaises(ValueError):simulate_target('Vi',0,10,0,1,.5,.5,.5)
    def test_unknown_rune(self):
        with self.assertRaises(ValueError):simulate_target('inconnue',0,10,0,1,1,0,0)
    def test_seed_reproducible(self):
        args=('Vi',0,30,20,100,.3,.3,.4)
        self.assertEqual(simulate_target(*args),simulate_target(*args))
    def test_does_not_write_observations(self):
        r=simulate_target('Vi',0,10,0,100,1,0,0)
        self.assertTrue(r.estimated)
