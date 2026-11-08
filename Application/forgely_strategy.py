"""Transparent advisory engine. Never equates past failures with increased next-roll luck.

Only comparable observations (same item & rune) enter empirical rates; incomplete
context means these are descriptive frequencies, not causal probabilities.
"""
from dataclasses import dataclass
from math import sqrt
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
    from forgely_decision import advise
    def counts_for(rune):
        return records(rune)[1] if records else {'SC':0,'SN':0,'EC':0}
    if any(v.get('current') is None or v.get('target') is None for v in plan['stats'].values()):
        return Advice(None,'Jet incomplet','Valeur actuelle ou objectif inconnu.','bloqué')
    proposal=advise({s:v['current'] for s,v in plan['stats'].items()},
                    {s:v['target'] for s,v in plan['stats'].items()},
                    pool=puits,counts_for=counts_for,item=plan.get('item'),level=plan.get('level'))
    details=proposal.explanation
    if last_rune:details+=f' Dernière rune détectée : {last_rune}.'
    if last_results:details+=' Les échecs passés ne garantissent pas le succès suivant.'
    rates,_=describe_observed(records(proposal.rune)[1]) if records and proposal.rune else (None,0)
    return Advice(proposal.rune,proposal.summary,details,proposal.evidence,rates,proposal.sample)

