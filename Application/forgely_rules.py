"""DOFUS PC FM constraints, community references checked 2026-11-07.

Not the proprietary success algorithm. A partial profile never proves absence.
Sources: https://huzounet.fr/guides/forgemagie (annex rules),
https://www.gamosaurus.com/jeux/dofus/forgemagie-le-guide-complet-dofus
"""
from math import isfinite
from forgely_probabilites import reference

MODES = ('Chances maximales', 'Budget optimisé')
RUNE_CHOICES = {
    'Vitalité': ('Vi', 'Pa Vi', 'Ra Vi'),
    'Force': ('Fo', 'Pa Fo', 'Ra Fo'),
    'Intelligence': ('Ine', 'Pa Ine', 'Ra Ine'),
    'Chance': ('Cha', 'Pa Cha', 'Ra Cha'),
    'Agilité': ('Age', 'Pa Age', 'Ra Age'),
    'Sagesse': ('Sa', 'Pa Sa', 'Ra Sa'),
    'Puissance': ('Pui', 'Pa Pui', 'Ra Pui'),
    'Initiative': ('Ini', 'Pa Ini', 'Ra Ini'),
    'Prospection': ('Prospe', 'Pa Prospe'),
    'Pods': ('Pod', 'Pa Pod', 'Ra Pod'),
    'PA': ('Ga Pa',), 'PM': ('Ga Pme',), 'Portée': ('Po',),
    'Invocations': ('Invo',), 'Coups critiques': ('Cri',),
    'Soins': ('So',), 'Tacle': ('Tac', 'Pa Tac'), 'Fuite': ('Fui', 'Pa Fui'),
    'Dommages': ('Do',),
}
for _suffix in ('Terre', 'Feu', 'Eau', 'Air', 'Neutre', 'Cri', 'Pou'):
    _name = {'Cri': 'critiques', 'Pou': 'poussée'}.get(_suffix, _suffix)
    RUNE_CHOICES['Dommages ' + _name] = ('Do ' + _suffix, 'Pa Do ' + _suffix)
for _suffix in ('Terre', 'Feu', 'Eau', 'Air', 'Neutre'):
    RUNE_CHOICES['Résistance ' + _suffix] = ('Ré ' + _suffix,)
    RUNE_CHOICES['% Résistance ' + _suffix] = ('Ré Per ' + _suffix,)

# Exact labels emitted by the OCR parser; retain legacy spellings for saved plans.
for _name, _source in {'Coups Critiques': 'Coups critiques', 'Invocation': 'Invocations',
                        'Dommages Critiques': 'Dommages critiques',
                        'Dommages Poussée': 'Dommages poussée'}.items():
    RUNE_CHOICES[_name] = RUNE_CHOICES[_source]

WEIGHTS = {stat: reference(runes[0]).weight / reference(runes[0]).gain
           for stat, runes in RUNE_CHOICES.items()}
CAP = 101.0


def finite_number(value, *, nonnegative=False):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and isfinite(value) and (not nonnegative or value >= 0))


def known_prices(prices):
    """Missing/invalid is unknown, never a free rune or a displayable price."""
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
            'reason': 'Contraintes non vérifiables sur toutes les lignes' if unknown else 'Sous les plafonds communautaires',
            'exotic_weight': round(exotic, 4)}


def objective_mode(value):
    """Retain legacy settings; old economy preference maps to the new mode."""
    if value in ('Économique', 'Budget optimisé'):
        return MODES[1]
    if value in (*MODES, 'Prudent', 'Rapide', 'Jet parfait'):
        return MODES[0]
    raise ValueError('Mode de recommandation inconnu')
