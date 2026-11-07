import tempfile,unittest
from pathlib import Path
from forgely_items import register_item,find_item,item_list,add_alias,remember_candidate,pending_items,item_history,key_for
from forgely_item_vision import identify_known,possible_unknown
from forgely_data import insert_observation, stats

class EquipmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=Path(self.tmp.name)/'test.db'
    def tearDown(self):self.tmp.cleanup()
    def test_accent_case_dedup(self):
        a=register_item('Gélano',self.db)
        b=register_item(' gelano ',self.db)
        self.assertEqual(a[0],b[0]);self.assertEqual(len(item_list(self.db)),1)
    def test_alias_unifies(self):
        item=register_item('Gelano',self.db)
        add_alias('Anneau Gelano',item[0],self.db)
        self.assertEqual(find_item('ANNEAU GELANO',self.db)[0],item[0])
    def test_duplicate_and_ambiguity(self):
        register_item('Gelano',self.db)
        register_item('Anneau du Chêne',self.db)
        self.assertEqual(identify_known('Objet: Gelano',item_list(self.db)),'Gelano')
        self.assertIsNone(identify_known('Gelano / Anneau du Chêne',item_list(self.db)))
    def test_local_table(self):
        register_item('Gelano',self.db)
        insert_observation('Gelano','Vi','EC','manual',db_file=self.db)
        insert_observation('Autre','Vi','SC','manual',db_file=self.db)
        self.assertEqual(len(item_history('Gelano',db_file=self.db)),1)
        self.assertEqual(stats(item='Gelano',db_file=self.db)[0],1)
    def test_candidate_not_new_item(self):
        remember_candidate('Possible anneau',self.db)
        self.assertEqual(len(item_list(self.db)),0)
        self.assertEqual(len(pending_items(self.db)),1)
    def test_non_item_lines_rejected(self):
        self.assertEqual(possible_unknown('Joaillomagie\nVitalité 4\nRel iquat'),[])

if __name__=='__main__': unittest.main()

class EquipmentOCRRegressionTests(unittest.TestCase):
    def test_single_typo_of_registered_name(self):
        self.assertEqual(identify_known('Anneau du Chene', [(1,'Anneau du Chêne')]),'Anneau du Chêne')
        self.assertEqual(identify_known('Anneau du Chene\n', [(1,'Anneau du Chêne')]),'Anneau du Chêne')
    def test_unknown_not_registered(self):
        self.assertIsNone(identify_known('Anneau Padgref', [(1,'Gelano')]))
    def test_ambiguous_ocr_never_selects(self):
        self.assertIsNone(identify_known('Anneau de Chene', [(1,'Anneau des Chênes'),(2,'Anneau du Chêne')]))
