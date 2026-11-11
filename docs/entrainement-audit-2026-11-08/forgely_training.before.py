"""Offline, cancellable training with auditable JSON checkpoints.

Synthetic outcomes remain simulations, never player observations. Policies are
experimental: validation compares them with a simple heuristic on held-out seeds.
"""
from collections import Counter, deque
from copy import deepcopy
from dataclasses import dataclass, asdict, replace
from datetime import datetime, timezone
from hashlib import sha256
from html import escape
import json
from math import floor
from pathlib import Path
from random import Random
from time import perf_counter
from uuid import uuid4

from forgely_dofocus import canonical_stat, RUNE_CHOICES, WEIGHT_PER_POINT, reference
from forgely_dofocus_engine import MODEL_VERSION, odds
from forgely_equipment_catalog import EquipmentCatalog, equipment_bounds
from forgely_rl import ForgemagingEnv, REWARD_VERSION
from forgely_rules import constraints, finite_number
from forgely_probabilites import wilson

POLICY_VERSION = 'generalized-no-currency-5'
MAX_STATES = 50000
from forgely_general_policy import CANDIDATES,make_policy,valid_policy,score_actions,state_scores


@dataclass(frozen=True)
class TrainingConfig:
    item_id: int
    targets: dict
    episodes: int = 1000
    max_steps: int = 100
    evaluation_episodes: int = 200
    policy_search_episodes: int = 0
    initial_preset: str = 'moyen'
    initial_pool: float = 0.
    # Deprecated compatibility inputs; never persisted or used in calculations.
    prices: dict | None = None
    budget: float | None = None
    seed: int = 20261107
    resume: bool = True
    allow_preparatory: bool = False
    use_real_observations: bool = False
    empirical_revision: str | None = None


