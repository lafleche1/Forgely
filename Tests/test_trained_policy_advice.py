import json
import threading
from unittest.mock import patch
from forgely_simulation_live import SimulationWorker
from forgely_trained_policy import TrainedPolicies
from forgely_training import POLICY_VERSION,state_key
from forgely_dofocus_engine import MODEL_VERSION
from forgely_rl import REWARD_VERSION
from test_simulation_live import cycloid


def saved_policy(root,context,**changes):
    state=context.environment(max_steps=100).get_state();key=state_key(state)
    data=dict(policy_version=POLICY_VERSION,model_version=MODEL_VERSION,reward_version=REWARD_VERSION,
        source='simulation',real_observations=0,eligible_for_advice=True,episodes_total=100,
        evaluation={'learned':{'episodes':100,'successes':80},
                    'baseline':{'episodes':100,'successes':20}},
        profile_lines=context._lines(),
        configuration=dict(item_id=context.key[1],targets=dict(context.targets),max_steps=100,prices={},budget=None),
        q={key:{'Fo':10,'Pa Fo':5,'stop':0}},visits={key:{'Fo':10,'Pa Fo':10,'stop':10}})
    data.update(changes)
    directory=root/'test-run';directory.mkdir(exist_ok=True)
    (directory/'policy.json').write_text(json.dumps(data),encoding='utf-8')
    return data


def test_unproven_or_cancelled_policy_never_affects_advice(tmp_path):
    worker=SimulationWorker(trials=16,training_root=tmp_path)
    item,jet=cycloid();jet['Force']=30
    try:
        with patch.object(worker,'_run'):
            context=worker.context(item.name,jet,0,{'Force':40})
        for changes in ({'evaluation':{}},
            {'evaluation':{'learned':{'episodes':100,'successes':0},
                           'baseline':{'episodes':100,'successes':0}}},
            {'cancelled':True},{'reward_version':'target-deficit-1'}):
            saved_policy(tmp_path,context,**changes)
            worker._policies.refresh(force=True)
            assert worker._policies.factors(context)=={}
    finally:worker.stop()


def test_policy_is_loaded_in_background_and_evidence_is_memory_only(tmp_path):
    worker=SimulationWorker(trials=16,training_root=tmp_path)
    item,jet=cycloid();jet['Force']=30
    try:
        with patch.object(worker,'_run'):
            context=worker.context(item.name,jet,0,{'Force':40})
        saved_policy(tmp_path,context)
        worker._policies.refresh(force=True)
        factors=worker._policies.factors(context)
        assert factors['Fo']['factor']==1.2
        assert factors['Fo']['real_observations']==0
        with worker._condition:
            worker._cache[context.key]={'Fo':{'trained_policy':factors['Fo']}}
        with patch.object(worker._policies,'refresh',side_effect=AssertionError('No IO in evidence')):
            evidence=context.evidence('Fo')
        assert evidence['trained_policy']['run_id']=='test-run'
    finally:worker.stop()


def test_economic_or_different_goal_or_unvisited_policies_are_ignored(tmp_path):
    worker=SimulationWorker(trials=16,training_root=tmp_path)
    item,jet=cycloid();jet['Force']=30
    try:
        with patch.object(worker,'_run'):
            context=worker.context(item.name,jet,0,{'Force':40})
        for changes in ({'visits':{}},{'model_version':'wrong'},{'profile_lines':None},
            {'visits':{'bad-state':{'Fo':'bad-count'}}},{'q':{'bad-state':[]}},
            {'configuration':dict(item_id=14092,targets={'Force':40},max_steps=100,prices={'Fo':10})},
            {'configuration':dict(item_id=14092,targets={'Force':39},max_steps=100,prices={})}):
            saved_policy(tmp_path,context,**changes)
            worker._policies.refresh(force=True)
            assert worker._policies.factors(context)=={}
    finally:worker.stop()


def test_completed_training_refreshes_stationary_live_context(tmp_path):
    ready=threading.Event()
    worker=SimulationWorker(trials=16,training_root=tmp_path,on_ready=lambda key:ready.set())
    item,jet=cycloid();jet['Force']=30
    try:
        context=worker.context(item.name,jet,0,{'Force':40})
        assert ready.wait(5)
        assert 'trained_policy' not in context.evidence('Fo')
        ready.clear()
        saved_policy(tmp_path,context)
        assert ready.wait(5)
        evidence=context.evidence('Fo')
        assert evidence['trained_policy']['factor']==1.2
        assert evidence['real_observation'] is False
        assert evidence['outlook']['real_observations']==0
    finally:worker.stop()


