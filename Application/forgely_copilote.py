"""Player-focused advisory helpers; no game input, no invented probabilities."""
from __future__ import annotations
from dataclasses import dataclass

MODES = ('Jet propre', 'Jet parfait', 'Exo PA', 'Exo PM', 'Exo PO')

@dataclass(frozen=True)
class PlayerSignal:
    title: str
    detail: str
    risk: str
    stop: bool


def goal_reached(jets, targets):
    """True only when ALL configured target values were actually observed."""
    return bool(targets) and bool(jets) and all(
        key in jets and isinstance(jets[key], (int, float)) and jets[key] >= value
        for key, value in targets.items()
    )


def player_signal(proposal, jets, targets, pool, verified, after_fusion, mode='Jet propre'):
    if not verified or after_fusion or not jets or pool is None:
        return PlayerSignal('Lecture en attente', 'Aucune rune conseillée sans jet et puits confirmés.', 'Inconnu', False)
    if goal_reached(jets, targets):
        return PlayerSignal('STOP — objectif atteint', 'Vérifie le jet dans DOFUS avant toute nouvelle rune.', 'Élevé si poursuite', True)
    if mode.startswith('Exo'):
        stat = mode.split()[-1]
        if stat not in targets:
            return PlayerSignal('Objectif exo à définir', f'Ajoute une cible {stat} dans les objectifs avant de poursuivre.', 'Inconnu', False)
    if not getattr(proposal, 'rune', None):
        if getattr(proposal, 'summary', '') == 'Aucun objectif':
            return PlayerSignal('Jet lu · cible à définir',
                f'Équipement et jet confirmés ; reliquat {pool:g}. Définis un objectif pour obtenir un conseil.',
                'Inconnu', False)
        return PlayerSignal('Conseil suspendu', getattr(proposal, 'summary', 'Jet incomplet'), 'Inconnu', False)
    # These are qualitative caution labels, never empirical probabilities.
    risk = 'Élevé' if mode.startswith('Exo') or pool == 0 else 'Modéré'
    return PlayerSignal(f'{proposal.rune} ×1', getattr(proposal, 'summary', ''), risk, False)


def budget_summary(attempts, unit_prices, budget):
    if attempts is None or unit_prices is None: raise ValueError('Données manquantes')
    spent = sum(max(0, int(n)) * max(0, float(unit_prices.get(r, 0))) for r, n in attempts.items())
    return {'spent': round(spent, 2), 'budget': budget,
            'remaining': None if budget is None else round(float(budget) - spent, 2),
            'over_budget': budget is not None and spent > float(budget)}
