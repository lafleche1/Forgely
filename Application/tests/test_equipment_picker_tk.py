"""Opt-in native UI tests for catalogue → targets → session."""
import os
import unittest
from unittest.mock import patch
from forgely_equipment_catalog import EquipmentCatalog

@unittest.skipUnless(os.environ.get('FORGELY_GUI_TESTS')=='1','requires a desktop')
class EquipmentPickerTkTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from forgely import Forgely
  with patch('forgely.load_plan',return_value=None),patch('forgely.load_theme',return_value='Obsidienne'):
   cls.app=Forgely()
  cls.app.auto_floating.set(False)
 @classmethod
 def tearDownClass(cls):cls.app.close()
 def setUp(self):
  from forgely_equipment_picker import EquipmentPicker
  from forgely_themes import THEMES
  self.committed=[]
  self.picker=EquipmentPicker(self.app,THEMES[self.app.theme_name],lambda *args:self.committed.append(args))
  self.app.update()
 def tearDown(self):
  if self.picker.winfo_exists():self.picker.close()
 def test_category_item_then_targets(self):
  p=self.picker
  self.assertEqual(str(p.continue_button.cget('state')),'disabled')
  p.choose_category('Anneau');p.query.set('cycloide');p.search_changed()
  item=p.catalog.search('Anneau','cycloide')[0];p.choose(item)
  self.assertEqual(str(p.continue_button.cget('state')),'normal')
  self.assertIsNotNone(p.photo(item))
  p.show_goals();p.fill_maximum();p.commit(False)
  self.assertEqual(self.committed[0][0],item)
  self.assertGreaterEqual(len(self.committed[0][1]),5)
  self.assertTrue(all(pair[0] is None for pair in self.committed[0][1].values()))
 def test_cancel_never_changes_the_active_item_or_plan(self):
  old=self.app.item.get();plan=self.app.plan
  p=self.picker;p.choose_category('Anneau');p.choose(p.catalog.search('Anneau','Gelano')[0]);p.show_goals();p.close()
  self.assertEqual(self.app.item.get(),old);self.assertIs(self.app.plan,plan);self.assertEqual(self.committed,[])
 def test_category_buttons_and_footer_fit_small_window(self):
  p=self.picker;p.geometry('800x600');p.choose_category('Anneau');self.app.update()
  for widget in [*p.category_buttons.values(),p.footer,p.continue_button,p.search]:
   with self.subTest(widget=str(widget)):
    self.assertTrue(widget.winfo_ismapped())
    self.assertLessEqual(widget.winfo_rootx()+widget.winfo_width(),p.winfo_rootx()+p.winfo_width())
    self.assertLessEqual(widget.winfo_rooty()+widget.winfo_height(),p.winfo_rooty()+p.winfo_height())

 def test_observation_requires_selected_item_and_targets(self):
  app=self.app;app.manual_equipment=None;app.running=False;app.plan=None;app.equipment_mode.set('manual')
  with patch.object(app,'open_equipment_quick') as choose:
   app.toggle_observer()
  choose.assert_called_once();self.assertFalse(app.running)

 def test_committed_choice_preserves_targets_and_skips_auto_icon_enrollment(self):
  import threading
  app=self.app
  item=EquipmentCatalog().search('Anneau','Gelano')[0]
  app.running=False
  app.commit_equipment_selection(item,{'PA':(None,1)})
  self.assertEqual(app.plan['item_id'],item.item_id)
  self.assertEqual(app.plan['stats']['PA'],{'current':None,'target':1})
  self.assertFalse(app.active_equipment_verified)
  self.assertEqual(app.item.get(),'Gelano')
  from PIL import Image,ImageDraw
  icon=Image.new('RGB',(32,32),'#38394e');ImageDraw.Draw(icon).ellipse((4,4,27,27),fill='#df2835')
  app.confirmation_requested=threading.Event()
  with patch('forgely.remember_current_item') as remember,patch('forgely.register_item_with_icon') as enroll:
   for _ in range(3):
    app.messages.put(('item_visual',(None,None,'',icon,None,None,(),[],None,None)))
    app.process_messages()
  self.assertTrue(app.active_equipment_verified)
  remember.assert_not_called();enroll.assert_not_called()
