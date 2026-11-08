"""Client-derived weights and conservative Forgely constraints, checked 2026-11-08.

Not the proprietary success algorithm. A partial profile never proves absence.
Weights: versioned client extraction in forgely_weights; not publisher verified.
Simulator display contexts: https://dofocus.fr/forgemagie/
The retained 101 line/exotic guards are Forgely policy, not a reconstructed
Dofocus formula. Historical background remains in docs/FM_DOUBLE_OBJECTIF.md.
"""
from math import isfinite
from forgely_dofocus import (reference, RUNE_CHOICES as DOFOCUS_CHOICES,
                             WEIGHT_PER_POINT, canonical_stat)

MODES = ('Chances maximales','Budget optimisé')
RUNE_CHOICES = {stat:tuple(runes) for stat,runes in DOFOCUS_CHOICES.items()}
# Keep spellings accepted by earlier objective files.
for alias in ('Coups critiques','Invocation','Dommages critiques','Dommages poussée'):
    RUNE_CHOICES[alias]=RUNE_CHOICES[canonical_stat(alias)]
WEIGHTS = {stat:WEIGHT_PER_POINT[canonical_stat(stat)] for stat in RUNE_CHOICES}

CAP = 101.0


def finite_number(value, *, nonnegative=False):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and isfinite(value) and (not nonnegative or value >= 0))


def known_prices(prices):
    """Keep absent and invalid prices unknown, never implicitly free."""
    return {r:p for r,p in (prices or {}).items() if finite_number(p,nonnegative=True)}


def constraints(jets, natural_max, *, complete_profile=True, cap=CAP):
    """Tri-state constraint check, not a guarantee that a rune will pass.

    Over: total resulting line density <=101. Natural high lines stay legal.
    Exotics: cumulative density <=101. Unknown weights/profile => unknown.
    Negative natural lines require separate malus rules; no silent approval.
    """
    if not finite_number(cap, nonnegative=True):
        return {'valid': False, 'reason': 'Plafond invalide', 'exotic_weight': None}
    if any(not finite_number(v) for v in jets.values()):
        return {'valid': False, 'reason': 'Jet invalide', 'exotic_weight': None}
    if natural_max is None:
        return {'valid': None, 'reason': 'Profil naturel inconnu', 'exotic_weight': None}
    if any(not finite_number(v) for v in natural_max.values()):
        return {'valid': False, 'reason': 'Bornes naturelles invalides', 'exotic_weight': None}
    exotic = 0.0
    unknown = False
    for stat, value in jets.items():
        maximum = natural_max.get(stat)
        weight = WEIGHTS.get(stat)
        if value < 0 or (maximum is not None and maximum < 0):
            unknown = True
            continue
        if maximum is not None:
            if value <= maximum:
                continue
            if weight is None:
                unknown = True
            elif value * weight > cap + 1e-8:
                return {'valid': False, 'reason': f'Plafond de ligne over dépassé : {stat}', 'exotic_weight': exotic}
        elif value:
            if not complete_profile or weight is None:
                unknown = True
            else:
                exotic += value * weight
    if exotic > cap + 1e-8:
        return {'valid': False, 'reason': 'Densité cumulée des exos dépassée', 'exotic_weight': exotic}
    return {'valid': None if unknown else True,
            'reason': 'Contraintes non vérifiables sur toutes les lignes' if unknown else 'Sous les gardes conservatrices Forgely (pas une formule Dofocus publiée)',
            'exotic_weight': round(exotic, 4)}


def objective_mode(value):
    """Legacy economic preferences migrate to the sole target-first mode."""
    if value in MODES:return value
    if value in (*MODES, 'Économique', 'Budget optimisé', 'Prudent', 'Rapide',
                 'Jet propre', 'Jet parfait', 'Exo PA', 'Exo PM', 'Exo PO'):
        return MODES[0]
    raise ValueError('Mode de recommandation inconnu')
