"""Simulateur expérimental de progression d'une caractéristique.

Hypothèses fournies par l'utilisateur : probabilités fixes SC/SN/EC.
SC ajoute le gain ; SN ajoute le gain en consommant du puits ; EC consomme du
puits. Ne modélise PAS la perte d'autres caractéristiques, les limites d'exo,
les règles précises de puits, ni les probabilités dépendant du jet.
Aucun résultat n'est enregistré parmi les observations réelles.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import ceil
from random import Random
from statistics import mean, median
from forgely_probabilites import reference

@dataclass(frozen=True)
class SimResult:
    trials: int
    completed: int
    completion_rate: float
    mean_attempts: float | None
    median_attempts: float | None
    mean_cost: float
    mean_pool_left: float
    sc: int
    sn: int
    ec: int
    truncated: int
    estimated: bool = True


def simulate_target(rune, current, target, pool, price, sc, sn, ec, *, trials=2000,
                    max_attempts=100, seed=19):
    """Run independent hypothetical sessions; fixed probabilities are inputs.

    Pool is treated as a budget for SN/EC for illustration, never negative.
    Once insufficient, the session is stopped. This is a deliberately
    conservative pedagogical simplification, not DOFUS' real mechanics.
    """
    ref=reference(rune)
    if ref.gain is None or ref.weight is None:
        raise ValueError('Gain ou poids de cette rune non documenté')
    if not all(isinstance(x,(int,float)) and not isinstance(x,bool) for x in (current,target,pool,price,sc,sn,ec)):
        raise ValueError('Paramètres numériques requis')
    if current<0 or target<=current or pool<0 or price<0:
        raise ValueError('Jet, cible, puits ou prix invalides')
    if min(sc,sn,ec)<0 or max(sc,sn,ec)>1 or abs(sc+sn+ec-1)>1e-8:
        raise ValueError('SC + SN + EC doivent totaliser 100 %')
    if not isinstance(trials,int) or not 1<=trials<=50000:
        raise ValueError('Nombre de simulations entre 1 et 50 000')
    if not isinstance(max_attempts,int) or not 1<=max_attempts<=10000:
        raise ValueError('Limite d’essais entre 1 et 10 000')
    rng=Random(seed)
    completed=[];costs=[];pools=[];counts={'SC':0,'SN':0,'EC':0};truncated=0
    for _ in range(trials):
        jet=float(current);remaining=float(pool);attempts=0
        while jet<target and attempts<max_attempts:
            outcome=rng.random()
            if outcome<sc:
                jet+=ref.gain;counts['SC']+=1
            elif outcome<sc+sn:
                if remaining<ref.weight:break
                remaining-=ref.weight;jet+=ref.gain;counts['SN']+=1
            else:
                if remaining<ref.weight:break
                remaining-=ref.weight;counts['EC']+=1
            attempts+=1
        if jet>=target:completed.append(attempts)
        else:truncated+=1
        costs.append(attempts*price);pools.append(remaining)
    return SimResult(trials,len(completed),len(completed)/trials,
        mean(completed) if completed else None,median(completed) if completed else None,
        mean(costs),mean(pools),counts['SC'],counts['SN'],counts['EC'],truncated)