def test_older_better_policy_has_priority_in_advice(tmp_path):
    worker=SimulationWorker(trials=16,training_root=tmp_path)
    item,jet=cycloid();jet['Force']=30
    try:
        with patch.object(worker,'_run'):
            context=worker.context(item.name,jet,0,{'Force':40})
        data=saved_policy(tmp_path,context)
        (tmp_path/'test-run').rename(tmp_path/'a-best')
        data['evaluation']['learned']['successes']=60
        key=next(iter(data['q']))
        data['q'][key]={'Fo':0,'Pa Fo':10,'stop':0}
        folder=tmp_path/'z-latest';folder.mkdir()
        (folder/'policy.json').write_text(json.dumps(data),encoding='utf-8')
        worker._policies.refresh(force=True)
        factors=worker._policies.factors(context)
        assert factors['Fo']['run_id']=='a-best'
        assert factors['Fo']['factor']==1.2
    finally:worker.stop()


def test_archive_count_does_not_hide_older_champion(tmp_path):
    worker=SimulationWorker(trials=16,training_root=tmp_path)
    item,jet=cycloid();jet['Force']=30
    try:
        with patch.object(worker,'_run'):
            context=worker.context(item.name,jet,0,{'Force':40})
        data=saved_policy(tmp_path,context)
        (tmp_path/'test-run').rename(tmp_path/'a-best')
        data['evaluation']['learned']['successes']=60
        for i in range(1000):
            folder=tmp_path/f'z-{i:04}';folder.mkdir()
            (folder/'policy.json').write_text(json.dumps(data),encoding='utf-8')
        worker._policies.refresh(force=True)
        assert worker._policies.factors(context)['Fo']['run_id']=='a-best'
    finally:worker.stop()


def test_valid_general_policy_can_adjust_unseen_state_without_fake_visits(tmp_path):
    from forgely_general_policy import make_policy
    worker=SimulationWorker(trials=16,training_root=tmp_path)
    item,jet=cycloid();jet['Force']=30
    try:
        with patch.object(worker,'_run'):
            context=worker.context(item.name,jet,0,{'Force':40})
        saved_policy(tmp_path,context,q={},visits={},
                     general_policy=make_policy([1,0,1,0],episodes=256))
        path=tmp_path/'test-run'/'policy.json'
        data=json.loads(path.read_text(encoding='utf-8'))
        from forgely_training import COPILOT_SELECTOR_VERSION,policy_payload_digest
        data['selector_audit']=dict(selector_version=COPILOT_SELECTOR_VERSION,
            source='simulation',real_observations=0,policy_payload_sha256=policy_payload_digest(data),
            evaluation=data['evaluation'])
        path.write_text(json.dumps(data),encoding='utf-8')
        worker._policies.refresh(force=True)
        factors=worker._policies.factors(context)
        assert factors and factors['Fo']['generalized'] is True
        assert factors['Fo']['action_visits']==0
        assert factors['Fo']['state_visits']==0
        assert factors['Fo']['real_observations']==0
    finally:worker.stop()


def test_direct_policy_gain_does_not_validate_the_deployed_selector(tmp_path):
    from forgely_general_policy import make_policy
    worker=SimulationWorker(trials=16,training_root=tmp_path)
    item,jet=cycloid();jet['Force']=30
    try:
        with patch.object(worker,'_run'):
            context=worker.context(item.name,jet,0,{'Force':40})
        saved_policy(tmp_path,context,q={},visits={},
                     general_policy=make_policy([1,0,1,0],episodes=256))
        worker._policies.refresh(force=True)
        assert worker._policies.factors(context)=={}
    finally:worker.stop()


def test_validated_general_policy_reaches_background_advice_on_unseen_states(tmp_path):
    from forgely_general_policy import make_policy
    from forgely_training import COPILOT_SELECTOR_VERSION,policy_payload_digest
    worker=SimulationWorker(trials=16,training_root=tmp_path)
    item,jet=cycloid();jet['Force']=30
    try:
        with patch.object(worker,'_run'):
            context=worker.context(item.name,jet,0,{'Force':40})
        data=saved_policy(tmp_path,context,q={},visits={},
                     general_policy=make_policy([1,0,1,0],episodes=256))
        data['selector_audit']=dict(selector_version=COPILOT_SELECTOR_VERSION,
            source='simulation',real_observations=0,policy_payload_sha256=policy_payload_digest(data),
            evaluation=data['evaluation'])
        (tmp_path/'test-run'/'policy.json').write_text(json.dumps(data),encoding='utf-8')
        # _run was suppressed when constructing the context, so exercise the real
        # calculation used by the background worker; no real UI is involved.
        result=worker._simulate(context)
        assert result and result['Fo']['trained_policy']['generalized']
        assert result['Fo']['trained_policy']['state_visits']==0
        assert result['Fo']['real_observations']==0
    finally:worker.stop()
