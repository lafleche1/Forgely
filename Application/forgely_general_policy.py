"""Compact action policies selected on training trajectories, not probabilities.

No player data, currency, file IO or random draws at inference time.
"""
from math import isfinite
from forgely_dofocus import RUNE_CHOICES, WEIGHT_PER_POINT, reference
from forgely_dofocus_engine import odds

GENERAL_VERSION='mass-deficit-search-1'
CANDIDATES=((1.,1.,1.,0.),(1.,0.,1.,0.),(1.,.5,1.,0.),(.5,0.,1.,0.),
            (1.,0.,3.,1.),(1.,.5,3.,1.),(1.,0.,0.,1.),(1.,0.,1.,2.))
RUNE_SPECS={r:{'stat':s,'gain':reference(r).gain,'weight':reference(r).weight}
            for s,runes in RUNE_CHOICES.items() for r in runes}


def valid_policy(policy):
    if not isinstance(policy,dict) or policy.get('kind')!=GENERAL_VERSION:return False
    p=policy.get('parameters');n=policy.get('episodes')
    return (isinstance(p,(list,tuple)) and len(p)==4 and type(n) is int and 1<=n<=8192
        and policy.get('source')=='simulation' and policy.get('real_observations')==0
        and all(type(x) in (int,float) and isfinite(x) and 0<=x<=4 for x in p))


def make_policy(parameters, *, episodes):
    policy=dict(kind=GENERAL_VERSION,parameters=list(parameters),episodes=episodes,
                source='simulation',real_observations=0)
    if not valid_policy(policy):raise ValueError('Paramètres de politique invalides')
    return policy


def score_actions(lines,pool,targets,level,actions,policy):
    """Positive ranking utilities; never success probabilities or Q rewards."""
    if not valid_policy(policy):return {}
    a,b,risk,surplus=policy['parameters']
    values={x['stat']:x['value'] for x in lines}
    output={}
    for rune in actions:
        if rune=='stop' or rune not in RUNE_SPECS:continue
        spec=RUNE_SPECS[rune];stat=spec['stat']
        remaining=targets.get(stat,values.get(stat,0))-values.get(stat,0)
        if remaining<=0:continue
        rates=odds(lines,spec,level=level)
        if rates.get('blocked'):continue
        unit=spec['weight']/spec['gain']
        progress=min(spec['gain'],remaining)*unit
        output[rune]=((rates['sc']+rates['sn'])/100*progress**a/(remaining*unit)**b
            /(1+risk*max(0,spec['weight']-pool)/spec['weight'])
            /(1+surplus*max(0,spec['gain']-remaining)/remaining))
    return output


def state_scores(state,policy):
    from forgely_rl import ForgemagingEnv
    features=dict(zip(state['features'],state['vector']))
    lines=[dict(stat=s,value=x['value'],min=x.get('min'),max=x.get('max'),weight=WEIGHT_PER_POINT[s])
           for s,x in state['stats'].items()]
    targets={s:x['target'] for s,x in state['stats'].items() if x.get('target') is not None}
    env=ForgemagingEnv(lines,state['pool'],targets,level=round(features['level']*200),
                        stock=state.get('stock'),max_steps=1)
    return score_actions(lines,env.pool,targets,env.level,env.get_valid_actions(),policy)
