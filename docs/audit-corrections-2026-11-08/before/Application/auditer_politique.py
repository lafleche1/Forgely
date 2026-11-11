"""Reproducible independent audit of a frozen checkpoint; never trains or promotes it."""
import argparse
import json
from hashlib import sha256
from pathlib import Path
from forgely_training import (TrainingConfig, _prepare, _actions, _choose, _heuristic,
                              episode_seed, advice_validation, POLICY_VERSION)
from forgely_rl import ForgemagingEnv, REWARD_VERSION
from forgely_dofocus_engine import MODEL_VERSION
from forgely_general_policy import valid_policy
from forgely_equipment_catalog import equipment_bounds
from forgely_dofocus import canonical_stat


def audit_policy(path, *, episodes=200, seed=20261108):
    if type(episodes) is not int or not 1<=episodes<=1000:
        raise ValueError('Sessions hors limites')
    raw=Path(path).read_bytes()
    policy=json.loads(raw)
    if (policy.get('policy_version') not in (POLICY_VERSION,'tabular-no-currency-4') or policy.get('model_version')!=MODEL_VERSION
            or policy.get('reward_version')!=REWARD_VERSION):
        raise ValueError('Politique incompatible : nouvel entraînement nécessaire')
    if policy.get('general_policy') is not None and not valid_policy(policy['general_policy']):
        raise ValueError('Politique généralisable invalide')
    config=TrainingConfig(**policy['configuration'])
    item,lines,targets,signature,_=_prepare(config)
    if policy['policy_version']=='tabular-no-currency-4':
        legacy={k:v for k,v in policy['configuration'].items()
                if k not in ('episodes','evaluation_episodes','resume')}
        legacy.update(model=MODEL_VERSION,policy=policy['policy_version'],reward=REWARD_VERSION,
                      bounds={canonical_stat(k):v for k,v in equipment_bounds(item).items()})
        signature=sha256(json.dumps(legacy,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    if policy.get('signature')!=signature:
        raise ValueError('Signature incompatible')
    evaluation={}
    for name in ('learned','baseline'):
        successes=attempts=0
        for index in range(episodes):
            env=ForgemagingEnv(lines,config.initial_pool,targets,level=item.level,
                  max_steps=config.max_steps,seed=episode_seed(seed,'independent_audit',index),allow_preparatory=config.allow_preparatory)
            while not env.closed:
                actions=_actions(env)
                action=_choose(env,actions,policy['q'],policy.get('general_policy')) if name=='learned' else _heuristic(env,actions)
                env.step(action)
                attempts+=action!='stop'
            successes+=env._complete(env.get_state())
        evaluation[name]=dict(episodes=episodes,successes=successes,
            success_rate=successes/episodes,mean_attempts=attempts/episodes)
    return dict(source='simulation',real_observations=0,checkpoint_sha256=sha256(raw).hexdigest(),
        seed=seed,seed_domain='independent_audit',training=False,promotion=False,
        evaluation=evaluation,validation=advice_validation(evaluation),
        limitation='Audit synthétique du modèle local ; aucune amélioration réelle en jeu démontrée.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('policy',type=Path)
    parser.add_argument('--episodes',type=int,default=200)
    parser.add_argument('--seed',type=int,default=20261108)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=audit_policy(args.policy,episodes=args.episodes,seed=args.seed)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':
    main()
