"""Auditable expert dashboard, not a learned policy or game controller.

One SC counterfactual is recalculated. SN/EC loss distributions are unknown;
their branches deliberately require the next confirmed reading.
"""
from forgely_dofocus import normalise_jet, reference, RUNE_CHOICES, WEIGHT_PER_POINT, natural_profile
from forgely_rules import finite_number


def audit_transition(rune, outcome, before, after, *, complete=False):
    result = {'status': 'invalide', 'outcome': outcome, 'rune': rune,
              'calculated_pool': None, 'lost_weight': None, 'formula': None}
    if outcome not in ('SC', 'SN', 'EC') or not isinstance(before, dict) or not isinstance(after, dict):
        return result
    start, end = normalise_jet(before.get('jet')), normalise_jet(after.get('jet'))
    pools = before.get('pool'), after.get('pool')
    if (not start or not end or set(start) != set(end)
            or any(not finite_number(p, nonnegative=True) for p in pools)):
        return result
    result.update(before_pool=pools[0], observed_pool=pools[1],
                  changes={s: round(end[s] - v, 4) for s, v in start.items() if end[s] != v},
                  status='partiel')
    ref = reference(rune)
    if outcome!='SC' and any(v<0 for v in (*start.values(),*end.values())):
        from forgely_pool_ledger import _jet, _decimal, signed_transfer
        stat = next((s for s, choices in RUNE_CHOICES.items() if rune in choices), None)
        if not complete:
            return result
        try:
            charge,lost=signed_transfer(_jet(start),_jet(end),stat,
                _decimal(ref.gain),_decimal(ref.weight),outcome)
        except (ValueError,TypeError,ArithmeticError):
            result.update(status='non_modélisé',formula='Cas signé non vérifié : reliquat lu requis.')
            return result
        expected=float(max(_decimal(0),_decimal(pools[0])+lost-charge))
        result.update(status='cohérent' if abs(expected-pools[1])<1e-4 else 'contradictoire',
            calculated_pool=expected,lost_weight=float(lost),attempted_weight=float(charge),
            formula=f'max(0 ; {pools[0]:g} + {lost} − {charge}) = {expected:g}')
        return result
    stat = next((s for s, choices in RUNE_CHOICES.items() if rune in choices), None)
    if not complete or stat not in start or ref.weight is None:
        return result
    if any(s not in WEIGHT_PER_POINT for s in start):
        return result
    # Account for losses on the targeted line too: nominal gain minus net change.
    losses = {s: v + (ref.gain if s == stat and outcome != 'EC' else 0) - end[s]
              for s, v in start.items()}
    if any(v < -1e-6 for v in losses.values()) or (outcome == 'SC' and any(abs(v) > 1e-6 for v in losses.values())):
        result['status'] = 'contradictoire'
        return result
    from forgely_decision import pool_transition
    lost = round(sum(max(0, v) * WEIGHT_PER_POINT[s] for s, v in losses.items()), 4)
    expected = pool_transition(pools[0], ref.weight, lost, outcome)
    result.update(lost_weight=lost, calculated_pool=expected,
                  status='cohérent' if abs(expected - pools[1]) < 1e-4 else 'contradictoire',
                  formula=(f'SC : puits conservé = {pools[0]:g}' if outcome == 'SC' else
                           f'max(0 ; {pools[0]:g} + {lost:g} − {ref.weight:g}) = {expected:g}'))
    return result


