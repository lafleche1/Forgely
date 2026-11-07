"""Forgely strategy engine: explainable constraints and NO fabricated probability.
This engine is advisory, not a clone of the proprietary game algorithm.
Gameplay data are never generated or modified here.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
from forgely_probabilites import reference, empirical, baseline
from forgely_connaissances import advice_context

WEIGHT_PER_POINT = {
    'Vitalité':0.2,'Force':1,'Agilité':1,'Intelligence':1,'Chance':1,
    'Sagesse':3,'Puissance':2,'Initiative':0.1,'PA':100,'PM':90,
    'Portée':51,'Invocations':30,'Coups critiques':10,
    'Dommages critiques':5,'Soins':10,'Tacle':4,'Fuite':4,
}
RUNE_CHOICES = {
    'Vitalité':['Vi','Pa Vi','Ra Vi'],
    'Force':['Fo','Pa Fo','Ra Fo'],
    'Agilité':['Age','Pa Age','Ra Age'],
    'Intelligence':['Ine','Pa Ine','Ra Ine'],
    'Chance':['Cha','Pa Cha','Ra Cha'],
    'Sagesse':['Sa','Pa Sa','Ra Sa'],
    'Puissance':['Pui','Pa Pui','Ra Pui'],
    'Initiative':['Ini','Pa Ini','Ra Ini'],
    'Prospection':['Prospe','Pa Prospe'],
    'PA':['Ga Pa'],'PM':['Ga Pme'],'Portée':['Po'],
    'Invocations':['Invo'],'Coups critiques':['Cri'],
    'Soins':['So'],'Tacle':['Tac','Pa Tac'],'Fuite':['Fui','Pa Fui']
}
CAP=101

@dataclass(frozen=True)
class Proposal:
    rune:str|None
    kind:str
    summary:str
    explanation:str
    evidence:str
    estimates:dict|None=None
    sample:int=0


def pool_transition(pool, attempted_weight, lost_weight, outcome):
    """Bookkeeping approximation for single confirmed transition.
    If a smaller stat falls while existing pool absorbs the difference, pool
    decreases. When larger losses occur, surplus adds to the pool.
    No inference from mere 'EC' without confirmed stat losses.
    """
    if outcome not in ('SC','SN','EC'):raise ValueError('Résultat inconnu')
    if any(not isinstance(v,(int,float)) or v<0 for v in (pool,attempted_weight,lost_weight)):
        raise ValueError('Poids non négatifs requis')
    if outcome=='SC':
        if lost_weight:raise ValueError('SC contradictoire avec une perte de caractéristique')
        return float(pool)
    return round(max(0., pool+lost_weight-attempted_weight),4)


def classify(stat,current,proposed,natural_max:Mapping[str,float]|None):
    if natural_max is None: return 'inconnu'
    if stat not in natural_max: return 'exo' if proposed>0 else 'absent'  # Caller must supply a complete verified profile
    return 'over' if proposed>natural_max[stat] else 'fm_classique'


def extra_mass(jets:Mapping[str,float], natural_max:Mapping[str,float]|None):
    if natural_max is None:return None
    total=0.
    for stat,amount in jets.items():
        if stat not in WEIGHT_PER_POINT:return None
        total+=max(0.,amount-natural_max.get(stat,0))*WEIGHT_PER_POINT[stat]
    return round(total,5)


def candidates(jets,targets,natural_max=None,pool=None,counts_for=None):
    """Legal-ish candidate selection; descriptive not predictive.
    max values must be a complete verified natural profile to distinguish exos.
    """
    if not targets:return []
    if pool is None or pool<0: return []
    if not jets or any(stat not in jets for stat in targets):return []
    available=[]
    for stat,goal in targets.items():
        current=jets[stat]
        if current>=goal: continue
        for rune in RUNE_CHOICES.get(stat,()):
            ref=reference(rune)
            if ref.weight is None or ref.gain is None:continue
            proposed=current+ref.gain
            if proposed>goal:continue
            modified=dict(jets);modified[stat]=proposed
            weight=extra_mass(modified,natural_max)
            if weight is not None and weight>CAP:continue
            kind=classify(stat,current,proposed,natural_max)
            counts=counts_for(rune) if counts_for else None
            obs=empirical(counts) if counts is not None else None
            base=baseline(rune,exotic=kind=='exo',natural_stat=False if kind=='exo' else None)
            # Prefer progress and smaller risk to the rest of the item; this is a
            # heuristic ranking, never a calculated SC probability.
            remaining=goal-current
            progress=min(1.,ref.gain/remaining)
            exposure=min(1.,ref.weight/(pool+1))
            score=1.0*progress - 0.25*exposure - 0.04*ref.weight/100
            if kind in ('exo','over'): score-=0.3
            available.append((score,rune,stat,kind,ref,base,obs,weight,current,goal))
    return sorted(available,key=lambda x:x[0],reverse=True)


def advise(jets,targets,natural_max=None,pool=None,counts_for=None,after_fusion=False):
    if after_fusion:
        return Proposal(None,'bloqué','Jet à relire',
            'Une fusion vient d’être détectée. Attendre une lecture stable du nouveau jet avant une nouvelle recommandation.', 'aucune')
    if not targets:return Proposal(None,'bloqué','Aucun objectif','Définis le jet cible de cet équipement.','aucune')
    if pool is None:return Proposal(None,'bloqué','Reliquat à confirmer',
        'Aucune recommandation fiable tant que le reliquat n’est pas confirmé.', 'aucune')
    if any(s not in jets for s in targets):return Proposal(None,'bloqué','Jet incomplet',
        'Toutes les lignes ciblées doivent être lues et confirmées.', 'aucune')
    if all(jets[s]>=v for s,v in targets.items()):
        return Proposal(None,'atteint','Objectif atteint','Ne pose pas de rune supplémentaire sans nouvel objectif.','état confirmé')
    options=candidates(jets,targets,natural_max,pool,counts_for)
    if not options:return Proposal(None,'bloqué','Aucune rune sûre à proposer',
        'Objectif hors catalogue, poids incertain, ou plafond d’over/exo potentiellement dépassé.', 'aucune')
    score,rune,stat,kind,ref,base,obs,weight,current,goal=options[0]
    explanation=(f'{stat} : {current:g} → {goal:g}, prochain gain nominal +{ref.gain:g}; '
        f'poids de rune {ref.weight:g}, reliquat confirmé {pool:g}. '
        f'Type : {kind}. ')
    if natural_max is None:
        explanation+='Jets naturels non fournis : classification FM/over/exo et plafond 101 non vérifiables. '
    elif weight is not None:
        explanation+=f'Poids over/exo après tentative : {weight:g}/101 (repère communautaire). '
    n=obs['n'] if obs else 0
    if n:
        sc=obs['levels']['SC']['percentage']
        explanation+=f'{n} observations sur cette rune dans cet item ; SC observés {sc:.1f}% (non ajustés au jet/puits). '
    else:
        explanation+='Pas de fréquence locale comparable. '
    if base['SC'] is not None:
        explanation+=f'Repère communautaire conditionnel : SC {base["SC"]:g}%, SN {base["SN"]:g}%, EC {base["EC"]:g}%. '
    for note in advice_context(natural_max_known=natural_max is not None, pool_confirmed=True, kind=kind, rune_weight=ref.weight):
        explanation+=note+' '
    explanation+='Classement indicatif, pas une probabilité de réussite calculée ; aucune garantie de jet parfait.'
    return Proposal(rune,kind,f'À envisager : {rune}',explanation,
                    'observations locales + règle communautaire' if n else 'règles et heuristique',
                    {'observed':obs,'benchmark':base},n)
