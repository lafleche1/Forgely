"""Regressions observed during the pool/learning audit, with final advice checks."""
from types import SimpleNamespace
import pytest
from forgely_decision import advise, pool_transition


def simulation(rune):
    return dict(kind='local_dofocus_model', blocked=False,
        probabilities={'SC':40.,'SN':40.,'EC':20.},
        display={'SC':'40','SN':'40','EC':'20'},
        trained_policy=dict(kind='trained_simulation_policy',source='simulation',
            real_observations=0,factor=1.2 if rune=='Ine' else .8,episodes=100))


def observations(rune):
    return dict(n=100,counts={'SC':50,'SN':0,'EC':50},usable=True,quality='local_verified')


def test_large_pool_without_heavy_target_still_recommends_legal_rune():
    p=advise({'Force':39},{'Force':40},natural_max={'Force':40},pool=100,predictive_policy=True)
    assert p.rune=='Fo'
    assert p.estimates['matrix']['pool_repair_preferred'] is True


@pytest.mark.parametrize('pool',[0,1,2,5,19,20,50,51])
@pytest.mark.parametrize(('stat','rune'),[('PA','Ga Pa'),('PM','Ga Pme')])
def test_natural_pa_pm_restoration_never_deadlocks_on_pool_phase(pool,stat,rune):
    p=advise({stat:0},{stat:1},natural_max={stat:1},pool=pool,predictive_policy=True)
    assert p.rune==rune
    assert p.kind=='fm_classique'


@pytest.mark.parametrize('pool',[1,2,5])
def test_red_zone_has_explicit_conservative_policy_and_no_free_weight(pool):
    p=advise({'Force':39},{'Force':40},natural_max={'Force':40},pool=pool,predictive_policy=True)
    assert p.rune=='Fo'
    assert p.estimates['matrix']['phase']=='critical'
    assert p.estimates['decision_trace']['pool_policy']=='conservative_no_free_weight'
    assert pool_transition(pool,10,0,'EC')==0
    assert 'gratuit' not in p.explanation.lower()


def test_phase_fallback_does_not_add_unrequested_over_or_exotic():
    p=advise({'Force':40,'PA':1},{'Force':40},natural_max={'Force':40,'PA':1},pool=100,predictive_policy=True)
    assert p.rune is None and p.kind=='atteint'
    p=advise({'Force':40},{'Force':41},natural_max={'Force':40},pool=100,predictive_policy=True)
    # Over is explicitly requested at minimum 41; a legal result above 41 is accepted.
    assert p.rune in ('Fo','Pa Fo','Ra Fo') and p.kind=='over'


def test_measured_goals_uses_learning_to_change_final_rune(monkeypatch):
    from forgely_measured_goals import MeasuredGoals
    monkeypatch.setattr('forgely_vision_guidance.reference_for',lambda _: {'Force':(0,40),'Intelligence':(0,40)})
    goals=MeasuredGoals();goals.targets={'Force':40,'Intelligence':40}
    # Keep this learning test below the covered Pa reserve threshold.
    snapshot=({'Force':39,'Intelligence':39},2)
    base=goals.proposal(snapshot,item='Audit fixture')
    learned=goals.proposal(snapshot,item='Audit fixture',simulation_for=simulation,contextual_for=observations)
    assert base.rune=='Fo' and learned.rune=='Ine'
    trace=learned.estimates['decision_trace']
    assert trace['selected']=='Ine'
    assert trace['candidates']['Ine']['evidence']['weights']=={'simulation':.4,'real':.6}
    assert trace['candidates']['Ine']['final_rank']==1


def test_unidentified_measured_goal_cannot_borrow_named_learning_sources():
    from forgely_measured_goals import MeasuredGoals
    def forbidden(_):raise AssertionError('Identity not confirmed')
    goals=MeasuredGoals();goals.targets={'Force':40}
    assert goals.proposal(({'Force':39},5),simulation_for=forbidden,contextual_for=forbidden).rune


def test_application_measured_path_receives_real_sources_without_simulation(monkeypatch):
    from forgely import Forgely
    from forgely_measured_goals import MeasuredGoals
    from forgely_simulation_live import SimulationWorker
    goals=MeasuredGoals();goals.targets={'Force':40,'Intelligence':40}
    monkeypatch.setattr('forgely.current_snapshot',lambda _: ({'Force':39,'Intelligence':39},5))
    monkeypatch.setattr('forgely.read_settings',lambda: {'strategy':'Chances maximales'})
    monkeypatch.setattr('forgely_vision_guidance.reference_for',lambda _: {'Force':(0,40),'Intelligence':(0,40)})
    context=SimpleNamespace(key=('fixture',),evidence=simulation)
    def forbidden(*args,**kwargs):raise AssertionError('Automatic simulation disabled')
    monkeypatch.setattr(SimulationWorker,'context',forbidden)
    worker=SimulationWorker(trials=16)
    app=SimpleNamespace(observation_only=False,measured_goals=goals,plan=None,
        item=SimpleNamespace(get=lambda:'Audit fixture'),active_equipment_verified=True,
        live_laboratory=SimpleNamespace(revision=0,estimate=lambda *a:observations(a[1])),simulator=worker)
    try:
        p=Forgely._strategy_current(app)
        assert p.rune is not None
        assert app._simulation_key is None
        assert p.estimates['source_comparison']['weights']['simulation']==0
        assert worker._thread is None
    finally:worker.stop()


