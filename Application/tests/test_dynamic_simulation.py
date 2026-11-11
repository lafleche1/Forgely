import json
from pathlib import Path
import sqlite3
import pytest
import forgely_simulateur as simulator


def test_step_preserves_sc_and_accounts_losses_on_any_line():
    a=simulator.apply_outcome({'Force':0,'PA':1},10,'Fo','SC')
    assert a['jet']=={'Force':1,'PA':1} and a['pool']==10
    b=simulator.apply_outcome({'Force':0,'PA':1},0,'Fo','SN',losses={'PA':1})
    assert b['jet']=={'Force':1,'PA':0} and b['pool']==99
    c=simulator.apply_outcome({'Force':10},0,'Fo','SN',losses={'Force':1})
    assert c['jet']=={'Force':10} and c['pool']==0
    assert simulator.apply_outcome({'Force':0},0,'Fo','EC') is None
    assert simulator.apply_outcome({'Force':0},1,'Fo','EC')['pool']==0
    with pytest.raises(ValueError):simulator.apply_outcome({'Force':0},0,'Fo','SC',losses={'Force':1})


def test_dynamic_session_recomputes_quality_and_never_writes_real_observations(tmp_path):
    r=simulator.simulate_item({'Force':0},{'Force':20},{'Force':100},100,
        prices={'Fo':36,'Pa Fo':132,'Ra Fo':382},trials=1,max_attempts=20,seed=7,trace_limit=20)
    from forgely_fm_model import VERSION
    assert r['model_version']==VERSION
    assert r['source']=='simulation_modele_dynamique'
    assert r['real_observations_written']==0
    steps=r['trace']
    assert len(steps)>=2
    for step in steps:
        from forgely_predictive import estimate
        expected=estimate(step['before']['jet'],{'Force':100},step['rune'])
        assert step['prediction']['SC']==expected['SC']
    assert any(s['prediction']['quality']!=steps[0]['prediction']['quality'] for s in steps[1:])
    assert simulator.simulate_item({'Force':0},{'Force':20},{'Force':100},100,
        prices={'Fo':36,'Pa Fo':132,'Ra Fo':382},trials=1,max_attempts=20,seed=7,trace_limit=20)==r


def test_unknown_losses_count_attempt_cost_and_remain_unknown():
    r=simulator.simulate_item({'Force':99},{'Force':100},{'Force':100},0,
        prices={'Fo':36},trials=1,max_attempts=1,seed=0,trace_limit=1)
    assert r['unknown_transitions']==1 and r['counts']['EC']==1
    assert r['mean_known_cost']==36
    assert r['completion_bounds']==[0,1]
    assert r['trace'][0]['after'] is None


def test_budget_and_goal_stops():
    r=simulator.simulate_item({'Force':0},{'Force':1},{'Force':100},10,
        prices={'Fo':36},budget=35,trials=2,max_attempts=4)
    assert r['attempts']==0 and r['stops']['no_affordable_rune']==2
    r=simulator.simulate_item({'Force':1},{'Force':1},{'Force':100},10,
        prices={},budget=0,trials=2,max_attempts=4)
    assert r['completed']==2 and r['mean_known_cost']==0


def test_approximate_losses_are_explicit_and_bounded():
    r=simulator.simulate_item({'Force':30,'PA':1},{'Force':40},
        {'Force':100,'PA':1},0,prices={'Fo':36,'Pa Fo':132,'Ra Fo':382},
        loss_mode='uniform',trials=5,max_attempts=10,seed=5,trace_limit=10)
    assert r['loss_mode']=='uniform' and 'approxim' in ' '.join(r['warnings']).lower()
    for step in r['trace']:
        if step['after']:
            assert step['after']['pool']>=0
            assert all(v>=0 for v in step['after']['jet'].values())


@pytest.mark.parametrize('kw',[{'pool':float('nan')},{'trials':True},{'max_attempts':0},{'budget':-1}])
def test_invalid_simulation_inputs(kw):
    args=dict(jets={'Force':0},targets={'Force':1},natural_max={'Force':100},pool=10,
              prices={'Fo':36},trials=1,max_attempts=4)
    args.update(kw)
    with pytest.raises(ValueError):simulator.simulate_item(**args)


