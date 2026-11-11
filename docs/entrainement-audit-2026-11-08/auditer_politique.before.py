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


def audit_selector(path, *, episodes=200, seed=20261108, progress=None):
    """Evaluate the deployed final selector with/without one frozen policy.

    Only this isolated audit injects an unpromoted policy. It never updates the
    checkpoint, player observations, eligibility flags, or live worker.
    """
    from copy import deepcopy
    from forgely_training import (COPILOT_SELECTOR_VERSION, policy_payload_digest,
        selector_code_digest, selector_runtime_digest)
    from forgely_simulation_live import SimulationWorker, SimulationContext
    from forgely_trained_policy import TrainedPolicies
    from forgely_decision import advise
    from forgely_pricing import active_price_book
    from forgely_tools import read_settings
    from forgely_rules import objective_mode
    if type(episodes) is not int or not 1<=episodes<=1000:
        raise ValueError('Sessions hors limites')
    if type(seed) is not int or not 0<=seed<2**63:
        raise ValueError('Graine invalide')
    raw=Path(path).read_bytes();policy=json.loads(raw)
    if (policy.get('policy_version')!=POLICY_VERSION or policy.get('model_version')!=MODEL_VERSION
            or policy.get('reward_version')!=REWARD_VERSION or policy.get('source')!='simulation'
            or policy.get('real_observations')!=0 or not isinstance(policy.get('q'),dict)
            or not isinstance(policy.get('visits'),dict)):
        raise ValueError('Politique incompatible avec le sélecteur actuel')
    if policy.get('general_policy') is not None and not valid_policy(policy['general_policy']):
        raise ValueError('Politique généralisable invalide')
    config=TrainingConfig(**policy['configuration'])
    item,lines,targets,signature,_=_prepare(config)
    transition=None;empirical=None
    if config.use_real_observations:
        from forgely_empirical_model import EmpiricalModel
        empirical=EmpiricalModel.load(Path(path).parent/'empirical_snapshot.json')
        revision=empirical.digest if empirical.sample_count else None
        if revision!=config.empirical_revision:raise ValueError('Instantané réel incompatible avec la politique')
        transition=empirical.transition(item.item_id) if empirical.sample_count else None
    if policy.get('signature')!=signature or policy.get('profile_lines')!=lines:
        raise ValueError('Signature ou profil incompatible')
    if config.allow_preparatory:
        raise ValueError('Actions préparatoires expérimentales exclues du conseil courant')
    book=active_price_book();mode=objective_mode(read_settings().get('strategy','Chances maximales'))
    code_digest=selector_code_digest();runtime_digest=selector_runtime_digest()
    frozen=deepcopy(policy);frozen['_run_id']=Path(path).parent.name
    class FrozenPolicies(TrainedPolicies):
        def __init__(self, enabled):self._policies=[frozen] if enabled else []
        def refresh(self, **kwargs):return False
    evaluation={};calls=adjustments=disagreements=blocked=0
    for name in ('learned','baseline'):
        frozen_real=(lambda item_name,rune,jet,pool:empirical.observation(item_name,rune,jet,pool)) if empirical else None
        worker=SimulationWorker(price_book_for=lambda:book,empirical_for=(lambda:empirical) if empirical else None,real_for=frozen_real)
        worker._policies=FrozenPolicies(name=='learned')
        successes=attempts=0;choices=[]
        try:
            for index in range(episodes):
                env=ForgemagingEnv(lines,config.initial_pool,targets,level=item.level,
                    max_steps=config.max_steps,seed=episode_seed(seed,'independent_selector_audit',index),transition_model=transition)
                while not env.closed:
                    current=tuple((x['stat'],x['value'],x.get('min'),x.get('max'),x['weight']) for x in env.lines)
                    # Learned and baseline share state-specific simulation seeds.
                    key=(MODEL_VERSION,item.item_id,item.level,current,float(env.pool),
                         tuple(sorted(targets.items())),('independent_selector_audit',seed))
                    context=SimulationContext(worker,key,item.level,current,float(env.pool),tuple(sorted(targets.items())),empirical)
                    worker._latest=key
                    results=worker._simulate(context)
                    if results is None:raise RuntimeError('Audit interrompu')
                    worker._cache.clear();worker._cache[key]=results
                    jets={x['stat']:x['value'] for x in env.lines}
                    maxima={x['stat']:x['max'] for x in env.lines if x.get('max') is not None}
                    proposal=advise(jets,targets,natural_max=maxima,pool=env.pool,item=item.identity_name,
                        level=item.level,profile_complete=True,predictive_policy=True,
                        mode=mode,price_book=book,simulation_for=context.evidence,
                        contextual_for=(lambda rune:frozen_real(item.identity_name,rune,jets,env.pool)) if frozen_real else None,
                        context_for=(lambda rune:frozen_real(item.identity_name,rune,jets,env.pool)) if frozen_real else None)
                    calls+=1
                    adjustments+=bool((proposal.estimates or {}).get('local_simulation',{}).get('trained_policy'))
                    choices.append(proposal.rune)
                    if proposal.rune is None:
                        blocked+=proposal.kind!='atteint'
                        env.step('stop');break
                    env.step(proposal.rune);attempts+=1
                successes+=env._complete(env.get_state())
                if progress:progress(name,index+1,episodes)
        finally:worker.stop()
        evaluation[name]=dict(episodes=episodes,successes=successes,
            success_rate=successes/episodes,mean_attempts=attempts/episodes)
        if name=='learned':learned_choices=choices
        else:disagreements=sum(a!=b for a,b in zip(learned_choices,choices))+abs(len(learned_choices)-len(choices))
    if code_digest!=selector_code_digest() or runtime_digest!=selector_runtime_digest():
        raise RuntimeError('Code ou préférences modifiés pendant l’audit : résultat invalidé')
    return dict(source='simulation',real_observations=0,checkpoint_sha256=sha256(raw).hexdigest(),
        empirical_revision=config.empirical_revision,
        policy_payload_sha256=policy_payload_digest(policy),selector_version=COPILOT_SELECTOR_VERSION,
        selector_code_sha256=code_digest,selector_runtime_sha256=runtime_digest,mode=mode,
        seed=seed,seed_domain='independent_selector_audit',training=False,promotion=False,
        policy_frozen=True,evaluation=evaluation,selector_validation=advice_validation(evaluation),
        advice_calls=calls,learned_adjustment_calls=adjustments,choice_differences=disagreements,blocked_calls=blocked,
        limitation='Sélecteur final simulé, sans données réelles ; aucune promotion ni amélioration en jeu démontrée.')


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
    transition=None
    if config.use_real_observations:
        from forgely_empirical_model import EmpiricalModel
        empirical=EmpiricalModel.load(Path(path).parent/'empirical_snapshot.json')
        revision=empirical.digest if empirical.sample_count else None
        if revision!=config.empirical_revision:raise ValueError('Instantané réel incompatible avec la politique')
        transition=empirical.transition(item.item_id) if empirical.sample_count else None
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
                  max_steps=config.max_steps,seed=episode_seed(seed,'independent_audit',index),allow_preparatory=config.allow_preparatory,transition_model=transition)
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
    parser.add_argument('--selector',action='store_true',help='Auditer le conseil final plutôt que la politique directe')
    args=parser.parse_args()
    if args.selector:
        result=audit_selector(args.policy,episodes=args.episodes,seed=args.seed,
            progress=lambda name,n,total:print(f'{name} : {n}/{total}',flush=True))
    else:result=audit_policy(args.policy,episodes=args.episodes,seed=args.seed)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')


if __name__=='__main__':
    main()
