import json
import threading
import pytest
from forgely_training import TrainingConfig,run_training,action_values,state_key,POLICY_VERSION
from forgely_dofocus_engine import MODEL_VERSION
from forgely_rl import ForgemagingEnv


def configuration(**kwargs):
    return TrainingConfig(item_id=14092,targets={'Force':40,'Intelligence':40},
        episodes=4,max_steps=8,evaluation_episodes=3,**kwargs)


def test_training_saves_auditable_policy_and_holdout_evaluation(tmp_path):
    result=run_training(configuration(),tmp_path)
    assert result['episodes_completed']==4
    assert result['source']=='simulation' and result['real_observations']==0
    assert result['evaluation']['learned']['episodes']==3
    assert result['evaluation']['baseline']['episodes']==3
    path=tmp_path/result['run_id']
    policy=json.loads((path/'policy.json').read_text(encoding='utf-8'))
    assert policy['signature']==result['signature'] and policy['q']
    assert (path/'rapport.html').is_file()
    assert not result['automatically_enabled_in_live_advice']


def test_cancel_is_cooperative_and_saves_partial_progress(tmp_path):
    stop=threading.Event()
    def progress(info):
        if info['phase']=='training' and info['completed']>=1:stop.set()
    result=run_training(configuration(),tmp_path,cancel=stop,progress=progress)
    assert result['cancelled'] and result['episodes_completed']<4
    assert (tmp_path/result['run_id']/'policy.json').exists()


def test_resume_only_uses_compatible_item_goal_and_model(tmp_path):
    first=run_training(configuration(),tmp_path)
    second=run_training(configuration(),tmp_path)
    assert second['prior_episodes']==4 and second['episodes_total']==8
    assert second['resumed_from']==first['run_id']
    other=TrainingConfig(item_id=14092,targets={'Force':39},episodes=2,max_steps=8,evaluation_episodes=3)
    assert run_training(other,tmp_path)['prior_episodes']==0


@pytest.mark.parametrize('change',[
    {'episodes':0},{'episodes':True},{'targets':{}},{'item_id':-1},
    {'targets':{'PA':2}},{'initial_pool':float('nan')},
])
def test_invalid_configuration_fails_before_creating_results(tmp_path,change):
    values=dict(item_id=14092,targets={'Force':40},episodes=2,max_steps=8,evaluation_episodes=3)
    values.update(change)
    with pytest.raises(ValueError):run_training(TrainingConfig(**values),tmp_path)
    assert not list(tmp_path.iterdir())


def test_legacy_prices_do_not_filter_training_actions(tmp_path):
    config=TrainingConfig(item_id=14092,targets={'Force':40},episodes=3,max_steps=8,
        evaluation_episodes=3,prices={'Fo':100})
    result=run_training(config,tmp_path)
    assert result['training_runes']
    assert 'prices_provided' not in result
    assert 'prices' not in result['configuration']


def test_policy_exposes_compatible_metadata_and_state_lookup(tmp_path):
    result=run_training(configuration(),tmp_path)
    policy=json.loads((tmp_path/result['run_id']/'policy.json').read_text(encoding='utf-8'))
    assert policy['configuration']['targets']=={'Force':40,'Intelligence':40}
    assert not policy['eligible_for_advice'] and policy['simulation_contribution_only']
    assert policy['advice_validation']['reason']=='insufficient_evaluation'
    env=ForgemagingEnv(policy['profile_lines'],0,policy['configuration']['targets'],max_steps=8)
    state=env.get_state()
    assert action_values(policy,state)==policy['q'][state_key(state)]
    policy['model_version']='different-model'
    assert action_values(policy,state)=={}


def test_corrupt_resume_is_ignored(tmp_path):
    result=run_training(configuration(),tmp_path)
    path=tmp_path/result['run_id']/'policy.json'
    policy=json.loads(path.read_text(encoding='utf-8'))
    policy['q']={'bad':{'Fo':float('inf')}}
    path.write_text(json.dumps(policy),encoding='utf-8')
    assert run_training(configuration(),tmp_path)['prior_episodes']==0


def test_evaluation_cancel_keeps_training_and_partial_evaluation(tmp_path):
    stop=threading.Event()
    def progress(info):
        if info['phase']=='evaluation' and info['completed']==1:stop.set()
    result=run_training(configuration(),tmp_path,cancel=stop,progress=progress)
    assert result['cancelled'] and result['episodes_completed']==4
    assert result['evaluation']['learned']['episodes']==1
    assert (tmp_path/result['run_id']/'metrics.json').is_file()


@pytest.mark.parametrize('targets',[{'Force':40.5},{'PA':.5}])
def test_fractional_stat_targets_fail_before_creating_results(tmp_path,targets):
    with pytest.raises(ValueError,match='entier'):
        run_training(TrainingConfig(item_id=14092,targets=targets,episodes=1,
            max_steps=2,evaluation_episodes=1),tmp_path)
    assert not list(tmp_path.iterdir())


def test_integer_valued_float_target_is_supported(tmp_path):
    result=run_training(TrainingConfig(item_id=14092,targets={'Force':40.0},
        episodes=1,max_steps=2,evaluation_episodes=1),tmp_path)
    assert result['episodes_completed']==1
