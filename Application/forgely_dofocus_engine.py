"""Offline numerical model of the public Dofocus simulator, analysed 2026-11-07.

Independent Python implementation of its observed mathematical mechanisms.
Source fingerprint and scope: docs/dofocus-algorithm-findings.md. This models
Dofocus, not a verified Ankama algorithm. No network, game input or database IO.
"""
from math import ceil,exp,floor,isfinite
from random import Random

MODEL_VERSION='dofocus-2026-11-07-6a559153678e'
EPS=1e-9
SPECIAL='@special'


def _number(x):return type(x) in (int,float) and isfinite(x)
def _bounded(line):return line.get('min') is not None and line.get('max') is not None
def _limits(line):return min(line['min'],line['max']),max(line['min'],line['max'])
def _round(x):return floor(x*100+.5)/100


def _validate(lines,rune,level):
    if type(level) is not int or not 1<=level<=200:raise ValueError('Niveau invalide')
    if not isinstance(lines,(list,tuple)) or len(lines)>64:raise ValueError('Lignes invalides')
    seen=set()
    for line in lines:
        if (not isinstance(line,dict) or not isinstance(line.get('stat'),str)
                or not line['stat'] or line['stat'] in seen
                or not _number(line.get('value')) or abs(line['value'])>30000
                or not _number(line.get('weight')) or not .05<=line['weight']<=100):
            raise ValueError('Caractéristique invalide')
        seen.add(line['stat'])
        lo,hi=line.get('min'),line.get('max')
        if (lo is None)!=(hi is None) or (lo is not None and
                (not _number(lo) or not _number(hi) or max(abs(lo),abs(hi))>30000)):
            raise ValueError('Bornes invalides')
    if (not isinstance(rune,dict) or not isinstance(rune.get('stat'),str)
            or not rune['stat'] or not _number(rune.get('gain')) or not 0<rune['gain']<=30000
            or not _number(rune.get('weight')) or not 0<rune['weight']<=101):
        raise ValueError('Rune invalide')


def _quality(lines,excluded):
    current=maximum=0.
    for index,line in enumerate(lines):
        if index==excluded or not _bounded(line):continue
        high=_limits(line)[1]
        if high<0:continue
        current+=line['weight']*min(max(0,line['value']),high)
        maximum+=line['weight']*high
    return current/maximum if maximum>0 else 0.


def _extra_mass(lines):
    total=0.
    for line in lines:
        value,weight=line['value'],line['weight']
        if value<=0:continue
        if not _bounded(line):total+=value*weight
        else:
            high=_limits(line)[1]
            total+=value*weight-high*weight*.5 if high<0 else max(0,value-high)*weight
    return total


def odds(lines,rune,*,level=200):
    _validate(lines,rune,level)
    target=next((i for i,line in enumerate(lines) if line['stat']==rune['stat']),-1)
    line=lines[target] if target>=0 else None
    value=line['value'] if line else 0
    gain=rune['gain'];unit=rune['weight']/gain
    limit=1 if rune['stat']==SPECIAL else max(_limits(line)[1] if line and _bounded(line) else 0,
        floor(101/unit+EPS))
    if value+gain>limit:return {'blocked':'line-cap','limit':limit}
    changed=[dict(x) for x in lines]
    new_line={**line,'value':value+gain} if line else {'stat':rune['stat'],'value':gain,'min':None,'max':None,'weight':unit}
    if target>=0:changed[target]=new_line
    else:changed.append(new_line)
    if _extra_mass(changed)>101+EPS:
        return {'blocked':'item-cap','limit':limit,'load':_round(_extra_mass(lines))}
    quality=_quality(lines,target)
    if line is None or not _bounded(line) or rune['stat']==SPECIAL:
        if rune['stat'] in ('PA','PM','Portée'):
            result={'sc':1.5,'sn':0,'ec':98.5,'estimated':False}
        elif rune['stat']==SPECIAL:result={'sc':1,'sn':34,'ec':65,'estimated':True}
        else:
            density=(value+gain)*unit
            base=57 if density<=2 else 57-(density-2)*38/13 if density<=15 else 19-(density-15)*1.9 if density<25 else 0
            if level<100 and density<=50:base=max(base,8+(3-8)*(density-25)/25)
            if base<=0:result={'sc':1,'sn':0,'ec':99,'estimated':True}
            else:
                adjusted=max(1,.077*base)+.923*base
                logistic=adjusted/(100-adjusted)*exp(1.2*(.85-quality))
                success=max(1,100*logistic/(1+logistic))
                critical=max(1,.077*success)
                result={'sc':critical,'sn':success-critical,'ec':100-success,'estimated':True}
        return {**result,'regime':'exo','quality':quality,'gain':gain,'limit':limit}
    low,high=_limits(line)
    over=value+gain>high
    if over:
        other=_extra_mass([x for i,x in enumerate(lines) if i!=target])
        load=_extra_mass([new_line]) if high<0 else (value+gain)*unit
        if load+other>101+EPS:
            return {'blocked':'item-cap','limit':limit,'load':_round(max(0,value)*unit+other)}
    fixed=low==high
    position=1 if fixed else (value+gain-low)/(high-low)
    exo_pa=any(x['stat'] in ('PA','PM') and not _bounded(x) and x['value']>0 for x in lines)
    quality=1 if exo_pa else quality
    over_weight=(value+gain-high)*unit if over else 0
    ratio=value/gain
    difficulty=5+4*rune['weight']*max(0,ratio-14)+60*quality**12
    if over:difficulty+=65+4*max(0,over_weight)
    elif not fixed and position>=.8-EPS:difficulty+=45
    difficulty-=(20*max(0,1.1-quality) if level<170 else 0)+(15 if level<100 else 0)
    critical=max(2,(100-difficulty)/2)
    neutral=max(5,40-.375*(difficulty-100)) if over else min(50,100-critical) if difficulty<=100 else 50-.375*(difficulty-100)
    neutral=min(max(neutral,0),100-critical)
    result={'sc':critical,'sn':neutral,'ec':100-critical-neutral,
        'regime':'over' if over else 'repass' if fixed else 'step' if position>=.8-EPS else 'normal',
        'difficulty':difficulty,'position':position,'quality':quality,'gain':gain,'limit':limit,
        'overWeight':over_weight,'ratio':ratio,'power':rune['weight']}
    if value+gain<0:result['half']=True
    if exo_pa:result['exoPa']=True
    return result


