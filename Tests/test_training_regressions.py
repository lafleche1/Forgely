import json
from unittest.mock import patch
from forgely_training import TrainingConfig, run_training, _load
from forgely_rl import ForgemagingEnv


def test_early_failures_feed_curriculum_and_preserve_horizon(tmp_path):
    original = ForgemagingEnv.step
    def early_stop(env, action):
        result = original(env, action)
        if env.steps >= 2:
            env.closed = True
        return result
    config = TrainingConfig(14092, {'Force':40,'Intelligence':40},
                            episodes=8,max_steps=5000,evaluation_episodes=1)
    with patch.object(ForgemagingEnv, 'step', early_stop):
        result = run_training(config,tmp_path)
    assert result['curriculum']['buffered_failures'] > 0
    assert result['curriculum']['replayed_episodes'] > 0


def test_resume_keeps_better_policy_instead_of_latest(tmp_path):
    config = TrainingConfig(14092, {'Force':40},episodes=1,max_steps=8,evaluation_episodes=1)
    result = run_training(config,tmp_path)
    original = json.loads((tmp_path/result['run_id']/'policy.json').read_text(encoding='utf-8'))
    for name, wins in [('a-best',90),('z-latest',10)]:
        policy = dict(original, episodes_total=100, configuration=dict(original['configuration'], evaluation_episodes=100),
            evaluation={'learned':{'episodes':100,'successes':wins},
                        'baseline':{'episodes':100,'successes':20}})
        folder=tmp_path/name
        folder.mkdir()
        (folder/'policy.json').write_text(json.dumps(policy),encoding='utf-8')
    assert _load(tmp_path,result['signature'])[3]=='a-best'


def test_default_evaluation_is_larger_and_run_is_reproducible(tmp_path):
    assert TrainingConfig(14092, {'Force':40}).evaluation_episodes >= 200
    config=TrainingConfig(14092,{'Force':40},episodes=4,max_steps=8,evaluation_episodes=3,resume=False)
    a=run_training(config,tmp_path/'a')
    b=run_training(config,tmp_path/'b')
    assert a['evaluation']==b['evaluation']
    assert a['evaluation_protocol']['training_replay'] is False
    assert a['evaluation_protocol']['seed_domain'] != 'training'



def test_independent_audit_is_frozen_and_reproducible(tmp_path):
    from auditer_politique import audit_policy
    config=TrainingConfig(14092,{'Force':40},episodes=2,max_steps=8,evaluation_episodes=2)
    result=run_training(config,tmp_path)
    path=tmp_path/result['run_id']/'policy.json'
    before=path.read_bytes()
    a=audit_policy(path,episodes=3,seed=17)
    assert a==audit_policy(path,episodes=3,seed=17)
    assert path.read_bytes()==before
    assert not a['training'] and not a['promotion']
    assert a['seed_domain']=='independent_audit'


def test_cancelled_checkpoint_cannot_replace_complete_champion(tmp_path):
    from forgely_training import policy_rank
    assert policy_rank({'cancelled':True}) < policy_rank({})


def test_rng_domains_are_disjoint_for_resume_and_holdout():
    from forgely_training import episode_seed
    seeds=[episode_seed(42,domain,i) for domain in
           ('training','evaluation','independent_audit') for i in range(100)]
    assert len(set(seeds))==len(seeds)


def test_training_seeds_advance_even_when_best_checkpoint_is_older(tmp_path):
    config=TrainingConfig(14092,{'Force':40},episodes=2,max_steps=4,evaluation_episodes=2)
    first=run_training(config,tmp_path)
    second=run_training(config,tmp_path)
    third=run_training(config,tmp_path)
    assert first['training_seed_start']==0
    assert second['training_seed_start']==2
    assert third['training_seed_start']==4


def test_minimum_target_does_not_deadlock_below_natural_maximum():
    env=ForgemagingEnv([
        {'stat':'Vitalité','value':289,'min':250,'max':300,'weight':.2},
    ],0,{'Vitalité':290})
    assert 'Vi' in env.get_valid_actions()
    assert 'Ra Vi' not in env.get_valid_actions()


def test_minimum_target_allows_only_indivisible_minimal_finish_at_natural_cap():
    env=ForgemagingEnv([
        {'stat':'Vitalité','value':299,'min':250,'max':300,'weight':.2},
    ],0,{'Vitalité':300})
    assert env.get_valid_actions()==['Vi','stop']
