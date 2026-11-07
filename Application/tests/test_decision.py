import unittest
from forgely_decision import (advise, pool_transition, classify, extra_mass, candidates)

class TestDecision(unittest.TestCase):
    def test_pool_generation_and_consumption(self):
        self.assertEqual(pool_transition(0,10,30,'EC'),20)
        self.assertEqual(pool_transition(20,10,0,'EC'),10)
        self.assertEqual(pool_transition(10,10,0,'SC'),10)
    def test_pool_reject_invalid_sc(self):
        with self.assertRaises(ValueError):pool_transition(0,10,30,'SC')
    def test_types(self):
        maxes={'Force':60,'Vitalité':300}
        self.assertEqual(classify('Force',55,58,maxes),'fm_classique')
        self.assertEqual(classify('Force',60,63,maxes),'over')
        self.assertEqual(classify('PA',0,1,maxes),'exo')
        self.assertEqual(classify('PA',0,1,None),'inconnu')
    def test_cap(self):
        self.assertAlmostEqual(extra_mass({'Force':61,'PA':1},{'Force':60}),101)
        self.assertEqual(candidates({'PA':0,'Force':20},{'PA':1},{'Force':20},0)[0][1],'Ga Pa')
        self.assertEqual(candidates({'PA':0,'Force':20},{'PA':1},{'Force':20,'Vitalité':300},0)[0][1],'Ga Pa')
        self.assertEqual(candidates({'PA':0,'Force':20},{'PA':1},{'Force':20,'PM':1},0)[0][1],'Ga Pa')
        self.assertFalse(candidates({'PA':1,'PM':1},{'PM':2},{},0))
    def test_uncertain_never_advise(self):
        self.assertIsNone(advise({'Force':50},{'Force':60},pool=None).rune)
        self.assertIsNone(advise({'Force':50},{'Force':60},pool=0,after_fusion=True).rune)
        self.assertIsNone(advise({'Force':50},{'Vitalité':300},pool=0).rune)
    def test_exo_reference_separate(self):
        a=advise({'PA':0},{'PA':1},natural_max={'Force':100},pool=0)
        self.assertEqual(a.rune,'Ga Pa')
        self.assertEqual(a.estimates['benchmark']['SC'],1.)
        b=advise({'Force':50},{'Force':60},pool=10)
        self.assertIsNone(b.estimates['benchmark']['SC'])

if __name__=='__main__':unittest.main()
