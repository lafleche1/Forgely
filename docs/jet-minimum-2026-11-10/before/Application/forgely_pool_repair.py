"""Nominal useful rune budgets, recalculated after every observed result."""
from decimal import Decimal, ROUND_FLOOR
from functools import lru_cache
from math import gcd


def pool_repair_plan(rows,pool,natural=None):
    repairs=tuple((r[1],r[2],r[4].gain,r[4].weight,min(r[9],(natural or {}).get(r[2],r[9]))-r[8])
                  for r in rows if r[3]=='fm_classique' and r[9]>r[8]
                  and r[4].weight>0 and r[4].gain>0 and r[4].weight<=pool
                  and r[8]<min(r[9],(natural or {}).get(r[2],r[9])))
    return _plan(repairs,str(pool))


@lru_cache(maxsize=128)
def _plan(repairs,pool):
    if not repairs:return (),0
    weights={r[0]:int(Decimal(str(r[3]))*1000) for r in repairs}
    priority={r[0]:i for i,r in enumerate(repairs)}
    def preference(path):
        return len(path),tuple(sorted(priority[r] for r in path))
    quantum=0
    for w in weights.values():quantum=gcd(quantum,w)
    budget=int((Decimal(pool)*1000/quantum).to_integral_value(rounding=ROUND_FLOOR))
    groups={}
    for rune,stat,gain,weight,missing in repairs:
        groups.setdefault(stat,[]).append((rune,Decimal(str(gain)),weights[rune]//quantum,Decimal(str(missing))))
    states={0:()}
    for group in groups.values():
        # Build attainable gains for this line, never crossing its target.
        local={(Decimal(0),0):()}
        for rune,gain,weight,missing in group:
            additions=dict(local)
            for (value,cost),path in local.items():
                count=min(int((missing-value)//gain),(budget-cost)//weight)
                for n in range(1,count+1):
                    key=(value+n*gain,cost+n*weight)
                    candidate=path+(rune,)*n
                    if key not in additions or preference(candidate)<preference(additions[key]):additions[key]=candidate
            local=additions
        next_states={}
        for cost,path in states.items():
            for (_,extra),suffix in local.items():
                total=cost+extra
                if total>budget:continue
                candidate=path+suffix
                if total not in next_states or preference(candidate)<preference(next_states[total]):next_states[total]=candidate
        states=next_states
    spent=max(states)
    return tuple(sorted(states[spent],key=priority.get)),float(Decimal(spent*quantum)/1000)
