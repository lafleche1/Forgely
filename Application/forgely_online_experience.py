"""Bounded local experience adjusts a heuristic, never a success probability.

Only attributed, stable pre/post attempts belong here. Exact empirical rates
remain separate; neighbours cannot contribute to their counts or percentages.
"""
from collections import deque
from copy import deepcopy
from forgely_context import normalize_snapshot,snapshot_diff
from forgely_dofocus import reference,normalise_jet,canonical_stat
from forgely_rules import RUNE_CHOICES,WEIGHTS,finite_number
from forgely_items import key_for


class OnlineExperience:
    def __init__(self,max_samples=4096):
        self.samples=deque(maxlen=max_samples)
        self.last_id=0

    def observe(self,event_id,item,rune,outcome,before,after):
        if type(event_id) is not int or event_id<=self.last_id:return False
        self.last_id=event_id
        if not isinstance(before,dict) or not isinstance(after,dict):return False
        start=normalize_snapshot(before.get('jet'),before.get('pool'))
        end=normalize_snapshot(after.get('jet'),after.get('pool'))
        if start is None or end is None:return False
        start['jet']=normalise_jet(start['jet']);end['jet']=normalise_jet(end['jet'])
        if not start['jet'] or not end['jet']:return False
        delta=snapshot_diff(start,end)
        stat=next((s for s,rs in RUNE_CHOICES.items() if rune in rs),None)
        ref=reference(rune)
        if (not isinstance(item,str) or not item or outcome not in ('SC','SN','EC')
                or delta is None or stat not in start['jet'] or not ref.gain or not ref.weight
                or any(s not in WEIGHTS for s in start['jet'])):return False
        gain=end['jet'][stat]-start['jet'][stat]
        if any(s!=stat and v>0 for s,v in delta['changes'].items()):return False
        if gain>ref.gain or (outcome=='EC' and gain>0):return False
        if outcome in ('SC','SN') and gain<=0:return False
        if outcome=='SC' and (abs(gain-ref.gain)>1e-6 or delta['pool_delta']!=0
                or any(v<0 for v in delta['changes'].values())):return False
        self.samples.append((key_for(item),rune,deepcopy(start),deepcopy(end)))
        return True

    def evaluate(self,item,rune,jet,pool,targets,bounds):
        current=normalize_snapshot(jet,pool)
        if current is None or not isinstance(bounds,dict) or not bounds:return None
        jets=normalise_jet(jet);goals=normalise_jet(targets)
        try:
            maxima={canonical_stat(s):pair[1] if isinstance(pair,(tuple,list)) else pair
                    for s,pair in bounds.items()}
        except (IndexError,TypeError):return None
        if (not jets or not goals or not set(maxima).issubset(jets)
                or not set(goals).issubset(jets)
                or any(s not in WEIGHTS for s in jets)
                or any(not finite_number(v) for v in maxima.values())):return None
        ref=reference(rune)
        if not ref.weight or not ref.gain:return None
        numerator=weight=0.;n=exact=0
        identity=key_for(item)
        for sample_item,sample_rune,before,after in self.samples:
            if sample_item!=identity or sample_rune!=rune or set(before['jet'])!=set(jets):continue
            old_pool=before['pool']
            if ((old_pool==0)!=(pool==0) or (old_pool>=ref.weight)!=(pool>=ref.weight)
                    or abs(old_pool-pool)>max(1,ref.weight*.2)):continue
            distance=0.;compatible=True
            for stat,value in jets.items():
                old=before['jet'][stat]
                maximum=maxima.get(stat)
                if maximum is None:
                    compatible=old==value
                else:
                    compatible=((old>maximum)==(value>maximum)
                        and abs(old-value)<=max(1,abs(maximum)*.05)
                        and (WEIGHTS[stat]<20 or old==value))
                if not compatible:break
                distance+=abs(old-value)*WEIGHTS[stat]
            if not compatible:continue
            scale=sum(max(1,abs(maxima.get(s,jets[s])))*WEIGHTS[s] for s in jets)
            if distance/scale>.025:continue
            similarity=1/(1+50*distance/scale+abs(old_pool-pool)/max(1,ref.weight))
            # Re-evaluate the observed effect against TODAY's target. A lost
            # point above target is harmless until it crosses that target.
            progress=damage=0.
            for stat,target in goals.items():
                old=before['jet'][stat];new=after['jet'][stat]
                change=(max(0,target-old)-max(0,target-new))*WEIGHTS[stat]
                progress+=max(0,change);damage+=max(0,-change)
            spent=max(0,old_pool-after['pool'])
            reward=max(-1,min(1,(progress-damage-.1*spent)/ref.weight))
            numerator+=similarity*(reward-.5);weight+=similarity;n+=1
            exact+=int(before['jet']==jets and old_pool==pool)
        if not n:return None
        factor=max(.85,min(1.1,1+.2*numerator/(20+weight)))
        return {'n':n,'exact':exact,'effective_n':round(weight,3),'factor':factor,
                'kind':'experience_locale_indicative'}
