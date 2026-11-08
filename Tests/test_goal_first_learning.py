from copy import deepcopy

from forgely_rl import ForgemagingEnv
from forgely_training import _actions


def environment(**options):
    return ForgemagingEnv([
        {'stat': 'Force', 'value': 19, 'min': 0, 'max': 20, 'weight': 1},
        {'stat': 'PA', 'value': 0, 'min': None, 'max': None, 'weight': 100},
    ], 0, {'Force': 20, 'PA': 1}, **options)


def test_training_does_not_choose_abandon_while_targeted_runes_remain():
    assert 'stop' not in _actions(environment())
    assert _actions(environment(stock={})) == ['stop']


def test_abandoning_an_incomplete_jet_is_not_a_neutral_reward():
    _, reward, done, truncated, _ = environment().step('stop')
    assert done and not truncated
    assert reward < 0


def test_complete_jet_has_priority_over_large_partial_progress_and_cost():
    env = environment(max_steps=10)
    before = env.get_state()
    partial = deepcopy(before)
    partial['stats']['PA']['value'] = 1
    complete = deepcopy(partial)
    complete['stats']['Force']['value'] = 20
    assert env.reward(before, complete, cost=10**12) > env.reward(before, partial, cost=0) + .5


def test_terminal_failure_cannot_keep_partial_progress_reward():
    env = environment()
    before = env.get_state()
    after = deepcopy(before)
    after['stats']['PA']['value'] = 1
    assert env.reward(before, after, cost=0, failed=True) < 0


def test_prices_do_not_reduce_the_learning_reward_for_the_same_jet():
    env=environment()
    before=env.get_state()
    complete=deepcopy(before)
    complete['stats']['Force']['value']=20
    complete['stats']['PA']['value']=1
    assert env.reward(before,complete,cost=0)==env.reward(before,complete,cost=10**12)


def test_training_fallback_prioritizes_progress_over_rune_price():
    from forgely_training import _heuristic
    env=ForgemagingEnv([
        {'stat':'Force','value':0,'min':0,'max':40,'weight':1},
    ],0,{'Force':40},prices={'Fo':1,'Pa Fo':100000,'Ra Fo':1000000000})
    assert _heuristic(env,_actions(env))=='Ra Fo'


def test_holdout_validation_requires_a_demonstrated_goal_completion_gain():
    from forgely_training import advice_validation
    def result(wins, n=100):
        return {'episodes': n, 'successes': wins}
    for evaluation in ({}, {'learned': result(0), 'baseline': result(0)},
                       {'learned': result(5, 5), 'baseline': result(0, 5)},
                       {'learned': result(10), 'baseline': result(10)},
                       {'learned': result(90), 'baseline': result(0, 50)}):
        assert not advice_validation(evaluation)['eligible']
    good = {'learned': result(80), 'baseline': result(20)}
    assert advice_validation(good)['eligible']
    assert not advice_validation(good, cancelled=True)['eligible']
