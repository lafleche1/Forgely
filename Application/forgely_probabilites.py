"""References et estimateurs prudents pour DOFUS 3.

Il n'existe PAS de taux SC/SN/EC officiel fixe par rune.
Les sources communautaires sont indiquées comme telles. Les mesures locales
sont des fréquences descriptives, non corrigées pour la sélection des jets.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import sqrt
from forgely_huzounet import exo_success_reference

# Single shared density table. Historical exclusions must not contradict the
# active advisor or newly documented rune tiers.
from forgely_dofocus import RUNE_REFERENCES
BASE = {name: (ref.gain, ref.weight) for name, ref in RUNE_REFERENCES.items()}

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
