"""Classification and *hypothetical* FM simulation. Does not learn from synthetic trials.

natural_max comes from the item's *documented* natural stats, NEVER the OCR
current jet. A line not present in natural ranges is EXO, irrespective of stat.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
import random

WEIGHTS = {"Vitalité":.2,"Force":1.,"Intelligence":1.,"Chance":1.,"Agilité":1.,
           "Sagesse":3.,"Puissance":2.,"PA":100.,"PM":90.,"Portée":51.,
           "Invocations":30.,"Coups critiques":10.,"Soins":10.,"Initiative":.1}
EXTRA_CAP=101.0  # guide communautaire DOFUS, à confirmer selon version

@dataclass(frozen=True)
class LineState:
    characteristic:str
    current:float
    natural_max:float|None
    kind:str
    extra_weight:float|None


def classify(characteristic:str, current:float, natural_max:float|None, *, natural_present:bool|None):
    """Return nature/over/exo; unknown unless natural presence & max are known.

    current=0 on a missing natural stat does not make the *attempt* an exo;
    classify() describes the resulting or requested state, so pass proposed jet.
    """
    # Negative jets are real readings, never silently turned positive.
    weight=WEIGHTS.get(characteristic)
    if natural_present is None:kind='inconnu'
    elif not natural_present:kind='exo' if current!=0 else 'absent'
    elif natural_max is None:kind='inconnu'
    elif current>natural_max:kind='over'
    else:kind='naturel'
    extra=(max(0.,current-(natural_max or 0.)) if kind=='over' else abs(current) if kind=='exo' else 0.)
    return LineState(characteristic,current,natural_max,kind,extra*weight if weight is not None and kind!='inconnu' else None)


def classify_item(jets:Mapping[str,float], natural_max:Mapping[str,float], *, weights=WEIGHTS, complete_profile=True):
    """Absent from the verified base is exo, not automatically PA/PM/PO."""
    result=[]
    for stat,current in jets.items():
        present=stat in natural_max
        result.append(classify(stat,float(current),float(natural_max[stat]) if present else None,natural_present=(present if complete_profile or present else None)))
    return result


def extra_weight_total(states):
    if any(s.extra_weight is None for s in states):return None
    return sum(s.extra_weight for s in states)


def check_budget(jets,natural_max,cap=EXTRA_CAP):
    states=classify_item(jets,natural_max)
    total=extra_weight_total(states)
    if total is None:return {'valid':None,'total':None,'reason':'Poids inconnu pour au moins une caractéristique'}
    return {'valid':total <= cap+1e-8,'total':round(total,4),'cap':cap,
            'reason':'Plafond exo/over dépassé' if total>cap else 'Sous le plafond communautaire'}


def simulate_distribution(probabilities, n=10000, seed=42):
    """Only an illustration of explicit GIVEN probabilities, not DOFUS ground truth."""
    if not isinstance(n,int) or n<1 or n>1_000_000:raise ValueError('n invalide')
    if set(probabilities)!={'SC','SN','EC'} or any(not isinstance(p,(int,float)) or p<0 or p>1 for p in probabilities.values()):
        raise ValueError('Probabilites SC/SN/EC requises')
    if abs(sum(probabilities.values())-1)>1e-8:raise ValueError('La somme doit valoir 1')
    rng=random.Random(seed);counts={'SC':0,'SN':0,'EC':0};sc=probabilities['SC'];sn=probabilities['SN']
    for _ in range(n):
        x=rng.random();counts['SC' if x<sc else 'SN' if x<sc+sn else 'EC']+=1
    return {'source':'simulation_hypothetique_non_observation','n':n,'counts':counts,
            'caution':'NE PAS importer dans les statistiques de tentatives reelles.'}


def chance_independent_chain(chances):
    """Only if distinct events actually can coexist and probabilities are conditional as given."""
    p=1.
    for x in chances:
        if not 0<=x<=1:raise ValueError('Probabilite hors [0,1]')
        p*=x
    return p
