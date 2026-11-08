"""Explainable FM objectives; heuristic scores are NEVER success probabilities."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
from forgely_probabilites import empirical
from forgely_dofocus import (reference, lookup, lookup_context, natural_profile, line_limit,
    normalise_jet, displayed_number, risk_notes)
from forgely_rules import (RUNE_CHOICES, WEIGHTS as WEIGHT_PER_POINT, CAP,
                          constraints, finite_number, objective_mode, known_prices)


@dataclass(frozen=True)
class Proposal:
    rune: str | None
    kind: str
    summary: str
    explanation: str
    evidence: str
    estimates: dict | None = None
    sample: int = 0


def pool_transition(pool, attempted_weight, lost_weight, outcome):
    if outcome not in ('SC', 'SN', 'EC'):
        raise ValueError('Résultat inconnu')
    if any(not finite_number(v, nonnegative=True) for v in (pool, attempted_weight, lost_weight)):
        raise ValueError('Poids finis non négatifs requis')
    if outcome == 'SC':
        if lost_weight:
            raise ValueError('SC contradictoire avec une perte de caractéristique')
        return float(pool)
    return round(max(0., pool + lost_weight - attempted_weight), 4)


def classify(stat, current, proposed, natural_max: Mapping[str, float] | None, *, profile_complete=True):
    if natural_max is None:
        return 'inconnu'
    if stat not in natural_max:
        return ('exo' if proposed > 0 else 'absent') if profile_complete else 'inconnu'
    return 'over' if proposed > natural_max[stat] else 'fm_classique'


def extra_mass(jets, natural_max):
    """Descriptive surplus only, NOT a shared over/exo legality budget."""
    if natural_max is None:
        return None
    total = 0.
    for stat, amount in jets.items():
        if stat not in WEIGHT_PER_POINT:
            return None
        total += max(0., amount - natural_max.get(stat, 0)) * WEIGHT_PER_POINT[stat]
    return round(total, 5)


def candidates(jets, targets, natural_max=None, pool=None, counts_for=None, *,
               mode='Chances maximales', prices=None, remaining_budget=None, profile_complete=True,item=None):
    mode = objective_mode(mode)
    if (not targets or not jets or pool is None or not finite_number(pool, nonnegative=True)
            or any(stat not in jets for stat in targets)
            or any(not finite_number(v) for v in (*jets.values(), *targets.values()))
            or (natural_max is not None and any(not finite_number(v) for v in natural_max.values()))
            or (remaining_budget is not None and not finite_number(remaining_budget, nonnegative=True))):
        return []
    prices = known_prices(prices)
    pending_natural = any(current < targets.get(stat, current) and current < natural_max[stat]
                          for stat, current in jets.items() if natural_max and stat in natural_max)
    source_context=lookup_context(item,jets,pool) if item else None
    available = []
    for stat, goal in targets.items():
        current = jets[stat]
        if current >= goal:
            continue
        # Malus handling needs verified signed bounds, rather than positive-line rules.
        if current < 0 or (natural_max and natural_max.get(stat, 0) < 0):
            continue
        for rune in RUNE_CHOICES.get(stat, ()):
            ref = reference(rune)
            if ref.weight is None or ref.gain is None:
                continue
            proposed = current + ref.gain
            # Targets are minima: allow a tiny surplus only inside known natural bounds.
            if proposed > goal and not (natural_max is not None and stat in natural_max
                                         and proposed <= natural_max[stat]):
                continue
            modified = dict(jets)
            modified[stat] = proposed
            checked = constraints(modified, natural_max, complete_profile=profile_complete)
            if checked['valid'] is False:
                continue
            limit=line_limit(item,stat) if item else None
            if limit is not None and proposed>limit:continue
            sampled=source_context.get(rune) if source_context else None
            if sampled and sampled['blocked']:continue
            price = prices.get(rune)
            if not finite_number(price, nonnegative=True):
                price = None
            if (mode == 'Budget optimisé' or remaining_budget is not None) and price is None:
                continue
            if remaining_budget is not None and price > remaining_budget:
                continue
            kind = classify(stat, current, proposed, natural_max, profile_complete=profile_complete)
            counts = counts_for(rune) if counts_for else None
            obs = empirical(counts) if counts is not None else None
            base={'SC':None,'SN':None,'EC':None,'kind':'dofocus_non_documente',
                  'note':'Aucun taux fixe extrapolé depuis une autre source.'}
            remaining = goal - current
            progress = min(1., ref.gain / remaining)
            # Approximate exposure, not expected losses: actual loss distribution is unknown.
            exposed = max(0., ref.weight - pool)
            exposure = exposed / max(ref.weight, 1.)
            overshoot = max(0., proposed - goal) / max(1., remaining)
            # Community tier heuristic: soft penalty, never an impossibility threshold.
            tier_pressure = min(4., max(0., current / (20 * ref.gain) - 1.))
            finish_penalty = .8 if pending_natural and kind in ('exo', 'over') else 0.
            balance = 0.
            if natural_max and stat in natural_max and natural_max[stat] > 0:
                balance = .15 * max(0., 1 - current / natural_max[stat])
            utility = (progress + balance) / (1 + .7 * exposure + .5 * tier_pressure + overshoot)
            utility /= 1 + finish_penalty
            if sampled and not sampled['blocked']:
                display=sampled['display']
                utility *= (displayed_number(display['SC'])+displayed_number(display['SN']))/100
            if mode == 'Budget optimisé':
                # Price plus repair exposure valued at known cheapest cost per density.
                repair_prices = [p / reference(r).weight for r, p in prices.items()
                                 if finite_number(p, nonnegative=True) and reference(r).weight]
                repair_proxy = exposed * min(repair_prices) if repair_prices else 0.
                score = utility / max(1., price + repair_proxy)
            else:
                score = utility - .04 * ref.weight / 100 - finish_penalty
            available.append((score, rune, stat, kind, ref, base, obs,
                              extra_mass(modified, natural_max), current, goal))
    # Restore an available targeted natural line before risking a final over/exo.
    # This priority is independent of the rune prices, unlike the soft score.
    if pending_natural and any(row[3] == 'fm_classique' for row in available):
        available = [row for row in available if row[3] not in ('exo', 'over')]
    return sorted(available, key=lambda x: (-x[0], x[1]))


def advise(jets, targets, natural_max=None, pool=None, counts_for=None, after_fusion=False, *,
           mode='Chances maximales', prices=None, remaining_budget=None, profile_complete=True,item=None):
    jets=normalise_jet(jets)
    targets=normalise_jet(targets)
    if jets is None or targets is None:
        return Proposal(None,'bloqué','Valeurs invalides','Jet ou cible invalide.','Dofocus · contrôle des lectures')
    documented=natural_profile(item) if item else None
    if documented is not None:
        natural_max=documented
        profile_complete=True
    elif natural_max is not None:
        natural_max=normalise_jet(natural_max)
        if natural_max is None:
            return Proposal(None,'bloqué','Bornes naturelles invalides',
                            'Le profil fourni ne permet pas de vérifier les contraintes.','Dofocus · contrôle des bornes')
    mode = objective_mode(mode)
    prices = known_prices(prices)
    def blocked(title, detail):
        return Proposal(None, 'bloqué', title, detail, 'aucune')
    if after_fusion:
        return blocked('Jet à relire', 'Attendre une lecture stable du nouveau jet après la fusion.')
    if not targets:
        return blocked('Aucun objectif', 'Définis le jet cible de cet équipement.')
    if pool is None:
        return blocked('Reliquat à confirmer', 'Aucune recommandation tant que le reliquat n’est pas confirmé.')
    if (not finite_number(pool, nonnegative=True)
            or any(not finite_number(v) for v in (*jets.values(), *targets.values()))):
        return blocked('Valeurs invalides', 'Le jet et le reliquat doivent être des nombres finis confirmés.')
    if any(s not in jets for s in targets):
        return blocked('Jet incomplet', 'Toutes les lignes ciblées doivent être lues et confirmées.')
    if all(jets[s] >= v for s, v in targets.items()):
        return Proposal(None, 'atteint', 'Objectif atteint',
                        'Ne pose pas de rune supplémentaire sans nouvel objectif.', 'état confirmé')
    if remaining_budget is not None and not finite_number(remaining_budget, nonnegative=True):
        return blocked('Budget invalide', 'Renseigne un budget restant fini et positif ou nul.')
    if remaining_budget == 0:
        return blocked('Budget épuisé', 'Arrêt conseillé : aucune dépense supplémentaire autorisée par le budget.')
    options = candidates(jets, targets, natural_max, pool, counts_for, mode=mode, prices=prices,
                         remaining_budget=remaining_budget, profile_complete=profile_complete,item=item)
    if not options:
        return blocked('Aucune rune à proposer',
                       'Vérifie les prix, le budget restant, les bornes naturelles, les malus et les plafonds de lignes.')
    score, rune, stat, kind, ref, base, obs, weight, current, goal = options[0]
    sampled=lookup(item,jets,pool,rune) if item else None
    exposure = max(0., ref.weight - pool)
    explanation = (f'{mode} · {stat} : {current:g} → minimum {goal:g}. '
                   f'{rune} : gain nominal +{ref.gain:g}, poids {ref.weight:g}, reliquat {pool:g}. '
                   f'Poids non couvert par le reliquat : {exposure:g} (exposition, pas perte prédite). '
                   f'Type : {kind}. ')
    if natural_max is None or not profile_complete:
        explanation += 'Profil naturel incomplet : absence de ligne et légalité globale non certifiées. '
    if kind in ('exo', 'over'):
        explanation += 'Finition fragile : les poses suivantes peuvent dégrader cet ajout. '
    price = (prices or {}).get(rune)
    explanation += f'Prix unitaire de référence : {price:g} kamas. ' if price is not None else 'Prix inconnu. '
    if remaining_budget is not None:
        explanation += f'Budget restant avant pose : {remaining_budget:g} kamas. '
    if mode == 'Budget optimisé':
        explanation += 'Classement par progression/prix et exposition de réparation approximative ; coût final inconnu. '
    else:
        explanation += 'Classement par progression, palier de rune, équilibre des lignes et protection du jet. '
    n = obs['n'] if obs else 0
    if n:
        explanation += f'{n} observations agrégées : descriptives, non utilisées comme probabilités du prochain essai. '
    if sampled and not sampled['blocked']:
        display=sampled['display']
        explanation+=(f"Simulation Dofocus relevée le {sampled['captured_on']}, même jet complet et même reliquat : "
                      f"SC {display['SC']} %, SN {display['SN']} %, EC {display['EC']} %. "
                      "Valeurs affichées arrondies, non validées comme probabilités du jeu. ")
    else:
        explanation+='Aucun relevé Dofocus pour ce contexte exact : pourcentages non disponibles. '
    for note in risk_notes(current,current+ref.gain,ref.weight,pool,
                          natural_max.get(stat,0) if natural_max is not None and profile_complete else None):
        explanation+=note+' '
    explanation+='Politique Forgely : gardes conservatrices de plafond par ligne et d’exos cumulés à 101 ; pas une formule Dofocus publiée. '
    explanation+='Choix de rune indicatif selon l’objectif, sans garantie de réussite.'
    alternatives = [{'rune': row[1], 'stat': row[2], 'score': round(row[0], 6),
                     'price': (prices or {}).get(row[1])} for row in options[:5]]
    return Proposal(rune, kind, f'À envisager : {rune}', explanation, 'Densités du client · relevés Dofocus séparés ; classement Forgely',
                    {'observed': obs, 'benchmark': base,'dofocus':sampled,
                     'objective': {'mode': mode, 'remaining_budget': remaining_budget,
                                   'exposed_weight': exposure, 'alternatives': alternatives,
                                   'goal_probability': None}}, n)