def _prepare(config):
    if not isinstance(config, TrainingConfig):
        raise ValueError('Configuration invalide')
    for name, lower, upper in [('episodes',1,1000000),('max_steps',1,5000),
                                ('evaluation_episodes',1,1000),('policy_search_episodes',0,8192),('item_id',1,1000000000)]:
        value=getattr(config,name)
        if type(value) is not int or not lower<=value<=upper:
            raise ValueError(f'{name} hors limites ({lower} à {upper})')
    if type(config.seed) is not int or not 0<=config.seed<2**63:
        raise ValueError('Graine invalide')
    if type(config.resume) is not bool:
        raise ValueError('Option de reprise invalide')
    if type(config.allow_preparatory) is not bool:
        raise ValueError('Option préparatoire invalide')
    if type(config.use_real_observations) is not bool:
        raise ValueError('Option de données réelles invalide')
    if config.empirical_revision is not None:
        if (not config.use_real_observations or not isinstance(config.empirical_revision,str)
                or len(config.empirical_revision)!=64 or any(c not in '0123456789abcdef' for c in config.empirical_revision)):
            raise ValueError('Version des données réelles invalide')
    if config.allow_preparatory and config.policy_search_episodes:
        raise ValueError('Compare les actions préparatoires sans activer simultanément la stratégie généralisable.')
    item=EquipmentCatalog().get(config.item_id)
    bounds=equipment_bounds(item) if item else {}
    bounds={canonical_stat(s):pair for s,pair in bounds.items()}
    if any(min(pair)<0 for pair in bounds.values()):
        raise ValueError('Objet avec malus : entraînement indisponible sans règles signées validées.')
    if not bounds or any(s not in WEIGHT_PER_POINT for s in bounds):
        raise ValueError('Objet sans profil naturel complet exploitable')
    if not isinstance(config.targets,dict) or not config.targets:
        raise ValueError('Renseigne au moins une cible')
    targets={}
    for name,value in config.targets.items():
        stat=canonical_stat(name)
        if stat not in RUNE_CHOICES or not finite_number(value) or not 0<=value<=30000:
            raise ValueError('Cible invalide : '+str(name))
        if value != int(value):
            raise ValueError('La cible doit être un entier pour '+stat)
        if stat in targets:raise ValueError('Cible dupliquée : '+stat)
        targets[stat]=value
    check=constraints(targets,{s:p[1] for s,p in bounds.items()})
    if check['valid'] is not True:raise ValueError(check['reason'])
    if (not finite_number(config.initial_pool,nonnegative=True) or config.initial_pool>30000
            or config.initial_preset not in ('minimum','moyen','maximum','min','max')):
        raise ValueError('Jet initial ou reliquat invalide')
    lines=[]
    for stat in sorted(set(bounds)|set(targets)):
        lo,hi=bounds.get(stat,(None,None))
        value=0 if hi is None else (lo if config.initial_preset in ('min','minimum') else
            hi if config.initial_preset in ('max','maximum') else floor((lo+hi)/2+.5))
        lines.append(dict(stat=stat,value=value,min=lo,max=hi,weight=WEIGHT_PER_POINT[stat]))
    if all(next(x['value'] for x in lines if x['stat']==s)>=v for s,v in targets.items()):
        raise ValueError('Le jet initial atteint déjà toutes les cibles')
    spec=asdict(config);spec.update(targets=targets)
    spec.pop('prices',None);spec.pop('budget',None)
    if not config.allow_preparatory:spec.pop('allow_preparatory',None)
    if not config.use_real_observations:
        spec.pop('use_real_observations',None);spec.pop('empirical_revision',None)
    signature_data={k:v for k,v in spec.items() if k not in ('episodes','evaluation_episodes','resume')}
    signature_data.update(model=MODEL_VERSION,policy=POLICY_VERSION,reward=REWARD_VERSION,
                          bounds=bounds)
    if config.allow_preparatory:
        from forgely_reasoning import VERSION
        signature_data['reasoning_version']=VERSION
    signature=sha256(json.dumps(signature_data,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return item,lines,targets,signature,spec


def state_key(state, *, initial_budget=None):
    """All lines plus pool and horizon; discretization is approximate."""
    parts=[]
    for stat,line in sorted(state['stats'].items()):
        value=line['value']
        scale=max(1,abs(line.get('max') or 0),abs(line.get('target') or 0))
        parts.append(int(value) if WEIGHT_PER_POINT[stat]>=20 else floor(16*value/scale))
    remaining=dict(zip(state['features'],state['vector']))['steps_remaining']
    parts.extend((floor(state['pool']/2),min(15,floor(16*remaining))))
    if state.get('preparatory'):
        # Do not merge a completed line at max and the same line with +1 over.
        parts.append('prep1')
        parts.extend(f'{s}:{line["value"]}' for s,line in sorted(state['stats'].items())
                     if line.get('max') is not None and line['value']>=line['max'])
    return ','.join(map(str,parts))


def action_values(policy,state):
    """Return generalized utilities when trained, otherwise tabular Q values.

    Caller must first match model/version/item/targets/max_steps.
    Utilities and Q rewards are ranking scores, never probabilities or real observations.
    """
    if policy.get('policy_version')!=POLICY_VERSION or policy.get('model_version')!=MODEL_VERSION:
        return {}
    if valid_policy(policy.get('general_policy')):
        return state_scores(state,policy['general_policy'])
    key=state_key(state)
    return dict(policy.get('q',{}).get(key,{}))


def _key(env):
    return state_key(env.get_state())


policy_state_key = _key


def _actions(env):
    actions=env.get_valid_actions()
    runes=[a for a in actions if a!='stop']
    # The requested goal is completion. Voluntary abandonment is not an
    # alternative to a permitted attempt; exhausted stocks still stop.
    return runes or (['stop'] if 'stop' in actions else [])


def advice_validation(evaluation, *, cancelled=False):
    """Conservative holdout gate, based on complete jets, never shaped reward."""
    result={'eligible':False,'criterion':'complete_jet_wilson95_superiority',
            'minimum_episodes':50,'reason':'insufficient_evaluation'}
    if cancelled:
        return {**result,'reason':'cancelled'}
    if not isinstance(evaluation,dict):return result
    intervals={};sizes=[]
    for name in ('learned','baseline'):
        row=evaluation.get(name)
        if not isinstance(row,dict):return result
        n,wins=row.get('episodes'),row.get('successes')
        if (type(n) is not int or not 50<=n<=1000 or type(wins) is not int
                or not 0<=wins<=n):return result
        sizes.append(n);intervals[name]=wilson(wins,n)
    if sizes[0]!=sizes[1]:return result
    eligible=intervals['learned'][0]>intervals['baseline'][1]
    return {**result,'eligible':eligible,'intervals':intervals,
            'reason':'demonstrated_gain' if eligible else 'no_demonstrated_gain'}


COPILOT_SELECTOR_VERSION='copilot-pool-fallback-learning-4'


def selector_code_digest():
    """Bind validation to the actual selector and transition implementation."""
    filenames=('forgely_decision.py','forgely_predictive.py','forgely_simulation_live.py',
               'forgely_trained_policy.py','forgely_training.py','forgely_sequence.py',
               'forgely_pricing.py','forgely_rules.py','forgely_weights.py',
               'forgely_dofocus.py','forgely_dofocus_engine.py','forgely_rl.py','forgely_general_policy.py',
               'forgely_fm_model.py','forgely_empirical_model.py','forgely_fm_classification.py','forgely_probabilites.py','forgely_measured_goals.py',
               'forgely_equipment_catalog.py','forgely_reasoning.py',
               'references/poids_runes_client_3_7_13_17.json')
    root=Path(__file__).resolve().parent
    digest=sha256()
    for filename in filenames:
        digest.update(filename.encode());digest.update((root/filename).read_bytes())
    return digest.hexdigest()


def selector_runtime_digest():
    from forgely_pricing import active_price_book
    from forgely_tools import read_settings
    from forgely_rules import objective_mode
    book=active_price_book()
    payload=dict(mode=objective_mode(read_settings().get('strategy','Chances maximales')),
                 prices=asdict(book) if book is not None else None)
    return sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def policy_payload_digest(policy):
    keys=('model_version','policy_version','reward_version','configuration','profile_lines','general_policy','q','visits')
    payload={key:policy.get(key) for key in keys}
    return sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def policy_advice_validation(policy, *, selector_identity=None):
    """A direct policy test cannot certify a different deployed selector."""
    direct=advice_validation(policy.get('evaluation'),cancelled=policy.get('cancelled',False))
    if not direct['eligible']:return direct
    code,runtime=selector_identity or (selector_code_digest(),selector_runtime_digest())
    audit=policy.get('selector_audit')
    if (not isinstance(audit,dict) or audit.get('selector_version')!=COPILOT_SELECTOR_VERSION
            or audit.get('source')!='simulation' or audit.get('real_observations')!=0
            or audit.get('empirical_revision')!=policy.get('configuration',{}).get('empirical_revision')
            or audit.get('selector_code_sha256')!=code
            or audit.get('selector_runtime_sha256')!=runtime
            or audit.get('policy_payload_sha256')!=policy_payload_digest(policy)):
        return {**direct,'eligible':False,'reason':'advice_selector_not_validated',
                'direct_policy_eligible':True}
    selector=advice_validation(audit.get('evaluation'))
    return {**direct,'eligible':selector['eligible'],'selector_validation':selector,
            'reason':'demonstrated_selector_gain' if selector['eligible'] else 'no_demonstrated_selector_gain'}


def _heuristic(env,actions):
    values={x['stat']:x['value'] for x in env.lines}
    runes=[a for a in actions if a!='stop' and values.get(env._spec(a)['stat'],0)<env.targets.get(env._spec(a)['stat'],0)]
    if not runes:return 'stop'
    def score(rune):
        spec=env._spec(rune);rates=odds(env.lines,spec,level=env.level)
        success=(rates['sc']+rates['sn'])/100
        remaining=env.targets[spec['stat']]-next(x['value'] for x in env.lines if x['stat']==spec['stat'])
        progress=min(1,spec['gain']/max(1,remaining))
        exposure=max(0,spec['weight']-env.pool)/max(1,spec['weight'])
        return success*progress/(1+exposure)
    return max(runes,key=lambda a:(score(a),a))


def _choose(env,actions,q,general_policy=None):
    if valid_policy(general_policy):
        scores=score_actions(env.lines,env.pool,env.targets,env.level,actions,general_policy)
        if scores:return max(scores,key=lambda a:(scores[a],a))
    row=q.get(_key(env),{})
    known=[a for a in actions if a in row]
    return max(known,key=lambda a:(row[a],a)) if len(known)==len(actions) else _heuristic(env,actions)


def episode_seed(seed, domain, index):
    """Separate deterministic RNG namespaces, including across resumed runs."""
    return int.from_bytes(sha256(f'{seed}:{domain}:{index}'.encode()).digest(), 'big')


def policy_rank(policy):
    """Rank complete holdouts by conservative complete-jet success, never cost.

    All snapshots remain on disk. This is model selection on a fixed benchmark,
    not an independent claim of improvement over a previously selected model.
    """
    if policy.get('cancelled'):return (-1, 0.)
    evaluation=policy.get('evaluation',{})
    row=evaluation.get('learned',{}) if isinstance(evaluation,dict) else {}
    n,wins=row.get('episodes'),row.get('successes')
    expected=policy.get('configuration',{}).get('evaluation_episodes',n)
    if (type(n) is not int or n<1 or n!=expected or type(wins) is not int
            or not 0<=wins<=n):return (0, 0.)
    return (2 if advice_validation(evaluation)['eligible'] else 1, wilson(wins,n)[0])


def _load(root,signature):
    if not root.exists():return {},{},0,None
    paths=sorted(root.glob('*/policy.json'),key=lambda p:p.parent.name,reverse=True)
    best=None;best_rank=None
    for path in paths:
        try:
            data=json.loads(path.read_text(encoding='utf-8'))
            if data.get('signature')!=signature or data.get('policy_version')!=POLICY_VERSION:continue
            if data.get('general_policy') is not None and not valid_policy(data['general_policy']):continue
            q=data['q'];visits=data['visits'];n=data['episodes_total']
            if (type(n) is not int or n<0 or not isinstance(q,dict) or len(q)>MAX_STATES
                    or not isinstance(visits,dict)):continue
            all_runes={r for names in RUNE_CHOICES.values() for r in names}|{'stop'}
            if any(not isinstance(k,str) or not isinstance(row,dict) or
                   any(a not in all_runes or not finite_number(v) for a,v in row.items()) for k,row in q.items()):continue
            if any(type(v) is not int or v<0 for row in visits.values() for v in row.values()):continue
            rank=policy_rank(data)
            if best is None or rank>best_rank:
                best=(q,visits,n,path.parent.name);best_rank=rank
        except (OSError,ValueError,KeyError,TypeError,AttributeError):continue
    return best if best is not None else ({},{},0,None)


def _training_cursor(root, signature):
    """Advance randomness even when a rejected candidate is not resumed."""
    cursor=0
    for path in root.glob('*/policy.json'):
        try:
            data=json.loads(path.read_text(encoding='utf-8'))
            end=data.get('training_seed_end',data.get('episodes_total',0))
            if data.get('signature')==signature and type(end) is int and end>=0:
                cursor=max(cursor,end)
        except (OSError,ValueError,TypeError,AttributeError):
            continue
    return cursor


def _write(path,data):
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    temporary.replace(path)


def _search_policy(config,environment,q,hard_states,cursor,stopped,notify):
    """Balanced paired training tournament; no evaluation seed is consulted."""
    count=len(CANDIDATES)+1  # Retain the tabular learner if it wins or ties.
    trials=min(config.policy_search_episodes,config.episodes)//count
    if config.episodes<32 or trials<1:return None,dict(episodes=0,training_only=True)
    policies=[None]+[make_policy(p,episodes=trials*count) for p in CANDIDATES]
    rows=[];completed=0;replays=0
    replay_rng=Random(episode_seed(config.seed,'policy_search_replay',cursor))
    starts=[hard_states[replay_rng.randrange(len(hard_states))] if hard_states and i%4==3
            else None for i in range(trials)]
    for policy in policies:
        wins=0
        for index,start in enumerate(starts):
            if stopped():return None,dict(episodes=completed,training_only=True,cancelled=True)
            env=environment(episode_seed(config.seed,f'policy_search:{cursor}',index))
            if start is not None:
                env.lines,env.pool,env.steps=deepcopy(start);replays+=1
            while not env.closed and not stopped():
                env.step(_choose(env,_actions(env),q,policy))
            if stopped():return None,dict(episodes=completed,training_only=True,cancelled=True)
            wins+=int(env._complete(env.get_state()));completed+=1
            notify('policy_search',completed,trials*count)
        rows.append(dict(parameters=policy['parameters'] if policy else None,
                         episodes=trials,successes=wins))
    # Complete jets alone select the strategy; ties keep the tabular incumbent.
    winner=max(range(count),key=lambda i:rows[i]['successes'])
    return policies[winner],dict(episodes=completed,training_only=True,paired_seeds=True,
        seed_domain=f'policy_search:{cursor}',candidates=rows,selected=winner,
        targeted_episodes=replays,preserves_horizon=True,criterion='complete_jets_only')


def run_training(config,output_root,*,cancel=None,progress=None,empirical_db=None):
    if not isinstance(config,TrainingConfig):raise ValueError('Configuration invalide')
    from forgely_empirical_model import EmpiricalModel,load_empirical_model
    from forgely_data import DB_FILE
    model=load_empirical_model(empirical_db or DB_FILE).for_item(config.item_id) if config.use_real_observations else EmpiricalModel()
    revision=model.digest if model.sample_count else None
    if config.empirical_revision is not None and config.empirical_revision!=revision:
        raise ValueError('Les données réelles ont changé : nouvel entraînement requis.')
    config=replace(config,empirical_revision=revision)
    item,lines,targets,signature,spec=_prepare(config)
    root=Path(output_root)
    q,visits,prior,resumed=_load(root,signature) if config.resume else ({},{},0,None)
    cursor=_training_cursor(root,signature) if config.resume else 0
    run_id=datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')+f'-{item.item_id}-'+uuid4().hex[:6]
    directory=root/run_id;directory.mkdir(parents=True)
    if config.use_real_observations:model.save(directory/'empirical_snapshot.json')
    transition=model.transition(item.item_id) if model.sample_count else None
    started=perf_counter();runes=Counter();completed=successes=0
    def stopped():return cancel is not None and cancel.is_set()
    def notify(phase,count,total,**extra):
        if progress:progress(dict(phase=phase,completed=count,total=total,successes=successes,
                                 elapsed_seconds=perf_counter()-started,**extra))
    def environment(seed):
        return ForgemagingEnv(lines,config.initial_pool,targets,level=item.level,
                             max_steps=config.max_steps,seed=seed,allow_preparatory=config.allow_preparatory,transition_model=transition)
    hard_states=deque(maxlen=64)
    replayed=0
    rng=Random(episode_seed(config.seed,'exploration',cursor))
    notify('training',0,config.episodes)
    for index in range(config.episodes):
        if stopped():break
        seed=episode_seed(config.seed,'training',cursor+index)
        env=environment(seed)
        if hard_states and index%4==3:
            hard_lines,hard_pool,hard_steps=hard_states[rng.randrange(len(hard_states))]
            env=ForgemagingEnv(hard_lines,hard_pool,targets,level=item.level,
                              max_steps=config.max_steps,seed=seed,allow_preparatory=config.allow_preparatory,transition_model=transition)
            env.steps=hard_steps
            replayed+=1
        checkpoint=None;seen=0
        epsilon=max(.05,.30/(1+(prior+index)/1000))
        while not env.closed and not stopped():
            actions=_actions(env);key=_key(env)
            if key not in q and len(q)<MAX_STATES:
                # A positive prior guides exploration; it is never a measured probability.
                best=_heuristic(env,actions)
                q[key]={a:(.1 if a==best else 0.) for a in actions}
                visits[key]={}
            # Reservoir sampling captures short failures as well as long ones.
            # Only training trajectories enter the buffer; preserve the horizon.
            seen+=1
            if rng.randrange(seen)==0:
                checkpoint=(deepcopy(env.lines),env.pool,env.steps)
            action=rng.choice(actions) if rng.random()<epsilon else _choose(env,actions,q)
            _,reward,terminated,truncated,info=env.step(action)
            if action!='stop':runes[action]+=1
            if key in q:
                count=visits.setdefault(key,{}).get(action,0)+1;visits[key][action]=count
                next_actions=_actions(env)
                future=max((q.get(_key(env),{}).get(a,0.) for a in next_actions),default=0.)
                alpha=max(.05,count**-.6)
                old=q[key].get(action,0.)
                q[key][action]=old+alpha*(reward+(future if not (terminated or truncated) else 0)-old)
        if not stopped():
            completed+=1
            won=env._complete(env.get_state())
            successes+=int(won)
            if not won and checkpoint is not None:hard_states.append(checkpoint)
            notify('training',completed,config.episodes,runes=sum(runes.values()))
    cancelled=stopped()
    general_policy=None;search=dict(episodes=0,training_only=True)
    if not cancelled:
        general_policy,search=_search_policy(config,environment,q,hard_states,cursor,stopped,notify)
    cancelled=cancelled or stopped()
    evaluation={}
    if not cancelled:
        for name in ('learned','baseline'):
            count=won=attempts=stops=truncated_count=unseen=0;reward_total=0.
            for index in range(config.evaluation_episodes):
                if stopped():break
                env=environment(episode_seed(config.seed,'evaluation',index))
                while not env.closed and not stopped():
                    actions=_actions(env)
                    if name=='learned' and _key(env) not in q:unseen+=1
                    action=_choose(env,actions,q,general_policy) if name=='learned' else _heuristic(env,actions)
                    _,reward,_,truncated,info=env.step(action)
                    reward_total+=reward;attempts+=int(action!='stop')
                    stops+=int(action=='stop');truncated_count+=int(truncated)
                if stopped():break
                count+=1;won+=int(env._complete(env.get_state()))
                notify('evaluation',count,config.evaluation_episodes,policy=name)
            evaluation[name]=dict(episodes=count,successes=won,success_rate=won/count if count else None,
                mean_attempts=attempts/count if count else None,mean_reward=reward_total/count if count else None,
                stops=stops,truncated=truncated_count,
                unseen_states=unseen)
            if stopped():break
    cancelled=cancelled or stopped()
    direct_validation=advice_validation(evaluation,cancelled=cancelled)
    validation=policy_advice_validation(dict(evaluation=evaluation,cancelled=cancelled,general_policy=general_policy))
    if config.allow_preparatory:
        validation={**validation,'eligible':False,'reason':'experimental_preparatory_action_space_requires_live_selector_audit'}
    result=dict(run_id=run_id,signature=signature,item_id=item.item_id,item_name=item.identity_name,
        empirical_observations=model.sample_count,empirical_revision=revision,
        source='simulation',real_observations=0,automatically_enabled_in_live_advice=False,
        eligible_for_advice=validation['eligible'],advice_validation=validation,
        direct_policy_validation=direct_validation,simulation_contribution_only=True,
        model_version=MODEL_VERSION,policy_version=POLICY_VERSION,reward_version=REWARD_VERSION,
        episodes_completed=completed,prior_episodes=prior,episodes_total=prior+completed,
        training_seed_start=cursor,training_seed_end=cursor+completed,
        resumed_from=resumed,cancelled=cancelled,training_successes=successes,training_runes=dict(runes),
        configuration=spec,evaluation=evaluation,policy_search=search,
        evaluation_protocol=dict(version=1,seed=config.seed,seed_domain='evaluation',
            seed_derivation='sha256(seed:domain:index)',paired_seeds=True,
            training_replay=False,policy_frozen=True,selection_benchmark=True),
        curriculum={'replayed_episodes':replayed,'buffered_failures':len(hard_states),
                    'capacity':64,'evaluation_replay':False,'source':'simulation',
                    'sampling':'reservoir_per_failed_episode','preserves_horizon':True},
        elapsed_seconds=perf_counter()-started,states=len(q),
        limitations=['Résultats synthétiques du modèle local, pas des taux officiels du jeu.',
                     'État discrétisé : politique approximative, à comparer au témoin.',
                     'Banc fixe utilisé pour sélectionner la meilleure archive ; un audit avec une autre graine reste nécessaire pour établir la généralisation.'])
    _write(directory/'policy.json',dict(signature=signature,policy_version=POLICY_VERSION,
        model_version=MODEL_VERSION,reward_version=REWARD_VERSION,source='simulation',
        real_observations=0,eligible_for_advice=validation['eligible'],simulation_contribution_only=True,
        evaluation=evaluation,evaluation_protocol=result['evaluation_protocol'],
        advice_validation=validation,direct_policy_validation=direct_validation,cancelled=cancelled,
        item_id=item.item_id,configuration=spec,profile_lines=lines,general_policy=general_policy,
        episodes_total=prior+completed,training_seed_end=cursor+completed,q=q,visits=visits))
    selected=_load(root,signature)[3]
    result['selection']=dict(selected_run=selected,candidate_selected=selected==run_id,
        criterion='validation_then_wilson95_lower_bound',archives_preserved=True)
    _write(directory/'metrics.json',result)
    rows=''.join('<tr>'+''.join(f'<td>{escape(str(evaluation.get(name,{}).get(key,"—")))}</td>'
        for key in ('episodes','successes','success_rate','mean_attempts'))+'</tr>'
        for name in ('learned','baseline'))
    title=escape(item.identity_name)
    report=f'''<!doctype html><html lang="fr"><meta charset="utf-8"><title>Forgely — {title}</title>
    <style>body{{font:17px system-ui;max-width:900px;margin:40px auto;padding:20px;background:#f6f8f7;color:#16332b}}td,th{{padding:12px;border-bottom:1px solid #ccd}}table{{border-collapse:collapse}}</style>
    <h1>Entraînement Forgely : {title}</h1><p>{completed} sessions réalisées ; {prior} sessions antérieures compatibles.</p>
    <p>Cibles : {escape(str(targets))}. Jet initial : {escape(config.initial_preset)}. Reliquat : {config.initial_pool:g}.</p>
    <p>Évaluation indépendante : première ligne = politique apprise, seconde = témoin heuristique.</p>
    <table><tr><th>Sessions</th><th>Objectifs atteints</th><th>Proportion</th><th>Runes/session</th></tr>{rows}</table>
    <p>Recherche généralisable : {search['episodes']} trajectoires d'apprentissage supplémentaires, séparées de la vérification. Stratégie retenue : {'compacte généralisable' if general_policy else 'table de situations'}.</p>
    <p>Archive retenue : {escape(str(selected))}. Toutes les archives sont conservées.</p>
    <h2>Interprétation</h2><p>{escape(' '.join(result['limitations']))}</p>
    <p>La validation de la politique directe ne valide pas à elle seule le classement final du copilote. Une politique compacte reste inactive sans audit de ce sélecteur.</p>
    <p>Influence sur les conseils : {'autorisée après gain démontré sur le jet complet' if validation['eligible'] else 'inactive : amélioration non démontrée ou évaluation insuffisante'}. Priorité : atteindre toutes les cibles simultanément.</p>
    <p>Entrainement cible : {replayed} sessions reparties d'un etat difficile rencontre lors d'un echec. Evaluation : depart initial identique pour les deux strategies, sans reutiliser ces etats.</p>
    <p>Les politiques compatibles peuvent contribuer à la part simulation des conseils (40 %, contre 60 % de données réelles lorsque les deux sources sont exploitables). Elles ne remplacent pas seules les conseils. Zéro observation réelle est créée.</p>
    <p>{'Arrêt demandé : progression sauvegardée.' if cancelled else 'Entraînement terminé.'}</p></html>'''
    (directory/'rapport.html').write_text(report,encoding='utf-8')
    notify('done',completed,config.episodes,run_id=run_id)
    return result
