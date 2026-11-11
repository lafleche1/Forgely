import sys,unittest
from unittest.mock import Mock, patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Application'))
from PIL import Image,ImageDraw
from forgely_equipment_session import ManualEquipmentSession
from forgely_equipment_catalog import EquipmentCatalog


def icon(color):
 im=Image.new('RGB',(32,32),'#38394e');ImageDraw.Draw(im).ellipse((4,4,27,27),fill=color);return im

class ManualSessionTests(unittest.TestCase):
 def setUp(self):
  self.item=EquipmentCatalog().search('Anneau','cycloide')[0]
 def test_selected_name_binds_without_name_ocr(self):
  s=ManualEquipmentSession(self.item)
  for i in range(3):self.assertEqual(s.observe(icon('#df2835'),()),i==2)
  self.assertTrue(s.bound)
  self.assertEqual(s.equipment,self.item)
 def test_changed_slot_requires_explicit_reselection(self):
  s=ManualEquipmentSession(self.item)
  for i in range(3):s.observe(icon('#df2835'),())
  self.assertFalse(s.observe(icon('#22d050'),()))
  self.assertFalse(s.invalidated)
  for i in range(2):s.observe(icon('#22d050'),())
  self.assertTrue(s.invalidated)
  for i in range(4):self.assertFalse(s.observe(icon('#22d050'),()))
 def test_absent_slot_pauses_and_same_item_resumes(self):
  s=ManualEquipmentSession(self.item)
  for i in range(3):s.observe(icon('#df2835'),())
  for i in range(3):s.observe(None,())
  self.assertFalse(s.invalidated)
  self.assertFalse(s.bound)
  for i in range(3):ready=s.observe(icon('#df2835'),())
  self.assertTrue(ready)
 def test_workshop_absent_before_first_capture_keeps_selection(self):
  s=ManualEquipmentSession(self.item);s.workshop_lost()
  self.assertFalse(s.invalidated)
 def test_page_switch_preserves_selection_and_rechecks_on_return(self):
  s=ManualEquipmentSession(self.item)
  for i in range(3):s.observe(icon('#df2835'),())
  s.workshop_lost()
  self.assertFalse(s.invalidated)
  self.assertFalse(s.bound)
  for i in range(3):ready=s.observe(icon('#df2835'),())
  self.assertTrue(ready)

 def test_one_transient_icon_does_not_invalidate_selected_item(self):
  s=ManualEquipmentSession(self.item)
  for i in range(3):s.observe(icon('#df2835'),())
  self.assertFalse(s.observe(icon('#22d050'),()))
  self.assertFalse(s.invalidated)
  for i in range(3):ready=s.observe(icon('#df2835'),())
  self.assertTrue(ready)

 def test_different_item_after_page_switch_still_requires_reselection(self):
  s=ManualEquipmentSession(self.item)
  for i in range(3):s.observe(icon('#df2835'),())
  s.workshop_lost()
  for i in range(3):s.observe(icon('#22d050'),())
  self.assertTrue(s.invalidated)

 def test_ui_manual_selection_never_enrolls_or_checks_old_icon_reference(self):
  from forgely import Forgely
  from forgely_pipeline import VerifiedItemContext
  app=Mock()
  app.manual_equipment=ManualEquipmentSession(self.item)
  app.pending_transition=None
  app.workshop_readings.snapshot.return_value=({'Force':40},2.7)
  mailbox=object()
  with patch('forgely.remember_current_item',side_effect=AssertionError('old reference')), \
       patch('forgely.match_current_item',side_effect=AssertionError('old reference')):
   for frame in range(1,4):
    Forgely.process_manual_equipment(app,icon('#df2835'),(),(mailbox,1,'DOFUS'),frame)
  self.assertTrue(app.active_equipment_verified)
  self.assertEqual(app.live_pool,2.7)
  self.assertIsInstance(app._verified_item_context,VerifiedItemContext)
  self.assertEqual(app._verified_item_context.item,self.item.name)

class SharedIconBoundsTests(unittest.TestCase):
 def test_contradicting_natural_range_never_binds_selected_identity(self):
  item=EquipmentCatalog().search('Anneau','cycloide')[0]
  s=ManualEquipmentSession(item)
  for _ in range(3):
   self.assertFalse(s.observe(icon('#df2835'),(('vitalite',1,10),)))
  self.assertTrue(s.invalidated)
