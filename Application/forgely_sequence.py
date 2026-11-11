"""Bounded virtual continuations, never observations or official probabilities."""
from copy import deepcopy
from random import Random
from math import isfinite
from forgely_dofocus import WEIGHT_PER_POINT, reference, RUNE_CHOICES
from forgely_dofocus_engine import attempt, odds


def target_value(jet, targets):
    deficit=sum(max(0,goal-jet.get(stat,0))*WEIGHT_PER_POINT[stat] for stat,goal in targets.items())
    return 1. if deficit==0 else .1/(1+deficit)


def rollout_value(completed,trials,total_value):
    # One additional complete target must dominate every partial-only gain.
    return completed/trials+max(0.,total_value-completed)/(10*trials*trials)


def options(lines, pool, targets,*,level=200):
    # Local import avoids a module cycle. No database lookup without item identity.
    from forgely_decision import candidates
    jet={line['stat']:line['value'] for line in lines}
    maxima={line['stat']:line['max'] for line in lines if line.get('max') is not None}
    rows=candidates(jet,targets,maxima,pool)
    return [row for row in rows if not odds(lines,{'stat':row[2],'gain':row[4].gain,'weight':row[4].weight},level=level).get('blocked')]


def calibrated_probabilities(base,record):
    from forgely_decision import contextual_measurement
    measured=contextual_measurement(record)
    if measured is None or measured['quality']!='local_verified' or record.get('verified') is not True:return None
    values=[base.get(k) for k in ('sc','sn','ec')]
    if any(not isinstance(v,(int,float)) or not isfinite(v) or not 0<=v<=100 for v in values) or abs(sum(values)-100)>1e-7:return None
    from forgely_fm_model import calibrate_prediction
    corrected=calibrate_prediction({k.upper():base[k] for k in ('sc','sn','ec')},record)
    reliability=corrected['real_weight']
    result={k:corrected[k.upper()] for k in ('sc','sn','ec')}
    expected=(base['sc']+base['sn'])/100
    lo,hi=measured['success_ci95']
    result.update(weights={'simulation':1-reliability,'real':reliability},reliability=reliability,
                  observations=measured['n'],discordant=not lo<=expected<=hi,
                  quality=measured['quality'])
    return result


def plan_sequences(lines,pool,targets,*,level,seed,trials=16,horizon=8,cancelled=lambda:False,root_calibration=None,continuation=None,transition=None):
    if type(trials) is not int or not 16<=trials<=256 or type(horizon) is not int or not 1<=horizon<=32:
        raise ValueError('Invalid search budget')
    if not targets or any(s not in WEIGHT_PER_POINT or not isinstance(v,(int,float)) or not isfinite(v) for s,v in targets.items()):
        raise ValueError('Invalid targets')
    first=options(lines,pool,targets,level=level)
    output={}
    for row in first:
        rune=row[1];completed=steps_total=0;value=0.
        for trial in range(trials):
            if cancelled():return None
            current=deepcopy(lines);remaining=pool;rng=Random(seed+trial)
            action=rune;used=0
            for step in range(horizon):
                if cancelled():return None
                stat=next(s for s,rs in RUNE_CHOICES.items() if action in rs)
                ref=reference(action)
                result=(transition or attempt)(current,{'stat':stat,'gain':ref.gain,'weight':ref.weight},remaining,level=level,rng=rng,
                               probabilities=(root_calibration or {}).get(rune) if step==0 else None)
                current=result['lines'];remaining=result['pool'];used+=1
                jet={line['stat']:line['value'] for line in current}
                if target_value(jet,targets)==1:break
                choices=options(current,remaining,targets,level=level)
                if not choices:break
                action=continuation(current,remaining,choices) if continuation else choices[0][1]
                if action not in {row[1] for row in choices}:action=choices[0][1]
            final=target_value({line['stat']:line['value'] for line in current},targets)
            completed+=int(final==1);value+=final;steps_total+=used
        output[rune]={'kind':'sequence_rollouts','trials':trials,'horizon':horizon,
                      'completed':completed,'value':rollout_value(completed,trials,value),'mean_steps':steps_total/trials,
                      'real_observations':0,'source':'simulation',
                      'calibration':deepcopy((root_calibration or {}).get(rune))}
    return output


def validate_choice(planned,holdout,baseline,*,selected=None):
    selected=selected or min(planned,key=lambda r:(-planned[r]['value'],planned[r]['mean_steps'],r))
    new,old=holdout[selected],holdout[baseline]
    accepted=new['completed']>=old['completed'] and new['value']>=old['value']
    return {'selected':selected,'baseline':baseline,'accepted':accepted,
            'reason':'no_observed_regression' if accepted else 'holdout_regression',
            'statistical_superiority':False}