def test_loss_bank_reads_only_qualified_exact_contexts(tmp_path):
    from forgely_context import save_transition
    from forgely_loss_bank import LossBank
    db=tmp_path/'real.db'
    b={'jet':{'Force':0,'PA':1},'pool':0}
    a={'jet':{'Force':1,'PA':0},'pool':99}
    save_transition('Test','Fo','SN',b,a,db_file=db,natural_max={'Force':100,'PA':1},complete=True)
    save_transition('Test','Fo','SN',b,a,db_file=db)
    bank=LossBank(db)
    assert bank.samples==1
    from random import Random
    assert bank.sample('Test',b['jet'],0,'Fo','SN',Random(0))=={'PA':1}
    assert bank.sample('Other',b['jet'],0,'Fo','SN',Random(0)) is None
    assert bank.sample('Test',b['jet'],1,'Fo','SN',Random(0)) is None
    assert bank.sample('Test',{'Force':1,'PA':1},0,'Fo','SN',Random(0)) is None
    with sqlite3.connect(db) as c:assert c.execute('SELECT count(*) FROM fusion_contexts').fetchone()[0]==2


def test_cli_dynamic_mode_requires_complete_context_and_is_reproducible(tmp_path,capsys):
    from laboratoire_fm import main
    p=tmp_path/'context.json'
    p.write_text(json.dumps({'jets':{'Force':0},'targets':{'Force':10},'natural_max':{'Force':100},
        'pool':10,'level':169,'prices':{'Fo':36,'Pa Fo':132,'Ra Fo':382}}))
    assert main(['--contexte',str(p),'--sessions','2','--limite','10'])==0
    r=json.loads(capsys.readouterr().out)
    assert r['source']=='simulation_modele_dynamique'
    assert r['real_observations_written']==0


def test_application_job_uses_context_model_and_keeps_database_unchanged(tmp_path):
    from forgely_simulation_job import simulate_context
    from forgely_context import save_transition
    db=tmp_path/'real.db'
    for _ in range(30):
        save_transition('Test','Fo','SC',{'jet':{'Force':0},'pool':5},
            {'jet':{'Force':1},'pool':5},db_file=db,natural_max={'Force':100},complete=True)
    original=db.read_bytes()
    context={'item':'Test','jets':{'Force':0},'targets':{'Force':1},'natural_max':{'Force':100},
             'pool':5,'prices':{'Fo':36},'level':169}
    r=simulate_context(context,db_file=db,trials=1,max_attempts=1,trace_limit=1)
    assert r['trace'][0]['prediction']['calibration_n']==30
    assert db.read_bytes()==original
    assert r['context']['level']==169


def test_existing_exo_is_not_assumed_protected_by_a_large_pool():
    r=simulator.simulate_item({'Force':99,'PA':1},{'Force':100},{'Force':100},100,
        prices={'Fo':36},trials=1,max_attempts=1,seed=0,trace_limit=1)
    assert r['unknown_transitions']==1
    assert r['trace'][0]['after'] is None


def test_dynamic_job_keeps_item_specific_rune_guards():
    from unittest.mock import patch
    from forgely_simulation_job import simulate_context
    context={'item':'Test','jets':{'Force':0},'targets':{'Force':1},'natural_max':{'Force':100},
             'pool':5,'prices':{'Fo':36}}
    with patch('forgely_decision.line_limit',side_effect=lambda item,stat:0 if item=='Test' else None):
        r=simulate_context(context,trials=1,max_attempts=1)
    assert r['attempts']==0


@pytest.mark.parametrize('kw',[{'prices':[]},{'profile_complete':'false'}])
def test_malformed_json_context_is_rejected_cleanly(kw):
    args=dict(jets={'Force':0},targets={'Force':1},natural_max={'Force':100},pool=5,
              prices={'Fo':36},trials=1,max_attempts=1)
    args.update(kw)
    with pytest.raises(ValueError):simulator.simulate_item(**args)


def test_malus_has_specific_unmodeled_message():
    with pytest.raises(ValueError,match='[Mm]alus'):
        simulator.simulate_item({'Force':1,'Initiative':0},{'Force':2},
            {'Force':100,'Initiative':-100},5,prices={'Fo':36})
