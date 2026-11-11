"""Nominal useful rune budgets, recalculated after every observed result."""
from decimal import Decimal, ROUND_FLOOR, ROUND_CEILING
from functools import lru_cache
from math import gcd


def pool_repair_plan(rows,pool,natural=None):
    repairs=tuple((r[1],r[2],r[4].gain,r[4].weight,min(r[9],(natural or {}).get(r[2],r[9]))-r[8],
                   (natural or {}).get(r[2],r[9])-r[8])
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
    for rune,stat,gain,weight,missing,capacity in repairs:
        groups.setdefault(stat,[]).append((rune,Decimal(str(gain)),weights[rune]//quantum,
                                          Decimal(str(missing)),Decimal(str(capacity))))
    states={0:(Decimal(0),())}
    for group in groups.values():
        # Stop once the minimum is reached; only the natural maximum is a cap.
        local={(Decimal(0),0):()}
        for rune,gain,weight,missing,capacity in group:
            additions=dict(local)
            for (value,cost),path in local.items():
                count=min(max(0,int(((missing-value)/gain).to_integral_value(rounding=ROUND_CEILING))),
                          int((capacity-value)//gain),(budget-cost)//weight)
                for n in range(1,count+1):
                    key=(value+n*gain,cost+n*weight)
                    candidate=path+(rune,)*n
                    if key not in additions or preference(candidate)<preference(additions[key]):additions[key]=candidate
            local=additions
        next_states={}
        for cost,(progress,path) in states.items():
            for (value,extra),suffix in local.items():
                total=cost+extra
                if total>budget:continue
                candidate=path+suffix
                # Useful weighted deficit only: crossing the minimum is valid,
                # but surplus cannot masquerade as extra repaired target mass.
                _,gain,weight,missing,_=group[0]
                useful=progress+min(value,missing)*weight/gain
                previous=next_states.get(total)
                if previous is None or (-useful,preference(candidate))<(-previous[0],preference(previous[1])):
                    next_states[total]=(useful,candidate)
        states=next_states
    spent=min(states,key=lambda cost:(-states[cost][0],preference(states[cost][1]),cost))
    return tuple(sorted(states[spent][1],key=priority.get)),float(Decimal(spent*quantum)/1000)
