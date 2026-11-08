import sys,unittest,tempfile,csv
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Application'))
from forgely_equipment_catalog import EquipmentCatalog, category_for_type, target_values

class EquipmentCatalogTests(unittest.TestCase):
 def test_types_not_names_determine_category(self):
  self.assertEqual(category_for_type(16),'Coiffe')
  self.assertEqual(category_for_type(17),'Cape')
  self.assertEqual(category_for_type(9),'Anneau')
  self.assertEqual(category_for_type(1),'Amulette')
  self.assertEqual(category_for_type(10),'Ceintures')
  self.assertEqual(category_for_type(11),'Bottes')
  for t in (2,3,4,5,6,7,8,19,22): self.assertEqual(category_for_type(t),'Arme')
  self.assertIsNone(category_for_type(82))
 def test_real_catalog_search_and_identity(self):
  c=EquipmentCatalog()
  ring=next(x for x in c.search('Anneau','cycloide') if x.name=='Anneau du Cycloïde')
  self.assertGreater(ring.icon_id,0)
  self.assertEqual(c.get(ring.item_id),ring)
  self.assertTrue(all(x.category=='Anneau' for x in c.search('Anneau','')))
  self.assertEqual(c.search('Coiffe','cycloide'),[])
 def test_targets_keep_current_unknown_and_validate(self):
  self.assertEqual(target_values({'Force':'50','Vitalité':'','PA':'1'}),{'Force':(None,50),'PA':(None,1)})
  for values in ({},{'Force':'1.5'},{'Force':'20001'},{'Introuvable':'1'}):
   with self.assertRaises(ValueError):target_values(values)
 def test_icon_resolution_uses_icon_id(self):
  c=EquipmentCatalog()
  ring=c.search('Anneau','cycloide')[0]
  with tempfile.TemporaryDirectory() as d:
   path=Path(d)/f'{ring.icon_id}.png';path.write_bytes(b'test')
   self.assertEqual(c.icon_path(ring,Path(d)),path)

if __name__=='__main__':unittest.main()

class NaturalTargetTests(unittest.TestCase):
 def test_selected_item_has_its_own_natural_characteristics(self):
  from forgely_equipment_catalog import bundled_bounds
  self.assertEqual(bundled_bounds('Gelano').get('PA'),(1,1))
  cyclone=bundled_bounds('Anneau du Cycloïde')
  self.assertGreaterEqual(len(cyclone),5)
  self.assertNotEqual(cyclone,bundled_bounds('Gelano'))

class IdentityVariantTests(unittest.TestCase):
 def test_same_name_variants_keep_distinct_identity_and_bounds(self):
  from forgely_equipment_catalog import equipment_bounds
  c=EquipmentCatalog();low=c.get(20210);high=c.get(20353)
  self.assertEqual(low.name,high.name)
  self.assertNotEqual(low.identity_name,high.identity_name)
  self.assertNotEqual(equipment_bounds(low).get('Vitalité'),equipment_bounds(high).get('Vitalité'))
