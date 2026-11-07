"""Transparent advisory engine. Never equates past failures with increased next-roll luck.

Only comparable observations (same item & rune) enter empirical rates; incomplete
context means these are descriptive frequencies, not causal probabilities.
"""
from dataclasses import dataclass
from math import sqrt
from forgely_plan import STATS
from forgely_probabilites import reference
from forgely_huzounet import priority_note

INCREMENTS = {
 'Vitalité': (5, 15, 50), 'Force': (1, 3, 10),
 'Intelligence': (1, 3, 10), 'Chance': (1, 3, 10), 'Agilité': (1, 3, 10),
 'Sagesse': (1, 3, 10), 'Puissance': (1, 3, 10),
 'Initiative': (10, 30, 100), 'Prospection': (1, 3),
 'PA': (1,), 'PM': (1,), 'Portée': (1,),
}

@dataclass(frozen=True)
class Advice:
    rune: str | None
    headline: str
    details: str
    confidence: str
    rates: dict | None = None
    sample: int = 0


def wilson_interval(count, total, z=1.96):
    if total == 0:return (0., 1.)
    p=count/total
    d=1+z*z/total
    c=(p+z*z/(2*total))/d
    r=(z/d)*sqrt(p*(1-p)/total+z*z/(4*total*total))
    return (max(0.,c-r),min(1.,c+r))


def describe_observed(counts):
    n=sum(counts.get(k,0) for k in ('SC','SN','EC'))
    if not n: return None,0
    return ({k:{'rate':counts.get(k,0)/n,'ci95':wilson_interval(counts.get(k,0),n)}
             for k in ('SC','SN','EC')},n)


def recommend(plan, puits=None, jets_confirmed=False, records=None, last_rune=None, last_results=()):
    if not plan or not plan.get('stats'):
        return Advice(None,'Définir un objectif','Choisis les caractéristiques que tu souhaites atteindre.','bloqué')
    if not jets_confirmed:
        return Advice(None,'Jet à actualiser','Forgely doit relire et confirmer le jet après la dernière fusion. Aucun conseil sur un jet périmé.','bloqué')
    if puits is None:
        return Advice(None,'Puits à confirmer','Le reliquat n’est pas encore lu avec suffisamment de fiabilité. Recommandation suspendue.','bloqué')
    todo=[]
    for stat, pair in plan['stats'].items():
        current=pair.get('current');target=pair.get('target')
        if current is None or target is None:
            return Advice(None,'Jet incomplet',f'{stat} : valeur actuelle ou objectif inconnu.','bloqué')
        gap=target-current
        if gap <= 0: continue
        options=STATS.get(stat,())
        incs=INCREMENTS.get(stat,())
        for idx,rune in enumerate(options):
            if idx >= len(incs):continue
            inc=incs[idx]
            # Avoid proposing a tier that overshoots a target when a smaller tier exists.
            if inc > gap:continue
            n,counts=(records(rune) if records else (0,{'SC':0,'SN':0,'EC':0}))
            rates,_=describe_observed(counts)
            # Score is a conservative heuristic, NOT an inferred official probability.
            # Prefer closer-to-target increments; larger runes can save actions on big gaps.
            score=min(inc/gap,1)*0.45 + (1-abs(gap-inc)/max(gap,1))*0.35
            if n>=30:score+=0.20*(counts.get('SC',0)+counts.get('SN',0))/n
            todo.append((score,stat,rune,gap,inc,rates,n))
    if not todo:
        return Advice(None,'Objectif atteint ou hors catalogue','Aucune rune prudente identifiée pour les écarts restants. Contrôle le jet dans DOFUS.','bloqué')
    _,stat,rune,gap,inc,rates,n=max(todo,key=lambda p:p[0])
    desc=f'{stat} : manque {gap}; {rune} ajoute théoriquement {inc} en cas de gain complet. Puits indiqué : {puits:g}. '
    desc+=priority_note(target_ratio=None,rune_density=reference(rune).weight,reliquat=puits)+'. '
    if last_rune:desc+=f'Dernière rune détectée : {last_rune}. '
    if last_results:desc+=f'Derniers résultats : {", ".join(last_results[-4:])}. Les échecs passés ne garantissent pas le succès suivant. '
    if n:
        desc+=f'{n} tentatives locales sur cet équipement avec {rune}. '
        if n<30:desc+='Échantillon insuffisant pour une estimation robuste.'
        else:desc+='Fréquences constatées, contexte du jet et du puits non encore stratifié.'
    else:desc+='Pas encore de données locales comparables pour cette rune.'
    return Advice(rune,'Rune à envisager : '+rune,desc,'indicatif' if n<30 else 'observations',rates,n)
