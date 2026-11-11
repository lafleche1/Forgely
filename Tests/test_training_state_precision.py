from forgely_rl import ForgemagingEnv
from forgely_training import state_key


def environment(value=290, pool=0, stock=None):
    return ForgemagingEnv([dict(stat='Vitalité', value=value, min=250, max=300, weight=.2)],
                          pool, {'Vitalité':300}, max_steps=100, stock=stock)


def test_key_distinguishes_rune_legality_at_natural_cap():
    a, b = environment(285), environment(286)
    assert a.get_valid_actions() != b.get_valid_actions()
    assert state_key(a.get_state()) != state_key(b.get_state())


def test_key_distinguishes_pool_covering_small_rune():
    assert state_key(environment(pool=0).get_state()) != state_key(environment(pool=1).get_state())


def test_key_distinguishes_remaining_attempts():
    a = environment()
    before = state_key(a.get_state())
    a.steps = 1
    assert state_key(a.get_state()) != before


def test_key_distinguishes_available_stock():
    assert state_key(environment(stock={'Vi':1}).get_state()) != state_key(environment(stock={'Vi':0}).get_state())



def test_equivalent_numeric_readings_reuse_key():
    a,b=environment(285),environment(285.0)
    assert state_key(a.get_state()) == state_key(b.get_state())


def test_old_discretized_policy_is_not_applied_or_audited(tmp_path):
    import json
    import pytest
    from forgely_training import action_values
    from auditer_politique import audit_policy
    from forgely_dofocus_engine import MODEL_VERSION
    from forgely_rl import REWARD_VERSION
    state=environment().get_state()
    for version in ('generalized-no-currency-5','tabular-no-currency-4'):
        policy=dict(policy_version=version,model_version=MODEL_VERSION,
                    reward_version=REWARD_VERSION,q={state_key(state):{'Vi':999}})
        assert action_values(policy,state)=={}
        path=tmp_path/'legacy.json'
        path.write_text(json.dumps(policy),encoding='utf-8')
        with pytest.raises(ValueError,match='incompatible'):
            audit_policy(path,episodes=1)
