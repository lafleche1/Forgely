"""Regressions: never transfer simulator percentages across different starting states."""
import unittest
from copy import deepcopy
from forgely_decision import advise

CYClO = {'Vitalité':276,'Force':36,'Intelligence':36,'Agilité':36,
         'Dommages Neutre':9,'Dommages Terre':9,'Dommages Feu':9,
         'Dommages Air':9,'Initiative':251,'% Résistance Eau':7,'Tacle':5}

class DofocusTests(unittest.TestCase):
    def test_exact_full_state_uses_displayed_simulator_values(self):
        from forgely_dofocus import lookup
        result=lookup('ANNEAU DU CYCLOIDE',CYClO,0,'Fo')
        self.assertEqual(result['display'],{'SC':'2','SN':'47','EC':'51'})
        self.assertEqual(result['kind'],'simulation_reference')
        self.assertFalse(result['real_observation'])

    def test_no_transfer_to_partial_changed_or_extra_jet_or_pool(self):
        from forgely_dofocus import lookup
        for jet,pool in (({'Force':36},0),({**CYClO,'Intelligence':35},0),
                         ({**CYClO,'PA':1},0),(CYClO,1),(CYClO,None)):
            self.assertIsNone(lookup('Anneau du Cycloïde',jet,pool,'Fo'))
        self.assertIsNone(lookup('autre objet',CYClO,0,'Fo'))

    def test_known_pool10_state_and_force10_are_distinct(self):
        from forgely_dofocus import lookup
        self.assertEqual(lookup('Anneau du Cycloïde',{**CYClO,'Force':10},10,'Fo')['display']['SC'],'40')
        self.assertIsNone(lookup('Anneau du Cycloïde',{**CYClO,'Force':10},0,'Fo'))

    def test_dofocus_exo_does_not_inherit_huz_fixed_rate(self):
        p=advise({'PA':1,'PM':0},{'PM':1},pool=0,item='Gelano')
        self.assertEqual(p.rune,'Ga Pme')
        self.assertEqual(p.estimates['dofocus']['display']['SC'],'1,5')
        self.assertIsNone(p.estimates['benchmark']['SC'])
        self.assertIn('Modèle FM partagé',p.evidence)
        self.assertEqual(p.estimates['prediction']['SC'],1)
        self.assertEqual(p.sample,0)
        unknown=advise({'PA':0},{'PA':1},natural_max={'Force':100},pool=0)
        self.assertIsNone(unknown.estimates['benchmark']['SC'])

    def test_simulator_forbidden_rune_cannot_be_recommended(self):
        p=advise({'PA':1},{'PA':2},pool=0,item='Gelano')
        self.assertIsNone(p.rune)

    def test_new_damage_and_resistance_targets_use_source_weights(self):
        p=advise({'Dommages Feu':4},{'Dommages Feu':7},pool=15)
        self.assertEqual(p.rune,'Pa Do Feu')
        self.assertIn('15',p.explanation)
        self.assertIn('Modèle FM partagé',p.evidence)

    def test_approximate_zero_is_preserved(self):
        from forgely_dofocus import lookup
        p=lookup('Gelano',{'PA':0},0,'Ga Pa')
        self.assertEqual(p['display']['EC'],'≈0')
        self.assertNotIn('probability',p)

    def test_snapshot_data_are_complete_without_prices_or_real_attempts(self):
        from forgely_dofocus import catalogue, validate_catalogue
        data=catalogue()
        validate_catalogue(data)
        self.assertEqual(data['real_attempts'],0)
        bad=deepcopy(data)
        bad['snapshots'][0]['rows'][0]['runes']['Vi']['display']['SC']='200'
        with self.assertRaises(ValueError):validate_catalogue(bad)

    def test_negative_and_alias_stats_preserve_distinct_meaning(self):
        from forgely_dofocus import canonical_stat, normalise_jet, lookup
        self.assertEqual(canonical_stat('Résistances Eau (%)'),'% Résistance Eau')
        self.assertEqual(canonical_stat('Résistances Eau (fixe)'),'Résistance Eau')
        self.assertIsNone(normalise_jet({'Coups critiques':5,'Coups Critiques':6}))
        self.assertIsNone(lookup('Gelano',{'PA':True},0,'Ga Pa'))

    def test_summary_uses_same_dofocus_engine_and_confirmed_pool(self):
        from forgely_plan import next_action
        plan={'item':'Gelano','stats':{'PA':{'current':0,'target':1}}}
        self.assertIn('confirmer',next_action(plan)[0])
        title,detail=next_action(plan,pool=0)
        self.assertIn('Ga Pa',title)
        self.assertIn('Dofocus',detail)

    def test_legacy_advice_also_uses_dofocus(self):
        from forgely_strategy import recommend
        p=recommend({'item':'Gelano','stats':{'PA':{'current':0,'target':1}}},puits=0,jets_confirmed=True)
        self.assertEqual(p.rune,'Ga Pa')
        self.assertIn('Dofocus',p.details)
        self.assertEqual(p.sample,0)

    def test_negative_natural_stat_can_be_saved_as_an_observed_current(self):
        import tempfile
        from pathlib import Path
        from forgely_plan import save_plan
        with tempfile.TemporaryDirectory() as d:
            plan=save_plan('Baguette de Malléfisk',{'Portée':(-1,0)},Path(d)/'plan.json')
        self.assertEqual(plan['stats']['Portée']['current'],-1)

    def test_invalid_catalogue_shapes_fail_closed(self):
        import json
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from forgely_dofocus import catalogue
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'reference.json'
            try:
                for invalid in ([],{'snapshots':[]},{'schema':1,'kind':'simulation_reference','real_attempts':0,'snapshots':[{}]}):
                    p.write_text(json.dumps(invalid))
                    catalogue.cache_clear()
                    with patch('forgely_dofocus.REFERENCE_PATH',p):
                        self.assertEqual(catalogue()['snapshots'],[])
            finally:catalogue.cache_clear()

    def test_wrong_rune_row_and_provenance_are_rejected(self):
        from forgely_dofocus import catalogue,validate_catalogue
        for mutate in ('rune_row','source','date'):
            bad=deepcopy(catalogue())
            if mutate=='rune_row':
                bad['snapshots'][0]['rows'][0]['runes']['Fo']=bad['snapshots'][0]['rows'][1]['runes'].pop('Fo')
            elif mutate=='source':bad['source']='autre simulateur'
            else:bad['captured_on']='date inconnue'
            with self.subTest(mutate=mutate),self.assertRaises(ValueError):validate_catalogue(bad)

    def test_validated_capture_date_is_not_replaced_by_a_literal(self):
        import json,tempfile
        from pathlib import Path
        from unittest.mock import patch
        from forgely_dofocus import catalogue,lookup
        from forgely_dofocus_store import build_database
        data=deepcopy(catalogue());data['captured_on']='2026-11-06'
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'source.json';db=Path(directory)/'reference.sqlite3'
            source.write_text(json.dumps(data),encoding='utf-8');build_database(source,db)
            with patch('forgely_dofocus.STORE_PATH',db):
                self.assertEqual(lookup('Gelano',{'PA':0},0,'Ga Pa')['captured_on'],'2026-11-06')

    def test_advice_window_fits_short_screens(self):
        from forgely_dashboard import advice_window_size
        self.assertEqual(advice_window_size(800,510),(680,430))
        self.assertEqual(advice_window_size(1920,1080),(680,700))

    def test_invalid_explicit_profile_does_not_disable_constraints(self):
        for invalid in ({'PA':float('nan')},{'PA':True},{'Coups Critiques':1,'Coups critiques':2}):
            with self.subTest(profile=invalid):
                self.assertIsNone(advise({'PA':1},{'PA':2},natural_max=invalid,pool=0).rune)
