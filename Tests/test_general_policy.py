import pytest
from forgely_rl import ForgemagingEnv


def environment(value=20,pool=0):
    return ForgemagingEnv([
        {'stat':'Force','value':value,'min':10,'max':40,'weight':1},
        {'stat':'Vitalité','value':270,'min':250,'max':300,'weight':.2},
    ],pool,{'Force':40,'Vitalité':290},seed=7,max_steps=50)


def test_general_policy_scores_unseen_states_without_mutating_them():
    from forgely_general_policy import score_actions, make_policy
    env=environment();before=env.get_state()
    policy=make_policy([1,0,1,0],episodes=16)
    a=score_actions(env.lines,env.pool,env.targets,env.level,env.get_valid_actions(),policy)
    other=environment(value=21)
    b=score_actions(other.lines,other.pool,other.targets,other.level,other.get_valid_actions(),policy)
    assert a and b and all(x!='stop' for x in a)
    assert before==env.get_state()
    assert a!=b


def test_general_policy_cannot_use_prices_or_invalid_parameters():
    from forgely_general_policy import make_policy, valid_policy
    for weights in ([float('nan'),0,1,0],[1,-1,1,0],[True,0,1,0],[1,2]):
        with pytest.raises(ValueError):make_policy(weights,episodes=16)
    assert not valid_policy({'kind':'mass-deficit-search-1','parameters':[1,0,1,0],'episodes':0})


def test_general_scores_preserve_legal_actions_and_finish_whole_jet():
    from forgely_general_policy import score_actions, make_policy
    env=environment(value=40)
    row=score_actions(env.lines,env.pool,env.targets,env.level,env.get_valid_actions(),
                      make_policy([1,0,1,0],episodes=16))
    assert row and set(row)<=set(env.get_valid_actions())
    assert all(env._spec(r)['stat']=='Vitalité' for r in row)


def test_general_training_is_saved_and_used_on_unseen_states(tmp_path,monkeypatch):
    import json
    from forgely_training import TrainingConfig,run_training,action_values
    from forgely_general_policy import make_policy
    learned=make_policy([1,0,1,0],episodes=16)
    monkeypatch.setattr('forgely_training._search_policy',lambda *args:(learned,dict(episodes=16,training_only=True)))
    config=TrainingConfig(14092,{'Force':40,'Intelligence':40},episodes=32,
        max_steps=8,evaluation_episodes=2,policy_search_episodes=16)
    result=run_training(config,tmp_path)
    policy=json.loads((tmp_path/result['run_id']/'policy.json').read_text(encoding='utf-8'))
    assert policy['general_policy']['episodes']==16
    assert result['policy_search']['training_only'] is True
    policy['q']={}
    from forgely_training import _prepare
    item,lines,targets,_,_=_prepare(config)
    env=ForgemagingEnv(lines,0,targets,level=item.level,max_steps=8)
    assert action_values(policy,env.get_state())


def test_search_is_balanced_uses_training_seeds_and_preserves_incumbent_on_tie():
    from forgely_training import _search_policy,TrainingConfig
    config=TrainingConfig(14092,{'Force':40},episodes=32,policy_search_episodes=18)
    seeds=[]
    def make_env(seed):
        seeds.append(seed)
        return ForgemagingEnv([{'stat':'Force','value':39,'min':10,'max':40,'weight':1}],
                            0,{'Force':40},max_steps=1,seed=seed)
    selected,search=_search_policy(config,make_env,{},[],0,lambda:False,lambda *args:None)
    assert search['episodes']==18
    assert len(set(seeds))==2
    assert all(row['episodes']==2 for row in search['candidates'])
    assert search['seed_domain']=='policy_search:0'
    assert search['selected']==0 and selected is None


def test_audit_rejects_corrupt_general_policy_instead_of_silent_tabular_fallback(tmp_path):
    import json
    from forgely_training import run_training,TrainingConfig
    from auditer_politique import audit_policy
    result=run_training(TrainingConfig(14092,{'Force':40},episodes=1,max_steps=2,evaluation_episodes=1),tmp_path)
    path=tmp_path/result['run_id']/'policy.json'
    policy=json.loads(path.read_text(encoding='utf-8'))
    policy['general_policy']={'kind':'wrong'}
    path.write_text(json.dumps(policy),encoding='utf-8')
    with pytest.raises(ValueError):audit_policy(path,episodes=1)


def test_audit_previous_policy_version_remains_reproducible():
    from pathlib import Path
    from auditer_politique import audit_policy
    path=Path(__file__).resolve().parents[1]/'Entrainements/verification-20261108/20261108-021833-877007-14092-5ff083/policy.json'
    if not path.exists():pytest.skip('Local historical checkpoint absent')
    result=audit_policy(path,episodes=1,seed=123)
    assert result['evaluation']['learned']['episodes']==1


def test_search_cancellation_saves_no_half_evaluated_general_policy():
    from forgely_training import _search_policy,TrainingConfig
    import threading
    stop=threading.Event()
    config=TrainingConfig(14092,{'Force':40},episodes=32,policy_search_episodes=18)
    q={}
    def make_env(seed):
        return ForgemagingEnv([{'stat':'Force','value':39,'min':10,'max':40,'weight':1}],
                            0,{'Force':40},max_steps=1,seed=seed)
    def progress(*args):stop.set()
    selected,search=_search_policy(config,make_env,q,[],0,stop.is_set,progress)
    assert selected is None and search['cancelled']
    assert search['episodes']==1 and q=={}


def test_selector_validation_is_bound_to_the_exact_general_payload():
    from forgely_training import (policy_advice_validation,policy_payload_digest,
                                  COPILOT_SELECTOR_VERSION)
    from forgely_general_policy import make_policy
    good={'learned':{'episodes':100,'successes':90},'baseline':{'episodes':100,'successes':10}}
    policy=dict(general_policy=make_policy([1,0,1,0],episodes=18),evaluation=good)
    assert not policy_advice_validation(policy)['eligible']
    policy['selector_audit']=dict(selector_version=COPILOT_SELECTOR_VERSION,source='simulation',
        real_observations=0,policy_payload_sha256=policy_payload_digest(policy),evaluation=good)
    assert policy_advice_validation(policy)['eligible']
    policy['general_policy']['parameters'][0]=.5
    assert not policy_advice_validation(policy)['eligible']


def test_unproven_general_search_is_opt_in_by_default():
    from forgely_training import TrainingConfig
    assert TrainingConfig(14092,{'Force':40}).policy_search_episodes==0