def build_dashboard(proposal, jets, targets, pool, *, natural_max=None,
                    profile_complete=True, item=None, mode='Chances maximales',
                    prices=None, remaining_budget=None, verified=True,
                    after_fusion=False, last_transition=None,level=None):
    clean, goals = normalise_jet(jets), normalise_jet(targets)
    documented = natural_profile(item) if item else None
    if documented is not None:
        natural_max, profile_complete = documented, True
    elif natural_max is not None:
        natural_max = normalise_jet(natural_max)
    confirmed = (verified and not after_fusion and bool(clean)
                 and goals is not None and finite_number(pool, nonnegative=True))
    action = proposal.rune if confirmed else None
    ref = reference(action)
    result = {'pool': {'value': pool if confirmed else None,
                       'status': 'confirmé' if confirmed else 'inconnu ou à confirmer'},
              'action': {'rune': action, 'weight': ref.weight, 'gain': ref.gain},
              'phase': 'Lecture ou objectif à confirmer', 'branches': {},
              'risk': 'Inconnu', 'goal_probability': None, 'confidence_percent': None,
              'confidence': 'Classement heuristique ; probabilité finale non estimée.',
              'stop': confirmed and proposal.kind == 'atteint',
              'status': proposal.summary, 'transition': last_transition if confirmed else None,
              'prediction':(proposal.estimates or {}).get('prediction') if confirmed else None,'level':level}
    if not confirmed or not action or ref.gain is None or ref.weight is None:
        if result['stop']:
            result['phase'] = 'Objectif atteint — arrêt'
        return result
    result['phase'] = ('Finition over/exo' if proposal.kind in ('over', 'exo') else 'Remontée des cibles')
    result['risk'] = ('Critique' if proposal.kind in ('over', 'exo') else
                      'Moyen' if ref.weight > pool else 'Faible')
    if natural_max is not None:
        for stat, amount in clean.items():
            # Existing overs can be lost on a later attempt even with a covered rune.
            if ((stat in natural_max and amount > natural_max[stat]) or
                    (profile_complete and stat not in natural_max and amount > 0)):
                result['risk'] = 'Critique'
    stat = next((s for s, choices in RUNE_CHOICES.items() if action in choices), None)
    if stat not in clean:
        return result
    post = dict(clean)
    post[stat] += ref.gain
    left = None  # Currency budgets do not participate in target advice.
    from forgely_decision import advise
    next_proposal = advise(post, goals, natural_max=natural_max, pool=pool,
                           mode=mode, prices=prices, remaining_budget=left,
                           profile_complete=profile_complete, item=item,level=level)
    result['branches']['SC'] = {'pool': pool, 'next_rune': next_proposal.rune,
        'status': next_proposal.summary, 'remaining_budget': left,
        'condition': 'Hypothèse : gain nominal sans perte ; relecture réelle obligatoire.'}
    for outcome in ('SN', 'EC'):
        result['branches'][outcome] = {'pool': None, 'next_rune': None,
            'status': 'Relire le jet et les pertes avant de recalculer',
            'formula': f'max(0 ; {pool:g} + poids perdu observé − {ref.weight:g})',
            'condition': 'Pertes inconnues : aucune prochaine rune prédéfinie.'}
    if (proposal.estimates or {}).get('signed_profile'):
        result['risk']='Non quantifié (malus)'
        for outcome in ('SN','EC'):
            result['branches'][outcome]['formula']='Malus : relire le reliquat, comptabilité des pertes signées non validée.'
    return result


def render_dashboard(board):
    pool = board['pool']['value']
    lines = ['[ÉTAT DU PUITS] ' + (f'{pool:g} · confirmé' if pool is not None else 'Inconnu / à confirmer')]
    audit = board.get('transition')
    if audit and 'observed_pool' in audit:
        lines.append(f"Dernière pose : {audit['rune']} · {audit['outcome']} ; puits lu {audit['before_pool']:g} → {audit['observed_pool']:g}.")
        lines.append(audit['formula'] or 'Lecture partielle : comptabilité complète des pertes non certifiée.')
        if audit['status'] == 'contradictoire':
            lines.append('Contradiction détectée : vérifier les lectures ; aucune correction automatique du puits.')
    action = board['action']
    prediction=board.get('prediction')
    if prediction:
        lines.append('[PROBABILITÉS ESTIMÉES] '+ ' · '.join(f'{k} {prediction[k]:.2f} %' for k in ('SC','SN','EC'))
                     +' · modèle vidéo, hypothèses affichées ; aucun taux officiel.')
        if prediction.get('difficulty') is not None:
            lines.append(f"[DIFFICULTÉ] {prediction['difficulty']:.2f} · niveau {board.get('level') or 'inconnu'} · "+'; '.join(prediction.get('assumptions',[])))
    lines.append('[ACTION SUIVANTE] ' + (f"{action['rune']} · poids {action['weight']:g}" if action['rune'] else board['status']))
    lines.append('[PLAN À MOYEN TERME] ' + board['phase'])
    for outcome, branch in board['branches'].items():
        if outcome == 'SC':
            lines.append(f"SC → puits {branch['pool']:g} ; " + (f"puis {branch['next_rune']}" if branch['next_rune'] else branch['status']) + ' (scénario conditionnel).')
        else:
            lines.append(f"{outcome} → {branch['formula']} ; relire puis recalculer.")
    lines.extend(('[RISQUE] ' + board['risk'] + ' · exposition indicative, pas un taux de perte.',
                  '[FIABILITÉ] ' + board['confidence'],
                  '[APPRENTISSAGE] Fréquences descriptives séparées ; aucun coefficient serveur déduit d’un échec.'))
    return '\n'.join(lines)