def test_detailed_report_explains_effective_sources_and_final_order(monkeypatch):
    from forgely_predictive import report_text
    p=advise({'Force':39,'Intelligence':39},{'Force':40,'Intelligence':40},
        natural_max={'Force':40,'Intelligence':40},pool=5,predictive_policy=True,
        simulation_for=simulation,contextual_for=observations)
    text=report_text(p,{'Force':39,'Intelligence':39},{'Force':40,'Intelligence':40},None,5)
    assert '60 %' in text and '40 %' in text
    assert 'Ine' in text and 'classement' in text.lower()
    assert 'score' in text.lower() and 'séquence' in text.lower()


def test_tabular_policy_requires_current_final_selector_audit():
    from forgely_training import policy_advice_validation
    good={'learned':{'episodes':100,'successes':90},'baseline':{'episodes':100,'successes':10}}
    assert not policy_advice_validation(dict(evaluation=good,q={},visits={}))['eligible']


def test_selector_audit_is_invalidated_by_tabular_or_visits_changes():
    from forgely_training import policy_payload_digest
    policy=dict(q={'state':{'Fo':1}},visits={'state':{'Fo':1}})
    before=policy_payload_digest(policy)
    policy['q']['state']['Fo']=2
    assert policy_payload_digest(policy)!=before
    before=policy_payload_digest(policy)
    policy['visits']['state']['Fo']=2
    assert policy_payload_digest(policy)!=before


def test_final_selector_audit_runs_real_advice_without_promoting_policy(tmp_path):
    import json
    from forgely_training import TrainingConfig,run_training
    from auditer_politique import audit_selector
    result=run_training(TrainingConfig(14092,{'Force':40},episodes=1,max_steps=1,evaluation_episodes=1),tmp_path)
    path=tmp_path/result['run_id']/'policy.json';before=path.read_bytes()
    a=audit_selector(path,episodes=2,seed=41)
    assert a==audit_selector(path,episodes=2,seed=41)
    assert a['evaluation']['learned']['episodes']==2
    assert a['evaluation']['baseline']['episodes']==2
    assert a['advice_calls']>0 and a['selector_validation']['eligible'] is False
    assert a['selector_version'] and a['selector_code_sha256']
    assert a['real_observations']==0 and not a['promotion']
    assert before==path.read_bytes()


def test_policy_invalidation_clears_advice_for_every_cached_state(tmp_path):
    from unittest.mock import patch
    from forgely_simulation_live import SimulationWorker
    from test_simulation_live import cycloid
    from test_trained_policy_advice import saved_policy
    worker=SimulationWorker(trials=16,training_root=tmp_path)
    item,jet=cycloid();jet['Force']=30
    try:
        with patch.object(worker,'_run'):
            first=worker.context(item.name,jet,0,{'Force':40})
            second=worker.context(item.name,{**jet,'Force':31},0,{'Force':40})
        saved_policy(tmp_path,first)
        worker._refresh_policies()
        worker._cache[first.key]={'Fo':{'trained_policy':{'factor':1.2}}}
        worker._cache[second.key]={'Fo':{'trained_policy':{'factor':1.2}}}
        (tmp_path/'test-run'/'policy.json').unlink()
        worker._policies._last_scan=-float('inf')
        worker._refresh_policies()
        assert 'trained_policy' not in first.evidence('Fo')
        assert 'trained_policy' not in second.evidence('Fo')
    finally:worker.stop()


@pytest.mark.parametrize('field',['selector_version','selector_code_sha256','selector_runtime_sha256','policy_payload_sha256'])
def test_stale_selector_identity_cannot_authorize_live_influence(field):
    from forgely_training import policy_advice_validation
    from selector_audit_fixture import qualifying_selector_audit
    good={'learned':{'episodes':100,'successes':90},'baseline':{'episodes':100,'successes':10}}
    policy=dict(evaluation=good,q={},visits={})
    policy['selector_audit']=qualifying_selector_audit(policy)
    assert policy_advice_validation(policy)['eligible']
    policy['selector_audit'][field]='stale'
    assert not policy_advice_validation(policy)['eligible']


def test_shared_probability_model_change_invalidates_selector_fingerprint(monkeypatch):
    from pathlib import Path
    from forgely_training import selector_code_digest
    original=Path.read_bytes
    before=selector_code_digest()
    def changed(path):
        data=original(path)
        return data+b'\n# changed probability implementation' if path.name=='forgely_fm_model.py' else data
    monkeypatch.setattr(Path,'read_bytes',changed)
    assert selector_code_digest()!=before


def test_simulation_only_audit_cannot_enable_policy_in_different_real_snapshot(tmp_path):
    from dataclasses import replace
    from unittest.mock import patch
    from forgely_simulation_live import SimulationWorker
    from test_simulation_live import cycloid
    from test_trained_policy_advice import saved_policy
    worker=SimulationWorker(trials=16,training_root=tmp_path)
    item,jet=cycloid();jet['Force']=30
    try:
        with patch.object(worker,'_run'):
            context=worker.context(item.name,jet,0,{'Force':40})
        saved_policy(tmp_path,context)
        worker._policies.refresh(force=True)
        assert worker._policies.factors(context)
        real=SimpleNamespace(sample_count=1,digest='new-qualified-evidence',transition=lambda _:None)
        assert worker._policies.factors(replace(context,empirical=real))=={}
    finally:worker.stop()


def test_shared_real_posterior_does_not_claim_second_contextual_adjustment():
    from forgely_decision import combine_candidate_evidence
    posterior={**simulation('Fo'),'empirical_n':300}
    result=combine_candidate_evidence(posterior,observations('Fo'))
    assert result['fallback']=='shared_posterior'
    assert result['real_factor'] is None
    assert 'observations_joueurs_contextuelles' not in result['sources']
    assert 'calibration_reelle_deja_incluse' in result['sources']
