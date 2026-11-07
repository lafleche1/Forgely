import csv
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path
from forgely_tools import (import_bounds_csv,natural_bounds,save_settings,read_settings,
  export_observations_csv,backup_local,illustrative_scenario,advisory_status,session_cost)
from forgely_data import insert_observation,connect

class ToolsTest(unittest.TestCase):
 def test_settings(self):
  with tempfile.TemporaryDirectory() as tmp:
   f=Path(tmp)/'s.json';save_settings({'strategy':'Économique','budget_kamas':500,'prices':{'Vi':10}},f)
   self.assertEqual(read_settings(f)['prices']['Vi'],10)
 def test_bounds(self):
  with tempfile.TemporaryDirectory() as tmp:
   s=Path(tmp)/'in.csv';dest=Path(tmp)/'jets.csv'
   s.write_text('equipement,statistique,min,max\nGelano,PA,1,1\n',encoding='utf8')
   self.assertEqual(import_bounds_csv(s,dest),1)
   self.assertEqual(natural_bounds('GÉLANO',dest)['PA'],(1,1))
 def test_export_and_backup(self):
  with tempfile.TemporaryDirectory() as tmp:
   db=Path(tmp)/'test.sqlite';connect(db).close()
   insert_observation('Objet','Vi','EC','manual',db_file=db)
   csvpath=Path(tmp)/'obs.csv';self.assertEqual(export_observations_csv(csvpath,db),1)
   self.assertEqual(session_cost('Objet',{'prices':{'Vi':20}},db)['known_cost'],20)
   z=Path(tmp)/'backup.zip';backup_local(z,db,Path(tmp)/'none',Path(tmp)/'none')
   with zipfile.ZipFile(z) as archive:self.assertIn('observations_locales.sqlite3',archive.namelist())
 def test_scenario_separate(self):
  result=illustrative_scenario('Vi',500,10,.2,.3,.5)
  self.assertEqual(sum(result['counts'].values()),500)
  self.assertFalse(result['is_real_observation'])
 def test_stop_unknown(self):
  self.assertIsNone(advisory_status({},None,None,False)['goal_probability'])
 def test_stop_complete(self):
  s=advisory_status({'stats':{'PA':{'target':1}}},{'PA':1},0,True,{'PA':(1,1)})
  self.assertEqual(s['goal_probability'],1.0)

if __name__=='__main__':unittest.main()