def rules_text(price_settings=None):
    from forgely_weights import load_weights
    data=load_weights()
    rules = [
        'Modèle vidéo estimé : calibration sur transitions réelles qualifiées, prior de 200 essais ; simulations et observations séparées.',
        'RÈGLES ACTIVES DU COPILOTE — 8 novembre 2026',
        '1. Atteindre tous les minima du jet demandé. Ne pas remplacer ces cibles par un jet parfait ou une valeur de revente.',
        '2. Conseiller uniquement sur un objet et un jet confirmés, avec toutes les lignes ciblées présentes et un puits confirmé. Après une pose, attendre la nouvelle lecture.',
        '3. Ne jamais déduire le puits des points manquants au jet parfait. Le puits n’est pas plafonné à 101.',
        '4. SC : puits conservé. SN/EC : max(0 ; puits initial + poids des pertes − poids de la rune). Les pertes du jet complet doivent être connues pour certifier le calcul.',
        '5. Poids = gain de la rune × poids par point, distinct du poids d’inventaire. Un seul référentiel versionné est partagé entre les moteurs.',
        '6. Bornes naturelles documentées : dépassement = over ; absence = exo uniquement si le profil naturel est complet. Un CSV partiel ne prouve pas une absence.',
        '7. Gardes conservatrices : densité totale d’une ligne over ≤101, sauf maximum naturel supérieur ; densité cumulée des lignes exotiques ≤101. Ce sont des gardes de Forgely, pas une formule officielle reconstituée.',
        '8. Exo possible sans puits. Aucun sacrifice automatique et aucun ordre universel de quatre phases. Remonter une ligne naturelle ciblée disponible avant une finition over/exo.',
        '9. Minima atteints : arrêt. Aucun budget dur ne bloque les conseils. Aucun seuil automatique à 98 % du jet parfait et aucun seuil de risque fictif à 60 %.',
        '10. Jet cible prioritaire : prix et anciens modes economiques exclus du conseil.',
        '11. Sequences comparables du jet complet prioritaires sur la phase de puits et le taux de la prochaine rune.',
        '12. Scenario SC : gain nominal et puits conserve ; SN/EC : relire les pertes avant le prochain conseil.',
        '13. Risque qualitatif : Faible si rune couverte ; Moyen si poids non couvert ; Critique pour finition ou over/exo déjà présent et identifié. Ce ne sont pas des probabilités. Un profil partiel peut laisser une fragilité inconnue.',
        '14. Aucun pourcentage de confiance ou de réussite finale inventé. Aucun coefficient de difficulté serveur déduit d’une série d’échecs.',
        '15. Relevés Dofocus : réutilisation seulement pour le même objet, jet complet et puits exacts. Leur SC+SN affiché peut pondérer le classement ; cela ne valide pas ces chiffres comme probabilités du jeu.',
        '16. Observations comparables : calibration explicite du modele ; aucune seconde application des memes essais.',
        '17. Simulations et observations restent séparées. Les politiques apprises restent inactives sans validation indépendante. Le mélange 60 % réel / 40 % simulations exige les validations et le contexte requis.',
        '18. Malus non traités par les règles positives ; transcendances, chasse et Signature ne sont pas proposées comme runes ordinaires. Mode observation : aucun conseil. Aucun clic automatique dans DOFUS.',
        '',
        'PRIX : exclus du conseil de rune ; anciens parametres ignores.',
        '',
        'PROVENANCE DES POIDS : ' + data['provenance']['notice'],
        'Client ' + data['provenance']['game_version'] + ' ; extraction : ' + data['provenance']['release_url'],
        '', 'POIDS DES 105 RUNES (densité totale de la rune) :',
    ]
    for row in sorted(data['runes'],key=lambda r:r['rune'].casefold()):
        if row['weight'] is None:
            rules.append(row['rune']+' : hors combat ; aucune densité attribuée.')
        else:
            rules.append(f"{row['rune']} : gain +{row['gain']:g} ; poids {row['weight']:g}" + (' ; propriété spéciale, non proposée.' if row['kind']!='ordinaire' else ''))
    from pathlib import Path
    contract = Path(__file__).with_name('PROMPT_CONSEILLER_FM.md').read_text(encoding='utf-8')
    return contract + '\n\n--- REFERENTIEL TECHNIQUE ---\n' + '\n'.join(rules)
