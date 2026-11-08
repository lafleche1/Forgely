import pytest
from forgely_rl import ForgemagingEnv


def env(**kwargs):
    return ForgemagingEnv([
        {'stat':'Force','value':19,'min':10,'max':20,'weight':1},
        {'stat':'PM','value':1,'min':1,'max':1,'weight':90},
    ], 3.5, {'Force':20}, seed=7, **kwargs)


def test_state_has_stable_vector_exact_pool_and_no_mutable_aliases():
    e=env();state=e.get_state()
    assert state['pool']==3.5
    assert len(state['vector'])==len(state['features'])
    assert state['stats']['Force']['max']==20
    state['stats']['Force']['value']=99
    assert e.get_state()['stats']['Force']['value']==19


def test_actions_exclude_unrequested_pm_over_but_ignore_old_prices():
    e=env(prices={'Fo':4},budget=3)
    assert 'Ga Pme' not in e.get_valid_actions()
    assert e.get_valid_actions()==['Fo','stop']


def test_step_is_seeded_and_invalid_action_cannot_change_state():
    a,b=env(),env()
    assert a.step('Fo')==b.step('Fo')
    before=a.get_state()
    with pytest.raises(ValueError):a.step('Ga Pme')
    assert a.get_state()==before


def test_stop_terminates_and_simulation_never_claims_real_observation():
    e=env();state,reward,terminated,truncated,info=e.step('stop')
    assert terminated and not truncated
    assert info['source']=='simulation' and info['real_observation'] is False
    assert reward<0
    with pytest.raises(ValueError):e.step('Fo')


def test_reward_does_not_reward_excess_or_punish_useful_pool():
    e=env()
    before=e.get_state()
    after=env().get_state()
    after['stats']['Force']['value']=20;after['pool']=0
    reward=e.reward(before,after,cost=0)
    after['stats']['Force']['value']=25
    assert e.reward(before,after,cost=0)==reward
    assert reward>0


def test_step_horizon_reset_without_monetary_state():
    e=env(prices={'Fo':2},budget=3,max_steps=1)
    assert e.get_valid_actions()==['Fo','stop']
    state,_,done,truncated,info=e.step('Fo')
    assert 'budget' not in state and 'cost' not in info
    assert done or truncated
    e.reset(seed=7)
    assert 'budget' not in e.get_state()
    assert e.get_state()['pool']==3.5


def test_live_simulation_context_exposes_environment_and_reward():
    import threading
    from test_simulation_live import cycloid
    from forgely_simulation_live import SimulationWorker
    item,jet=cycloid();ready=threading.Event()
    worker=SimulationWorker(trials=16,on_ready=lambda key:ready.set())
    try:
        context=worker.context(item.name,jet,3.5,{'Force':40})
        assert context.environment(seed=1).get_state()['pool']==3.5
        assert ready.wait(5)
        result=context.evidence('Fo')['outlook']
        assert result['reward_version']=='complete-target-first-2'
        assert isinstance(result['mean_reward'],float)
        assert result['real_observations']==0
    finally:worker.stop()


@pytest.mark.parametrize('kwargs',[{'pool':float('nan')},{'targets':{'Unknown':1}},
    {'confidence':-1}])
def test_invalid_inputs_rejected(kwargs):
    args=dict(lines=[{'stat':'Force','value':1,'min':0,'max':20,'weight':1}],
              pool=0,targets={'Force':20})
    args.update(kwargs)
    with pytest.raises(ValueError):ForgemagingEnv(**args)
