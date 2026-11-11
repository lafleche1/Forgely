import tempfile, unittest
from pathlib import Path
from forgely_plan import save_plan,load_plan,next_action
class TestPlan(unittest.TestCase):
    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'plan.json'
            plan=save_plan('Mon anneau',{'Vitalité':(100,150)},p)
            self.assertEqual(load_plan(p),plan)
            self.assertIn('Profil naturel',next_action(plan,pool=0)[0])
    def test_unknown_current(self):
        with tempfile.TemporaryDirectory() as d:
            plan=save_plan('Mon anneau',{'Force':(None,45)},Path(d)/'plan.json')
            self.assertEqual(next_action(plan)[0],'Jet à lire')
    def test_no_target(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): save_plan('Mon anneau',{},Path(d)/'plan.json')
if __name__=='__main__':unittest.main()
