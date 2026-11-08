from forgely_sqlite import database_connection
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
from forgely_dofocus import catalogue


class DofocusStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source=Path(self.tmp.name)/'source.json'
        self.db=Path(self.tmp.name)/'reference.sqlite3'
        self.data=deepcopy(catalogue())
        self.source.write_text(json.dumps(self.data,ensure_ascii=False),encoding='utf-8')

    def build(self):
        from forgely_dofocus_store import build_database,ReferenceStore
        build_database(self.source,self.db)
        return ReferenceStore(self.db)

    def test_compiled_source_preserves_every_recorded_value(self):
        store=self.build()
        for sample in self.data['snapshots']:
            jet={r['stat']:r['value'] for r in sample['rows']}
            context=store.context(sample['item'],jet,sample['pool'])
            for row in sample['rows']:
                for rune,result in row['runes'].items():
                    self.assertEqual(context[rune]['blocked'],result['blocked'])
                    if not result['blocked']:self.assertEqual(context[rune]['display'],result['display'])
        self.assertEqual(store.profile('Gelano'),{'PA':1})
        self.assertEqual(store.limit('Gelano','PA'),1)

    def test_packaged_database_matches_authoring_source(self):
        from hashlib import sha256
        from forgely_dofocus import REFERENCE_PATH,STORE_PATH,canonical_stat
        from forgely_dofocus_store import ReferenceStore
        store=ReferenceStore(STORE_PATH)
        with database_connection(STORE_PATH) as conn:
            metadata=json.loads(conn.execute('SELECT payload FROM metadata').fetchone()[0])
        self.assertEqual(metadata['source_sha256'],sha256(REFERENCE_PATH.read_bytes()).hexdigest())
        for sample in self.data['snapshots']:
            jet={r['stat']:r['value'] for r in sample['rows']}
            context=store.context(sample['item'],jet,sample['pool'])
            expected_profile={canonical_stat(r['stat']):r['max'] for r in sample['rows'] if r['max'] is not None}
            self.assertEqual(store.profile(sample['item']),expected_profile)
            for row in sample['rows']:
                for rune,result in row['runes'].items():
                    self.assertEqual(context[rune]['blocked'],result['blocked'])
                    if not result['blocked']:self.assertEqual(context[rune]['display'],result['display'])

    def test_invalid_source_does_not_replace_working_database(self):
        from forgely_dofocus_store import build_database
        self.build();before=self.db.read_bytes()
        self.source.write_text('[]')
        with self.assertRaises(ValueError):build_database(self.source,self.db)
        self.assertEqual(self.db.read_bytes(),before)

    def test_numeric_equivalence_and_full_context_are_preserved(self):
        store=self.build()
        self.assertEqual(store.context('GELANO',{'PA':0.0},0.0)['Ga Pa']['display']['SC'],'66')
        for jets,pool in (({'PA':False},0),({'PA':0,'Force':0},0),({'PA':0},1),({'PA':0},float('nan'))):
            self.assertIsNone(store.context('Gelano',jets,pool))
        self.assertIsNone(store.context('inconnu',{'PA':0},0))

    def test_cache_is_bounded_and_caller_cannot_change_stored_percentages(self):
        store=self.build()
        result=store.context('Gelano',{'PA':0},0)
        result['Ga Pa']['display']['SC']='99'
        self.assertEqual(store.context('Gelano',{'PA':0},0)['Ga Pa']['display']['SC'],'66')
        for i in range(200):store.context('Gelano',{'PA':i},0)
        self.assertLessEqual(store.cache_info()['contexts'].currsize,64)
        for i in range(100):store.profile(f'Inconnu {i}')
        self.assertLessEqual(store.cache_info()['items'].currsize,32)

    def test_missing_corrupted_and_wrong_schema_are_unavailable(self):
        from forgely_dofocus_store import ReferenceStore
        self.assertIsNone(ReferenceStore(self.db).context('Gelano',{'PA':0},0))
        self.db.write_bytes(b'broken')
        self.assertIsNone(ReferenceStore(self.db).profile('Gelano'))
        self.db.unlink();self.build()
        with database_connection(self.db) as conn:conn.execute('PRAGMA user_version=999')
        self.assertIsNone(ReferenceStore(self.db).context('Gelano',{'PA':0},0))

    def test_advice_does_not_read_authoring_json(self):
        from forgely_decision import advise
        with patch('forgely_dofocus.catalogue',side_effect=AssertionError('full JSON load forbidden')):
            p=advise({'PA':0},{'PA':1},pool=0,item='Gelano')
        self.assertEqual(p.estimates['dofocus']['display']['SC'],'66')

    def test_renamed_or_changed_context_payload_is_rejected(self):
        store=self.build()
        with database_connection(self.db) as conn:
            row=conn.execute('SELECT item_key,state_key,payload FROM contexts LIMIT 1').fetchone()
            payload=json.loads(row[2]);payload['item']='Autre objet'
            conn.execute('UPDATE contexts SET payload=? WHERE item_key=? AND state_key=?',(json.dumps(payload),row[0],row[1]))
        from forgely_dofocus_store import ReferenceStore
        jet={r['stat']:r['value'] for r in payload['rows']}
        self.assertIsNone(ReferenceStore(self.db).context('Anneau du Comte Harebourg',jet,payload['pool']))