def _losses(lines,target,charge,pool,random,failure):
    remaining=charge
    changes={}
    def lose(index,amount):
        lines[index]['value']-=amount
        changes[index]=changes.get(index,0)-amount
    def eligible(index):return index!=target or failure and lines[index]['value']>0
    def surplus(index):
        line=lines[index]
        return line['value']>(_limits(line)[1] if _bounded(line) else 0)
    def extra(index,amount,required):
        line=lines[index]
        return int(index!=target and _bounded(line) and line['weight']<1 and amount==required
            and line['value']>amount and random()<.29)
    def absorb(index,probability):
        nonlocal remaining
        line=lines[index]
        unit=line['weight']*(.5 if line['value']<0 else 1)
        if random()>=min(1,.75*max(0,charge/unit)**.85)*probability:return
        available=line['value'] if line['value']>0 else line['value']-_limits(line)[0]
        required=max(1,ceil(remaining/unit-EPS))
        amount=min(available,required)
        if line['value']>0:amount+=extra(index,amount,required)
        lose(index,amount);remaining-=amount*unit
    exos=[i for i in range(len(lines)) if i!=target and surplus(i)]
    for i in range(len(exos)-1,0,-1):
        j=floor(random()*(i+1));exos[i],exos[j]=exos[j],exos[i]
    for index in exos:
        if remaining<=EPS:break
        absorb(index,1)
    if remaining>EPS and pool>0:
        consumed=min(pool,remaining);pool-=consumed;remaining-=consumed
    if remaining>EPS and target>=0 and eligible(target) and surplus(target):absorb(target,1/3)
    while remaining>EPS:
        choices=[i for i in range(len(lines)) if eligible(i) and _bounded(lines[i]) and lines[i]['value']>0]
        if not choices:break
        weights=[min(1,charge/lines[i]['weight'])*(1/60 if i==target else 1) for i in choices]
        draw=random()*sum(weights);index=choices[-1]
        for candidate,weight in zip(choices,weights):
            draw-=weight
            if draw<0:index=candidate;break
        line=lines[index]
        required=min(line['value'],max(1,ceil(remaining/line['weight']-EPS)))
        amount=1 if required==1 else 1+floor(random()*required)
        amount+=extra(index,amount,required)
        lose(index,amount);remaining-=amount*line['weight']
    if remaining>EPS and target>=0 and lines[target]['value']>0:
        line=lines[target];amount=min(line['value'],max(1,ceil(remaining/line['weight']-EPS)))
        lose(target,amount);remaining-=amount*line['weight']
    if remaining<-EPS:pool-=remaining
    return _round(min(100,max(0,pool))),changes


def attempt(lines,rune,pool,*,level=200,rng=None,probabilities=None):
    if not _number(pool) or not 0<=pool<=30000:raise ValueError('Puits invalide')
    result_odds=odds(lines,rune,level=level)
    new_lines=[dict(x) for x in lines]
    if result_odds.get('blocked'):
        return {'lines':new_lines,'pool':pool,'outcome':None,'odds':result_odds,'changes':{}}
    if probabilities is not None:
        values=[probabilities.get(k) for k in ('sc','sn','ec')]
        if any(not _number(v) or not 0<=v<=100 for v in values) or abs(sum(values)-100)>1e-7:
            raise ValueError('Distribution invalide')
        result_odds={**result_odds,**{k:probabilities[k] for k in ('sc','sn','ec')}}
        if 'empirical_n' in probabilities:
            result_odds.update(empirical_n=probabilities['empirical_n'],
                               empirical_weight=probabilities['empirical_weight'])
    generator=rng or Random()
    def random():
        value=generator.random()
        if not _number(value) or not 0<=value<1:raise ValueError('Tirage invalide')
        return value
    draw=random()*100
    outcome='SC' if draw<result_odds['sc'] else 'SN' if draw<result_odds['sc']+result_odds['sn'] else 'EC'
    target=next((i for i,x in enumerate(new_lines) if x['stat']==rune['stat']),-1)
    changes={}
    if outcome!='EC':
        if target<0:
            target=len(new_lines)
            new_lines.append({'stat':rune['stat'],'value':0,'min':None,'max':None,'weight':rune['weight']/rune['gain']})
        new_lines[target]['value']+=rune['gain'];changes[target]=rune['gain']
    new_pool=pool
    if outcome!='SC':
        half=target>=0 and target<len(lines) and lines[target]['value']+rune['gain']<0
        new_pool,lost=_losses(new_lines,target,rune['weight']*(.5 if half else 1),pool,random,outcome=='EC')
        for index,amount in lost.items():changes[index]=changes.get(index,0)+amount
    return {'lines':new_lines,'pool':new_pool,'pool_delta':_round(new_pool-pool),
        'outcome':outcome,'odds':result_odds,'changes':{new_lines[i]['stat']:v for i,v in changes.items() if v}}
