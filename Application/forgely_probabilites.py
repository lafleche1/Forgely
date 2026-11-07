"""References et estimateurs prudents pour DOFUS 3.

Il n'existe PAS de taux SC/SN/EC officiel fixe par rune.
Les sources communautaires sont indiquées comme telles. Les mesures locales
sont des fréquences descriptives, non corrigées pour la sélection des jets.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import sqrt
from forgely_huzounet import exo_success_reference

# Poids vérifiables: bonus × poids d'une unité de caractéristique.
# Les noms suivent les captures DOFUS 3 fournies, pas les anciennes conventions.
# Valeurs sans preuve suffisamment stable laissées absentes de la table.
BASE = {
    'Vi': (5, 1.), 'Pa Vi': (15, 3.), 'Ra Vi': (50, 10.),
    'Fo': (1,1.), 'Pa Fo':(3,3.), 'Ra Fo':(10,10.),
    'Ine':(1,1.), 'Pa Ine':(3,3.), 'Ra Ine':(10,10.),
    'Cha':(1,1.), 'Pa Cha':(3,3.), 'Ra Cha':(10,10.),
    'Age':(1,1.), 'Pa Age':(3,3.), 'Ra Age':(10,10.),
    'Sa':(1,3.), 'Pa Sa':(3,9.), 'Ra Sa':(10,30.),
    'Ini':(10,1.), 'Pa Ini':(30,3.), 'Ra Ini':(100,10.),
    'Pui':(1,2.), 'Pa Pui':(3,6.), 'Ra Pui':(10,20.),
    'Prospe':(1,3.), 'Pa Prospe':(3,9.),
    'Pod':(10,2.5), 'Pa Pod':(30,7.5), 'Ra Pod':(100,25.),
    'Ga Pa':(1,100.), 'Ga Pme':(1,90.), 'Po':(1,51.),
    'Cri':(1,10.), 'So':(1,10.), 'Tac':(1,4.), 'Pa Tac':(3,12.),
    'Fui':(1,4.), 'Pa Fui':(3,12.), 'Invo':(1,30.),
    'Ré Terre':(1,2.), 'Ré Feu':(1,2.), 'Ré Eau':(1,2.),
    'Ré Air':(1,2.), 'Ré Neutre':(1,2.),
    'Ré Per Terre':(1,6.), 'Ré Per Feu':(1,6.),
    'Ré Per Eau':(1,6.), 'Ré Per Air':(1,6.), 'Ré Per Neutre':(1,6.),
    'Pa Ré Per Terre':(3,18.), 'Pa Ré Per Feu':(3,18.),
    'Pa Ré Per Eau':(3,18.), 'Pa Ré Per Air':(3,18.),
    'Pa Ré Per Neutre':(3,18.),
    'Do Terre':(1,5.), 'Do Feu':(1,5.), 'Do Eau':(1,5.),
    'Do Air':(1,5.), 'Do Neutre':(1,5.), 'Do Cri':(1,5.),
    'Do Pou':(1,5.), 'Pa Do Terre':(3,15.), 'Pa Do Feu':(3,15.),
    'Pa Do Eau':(3,15.), 'Pa Do Air':(3,15.),
    'Pa Do Neutre':(3,15.), 'Pa Do Cri':(3,15.), 'Pa Do Pou':(3,15.),
    'Do':(1,20.), 'Ré Pa':(1,7.), 'Ré Pme':(1,7.),
    'Ret Pa':(1,7.), 'Ret Pme':(1,7.), 'Pa Ret Pa':(3,21.), 'Pa Ret Pme':(3,21.),
}
# Eviter d'affirmer un poids contradictoire sans source moderne: supprimer
# des variantes controversées plutot que de diffuser une valeur fausse.
for _r in ('Ré Pa','Ré Pme','Pa Ret Pa','Pa Ret Pme','Ret Pa','Ret Pme',
           'Pa Ré Per Terre','Pa Ré Per Feu','Pa Ré Per Eau','Pa Ré Per Air','Pa Ré Per Neutre'):
    BASE.pop(_r,None)

# Huzounet: exo sur caractéristique absente et rune de densité >20 : 1 % SC, 0 % SN.
# Ce n'est pas un taux général applicable à toutes les runes exotiques.
EXO_PA_PM_SC_COMMUNITY = 0.01
HEAVY_EXO_RUNES = frozenset(('Ga Pa', 'Ga Pme', 'Po', 'Invo'))

@dataclass(frozen=True)
class RuneReference:
    name: str
    gain: float | None
    weight: float | None
    documented_fixed_odds: bool = False

def reference(rune):
    clean=(rune or '').strip()
    gain,weight=BASE.get(clean,(None,None))
    return RuneReference(clean,gain,weight)

def wilson(k,n,z=1.96):
    if not n: return 0.,1.
    p=k/n
    d=1+z*z/n
    center=(p+z*z/(2*n))/d
    width=z/d*sqrt(p*(1-p)/n+z*z/(4*n*n))
    return max(0.,center-width), min(1.,center+width)

def empirical(counts):
    """Returns only measured percentages and confidence intervals, never invented priors."""
    n=sum(int(counts.get(k,0)) for k in ('SC','SN','EC'))
    if n<0 or any(counts.get(k,0)<0 for k in ('SC','SN','EC')):
        raise ValueError('Comptages invalides')
    return {'n':n,'levels':{k:{'percentage':100*counts.get(k,0)/n if n else None,
                          'ci95':tuple(100*x for x in wilson(counts.get(k,0),n)) if n else None}
                           for k in ('SC','SN','EC')},
            'quality':'insuffisant' if n<30 else 'indicatif' if n<200 else 'meilleur echantillon',
            'warning':'Fréquences brutes : les jets et puits de départ ne sont pas encore comparables.'}

def baseline(rune, *, exotic=False, natural_stat=None):
    """Guide Huzounet benchmark only for a verified >20-weight exo on absent stat.
    No generally applicable SC/SN/EC base split is available elsewhere.
    """
    if exotic is True and natural_stat is False:
        ref=reference(rune)
        evidence=exo_success_reference(natural_present=False,rune_density=ref.weight)
        if evidence.sc_pct is not None:
            return {'SC':evidence.sc_pct,'SN':evidence.sn_pct,'EC':evidence.ec_pct,
                    'kind':evidence.provenance,'note':evidence.note}
    return {'SC':None,'SN':None,'EC':None,'kind':'non_documente',
            'note':'Pas de taux de base vérifié par rune : nécessite le contexte du jet et du puits.'}

def summary(rune,counts, *, exotic=False,natural_stat=None):
    return {'rune':rune,'reference':reference(rune),'baseline':baseline(rune,exotic=exotic,natural_stat=natural_stat),
            'observed':empirical(counts)}
