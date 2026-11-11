"""Explainable FM objectives; heuristic scores are NEVER success probabilities."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
from forgely_probabilites import empirical, wilson
from forgely_dofocus import (reference, lookup, lookup_context, natural_profile, line_limit,
    normalise_jet, displayed_number, risk_notes)
from forgely_rules import (RUNE_CHOICES, WEIGHTS as WEIGHT_PER_POINT, CAP,
                          constraints, finite_number, objective_mode)


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


def contextual_measurement(record):
    """Only sufficiently populated comparable local observations affect rank."""
    if not isinstance(record, dict) or record.get('usable') is not True:
        return None
    n, counts = record.get('n'), record.get('counts')
    if type(n) is not int or n < 30 or not isinstance(counts, dict):
        return None
    values = [counts.get(outcome, 0) for outcome in ('SC', 'SN', 'EC')]
    if any(type(v) is not int or v < 0 for v in values) or sum(values) != n:
        return None
    if record.get('quality') not in ('exploratoire_ocr_non_verifie', 'local_verified'):
        return None
    low, high = wilson(values[0] + values[1], n)
    strength = min(.8, n / (n + 50))
    return {'n': n, 'counts': dict(zip(('SC', 'SN', 'EC'), values)),
            'quality': record['quality'], 'success_ci95': (low, high),
            'score_factor': 1 - strength + strength * low}


def experience_measurement(record):
    if (not isinstance(record,dict) or record.get('kind')!='experience_locale_indicative'
            or type(record.get('n')) is not int or record['n']<1
            or not finite_number(record.get('factor')) or not .85<=record['factor']<=1.1):
        return None
    return record


def combine_candidate_evidence(sampled,record,*,experience=None,local=None,simulation_weight=.4):
    """Fuse one simulated reference and independent real counts, never multiply
    two estimates of the same event or count simulation as player attempts.
    This is a conservative ranking factor, not a calibrated game probability.
    """
    if not finite_number(simulation_weight) or not 0<=simulation_weight<=1:
        raise ValueError('Poids simulation invalide')
    measured=contextual_measurement(record)
    interval=None;reference_success=None;sources=[]
    if isinstance(sampled,dict) and sampled.get('kind')=='local_dofocus_model' and not sampled.get('blocked'):
        probabilities=sampled.get('probabilities',{})
        values=[probabilities.get(o) for o in ('SC','SN','EC')]
        if all(finite_number(v) and 0<=v<=100 for v in values) and abs(sum(values)-100)<1e-6:
            reference_success=(values[0]+values[1])/100
            interval=(reference_success,reference_success)
            sources.append('modele_local_dofocus')
    elif isinstance(sampled,dict) and not sampled.get('blocked'):
        try:
            display=sampled['display']
            clean={o:display[o].lstrip('~≈') for o in ('SC','SN','EC')}
            values=[displayed_number(clean[o]) for o in ('SC','SN','EC')]
            ranges=[]
            for outcome,value in zip(('SC','SN','EC'),values):
                raw=clean[outcome].replace(',','.')
                decimals=len(raw.split('.')[1]) if '.' in raw else 0
                half=.5/(10**decimals)
                ranges.append((max(0,value-half)/100,min(100,value+half)/100))
            if not sum(r[0] for r in ranges)<=1<=sum(r[1] for r in ranges):
                raise ValueError('inconsistent rounded percentages')
            interval=(max(ranges[0][0]+ranges[1][0],1-ranges[2][1]),
                      min(ranges[0][1]+ranges[1][1],1-ranges[2][0]))
            reference_success=min(1,sum(values[:2])/100)
            if reference_success==0:reference_success=interval[1]/2
            sources.append('simulation_dofocus')
        except (KeyError,TypeError,ValueError,AttributeError):pass
    n=measured['n'] if measured else 0
    observed_interval=measured['success_ci95'] if measured else None
    real_factor=None
    experience=experience_measurement(experience) if not measured else None
    if measured:
        sources.append('observations_joueurs_contextuelles')
        real_factor=observed_interval[0]
    elif experience:
        sources.append('experience_joueurs_locale')
        # Experience is a relative utility correction, not a success rate.
        # Keep it on the same baseline as the model before blending.
        real_factor=(reference_success if reference_success is not None else 1.)*experience['factor']
    simulation_factor=reference_success
    if simulation_factor is not None:
        # Virtual damage belongs entirely to the simulated share.
        simulation_factor*=virtual_loss_factor(local or sampled,(local or sampled).get('weight',1.))
        policy=(local or sampled).get('trained_policy')
        if (isinstance(policy,dict) and policy.get('kind')=='trained_simulation_policy'
                and policy.get('source')=='simulation' and policy.get('real_observations')==0
                and finite_number(policy.get('factor')) and .8<=policy['factor']<=1.2):
            simulation_factor*=policy['factor']
    weights={'simulation':simulation_weight,'real':1-simulation_weight};fallback=None
    if simulation_factor is None and real_factor is None:
        effective={'simulation':0.,'real':0.};factor=1.;fallback='no_evidence'
    elif real_factor is None:
        effective={'simulation':1.,'real':0.};factor=simulation_factor;fallback='simulation_only'
    elif simulation_factor is None:
        effective={'simulation':0.,'real':1.};factor=real_factor;fallback='real_only'
    else:
        effective=weights.copy();factor=weights['simulation']*simulation_factor+weights['real']*real_factor
    discordant=bool(interval and observed_interval and
        (interval[1]<observed_interval[0] or interval[0]>observed_interval[1]))
    return {'factor':factor,'observations':n,'sources':sources,
        'reference_interval':interval,'observed_interval':observed_interval,
        'discordant':discordant,'is_game_probability':False,
        'configured_weights':weights,'weights':effective,'fallback':fallback,
        'simulation_factor':simulation_factor,'real_factor':real_factor,
        'experience_observations':experience['n'] if experience else 0}


def virtual_loss_factor(sampled,weight):
    outlook=sampled.get('outlook') if isinstance(sampled,dict) and sampled.get('kind')=='local_dofocus_model' else None
    if (not isinstance(outlook,dict) or outlook.get('kind')!='virtual_trials'
            or outlook.get('real_observations')!=0 or type(outlook.get('trials')) is not int
            or not 16<=outlook['trials']<=256 or not finite_number(outlook.get('mean_target_loss'),nonnegative=True)):
        return 1.
    # Loss exposure is an additional cost, not another success probability.
    return 1/(1+.25*min(1,outlook['mean_target_loss']/max(weight,1e-9)))


def sequence_measurement(local):
    row=local.get('sequence') if isinstance(local,dict) else None
    if not isinstance(row,dict) or row.get('kind')!='sequence_rollouts' or row.get('source')!='simulation':return None
    if isinstance(row.get('validation'),dict) and not row['validation'].get('accepted'):return None
    n=row.get('trials');wins=row.get('completed');horizon=row.get('horizon')
    if (row.get('real_observations')!=0 or type(n) is not int or not 16<=n<=256
            or type(wins) is not int or not 0<=wins<=n or type(horizon) is not int or not 1<=horizon<=32
            or not finite_number(row.get('value')) or not 0<=row['value']<=1
            or not finite_number(row.get('mean_steps')) or not 1<=row['mean_steps']<=horizon):return None
    return row


def candidates(jets, targets, natural_max=None, pool=None, counts_for=None, *,
               mode='Chances maximales', prices=None, remaining_budget=None, profile_complete=True,item=None,
               contextual_for=None,experience_for=None,simulation_for=None,allow_minimal_overshoot=False,price_book=None,
               level=None,context_for=None):
    # prices/remaining_budget are ignored compatibility inputs.
    mode = objective_mode(mode)
    if mode=='Budget optimisé' and price_book is None and prices:
        from forgely_pricing import book_from_settings
        price_book=book_from_settings(dict(prices=prices))
    if (not targets or not jets or pool is None or not finite_number(pool, nonnegative=True)
            or any(stat not in jets for stat in targets)
            or any(not finite_number(v) for v in (*jets.values(), *targets.values()))
            or (natural_max is not None and any(not finite_number(v) for v in natural_max.values()))):
        return []
    pending_natural = any(current < targets.get(stat, current) and current < natural_max[stat]
                          for stat, current in jets.items() if natural_max and stat in natural_max)
    source_context=lookup_context(item,jets,pool) if item else None
    available = []
    planning = {}
    real_adjustments = {}
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
            smallest=min((reference(r).gain for r in RUNE_CHOICES.get(stat,())
                          if reference(r).gain is not None),default=0)
            minimal_finish=(allow_minimal_overshoot and natural_max is None and ref.gain==smallest)
            if proposed > goal and not (minimal_finish or (natural_max is not None and stat in natural_max
                                         and proposed <= natural_max[stat])):
                continue
            modified = dict(jets)
            modified[stat] = proposed
            checked = constraints(modified, natural_max, complete_profile=profile_complete)
            if checked['valid'] is False:
                continue
            limit=line_limit(item,stat) if item else None
            if limit is not None and proposed>limit:continue
            local=simulation_for(rune) if simulation_for else None
            if local and local.get('blocked'):continue
            sampled=(source_context.get(rune) if source_context else None) or local
            if sampled and sampled.get('blocked'):continue
            if sampled and sampled.get('kind')!='local_dofocus_model' and not isinstance(sampled.get('display'),dict):
                sampled=None
            kind = classify(stat, current, proposed, natural_max, profile_complete=profile_complete)
            counts = counts_for(rune) if counts_for else None
            obs = empirical(counts) if counts is not None else None
            base={'SC':None,'SN':None,'EC':None,'kind':'dofocus_non_documente',
                  'note':'Aucun taux fixe extrapolé depuis une autre source.'}
            from forgely_predictive import estimate,calibrate
            prediction=calibrate(estimate(jets,natural_max,rune,level=level,profile_complete=profile_complete),
                                 context_for(rune) if context_for else None)
            base['prediction']=prediction
            remaining = goal - current
            progress = min(1., ref.gain / remaining)
            # Approximate exposure, not expected losses: actual loss distribution is unknown.
            exposed = max(0., ref.weight - pool)
            exposure = exposed / max(ref.weight, 1.)
            video_rank=prediction is not None and sampled is None
            overshoot = max(0., proposed - goal) / max(1.,ref.gain if video_rank else remaining)
            # Community tier heuristic: soft penalty, never an impossibility threshold.
            tier_pressure = 0. if video_rank else min(4., max(0., current / (20 * ref.gain) - 1.))
            finish_penalty = .8 if pending_natural and kind in ('exo', 'over') else 0.
            balance = 0.
            if natural_max and stat in natural_max and natural_max[stat] > 0:
                balance = .15 * max(0., 1 - current / natural_max[stat])
            non_sc=(100-prediction['SC'])/100 if video_rank else 1.
            utility = (progress + balance) / (1 + .7 * exposure*non_sc + .5 * tier_pressure + overshoot)
            utility /= 1 + finish_penalty
            record=contextual_for(rune) if contextual_for else None
            experience=experience_for(rune) if experience_for else None
            combined=combine_candidate_evidence(sampled,record,experience=experience,local=local)
            utility*=combined['factor']
            if prediction is not None and sampled is None:
                utility*=(prediction['SC']+prediction['SN'])/100
            score = utility - .04 * ref.weight / 100 - finish_penalty
            sequence=sequence_measurement(local)
            if sequence is not None:planning[rune]=sequence
            if combined['real_factor'] is not None and combined['simulation_factor']:
                # Real experience is a bounded relative correction, not a
                # competing immediate-progress score on a different scale.
                ratio=combined['real_factor']/combined['simulation_factor']
                real_adjustments[rune]=.4+.6*min(1.1,max(.85,ratio))
            available.append((score, rune, stat, kind, ref, base, obs,
                              extra_mass(modified, natural_max), current, goal))
    # Restore available targeted natural lines before final over/exo attempts.
    if pending_natural and any(row[3]=='fm_classique' for row in available):
        available=[row for row in available if row[3] not in ('exo','over')]
    if available and all(row[1] in planning for row in available):
        # Calibrated rollouts already mix real/model root outcomes: no second
        # application of the real share. Uncalibrated local experience stays bounded.
        available=[(planning[row[1]]['value']*(1. if planning[row[1]].get('calibration')
                    else real_adjustments.get(row[1],1.)),*row[1:]) for row in available]
        validated={entry['validation'].get('selected') for entry in planning.values()
                   if isinstance(entry.get('validation'),dict) and entry['validation'].get('accepted')}
        winner=next(iter(validated)) if len(validated)==1 else None
        from forgely_pricing import price_ties
        def priority(row):
            return (row[1]!=winner if winner else False,-row[0],planning[row[1]]['mean_steps'])
        from forgely_pricing import economic_scores
        available=economic_scores(available,price_book,mode)
        ordered=sorted(available,key=lambda row:(*priority(row),row[1]))
        return price_ties(ordered,price_book,priority=priority)
    from forgely_pricing import price_ties,economic_scores
    available=economic_scores(available,price_book,mode)
    return price_ties(sorted(available, key=lambda x: (-x[0], x[1])),price_book)


def advise(jets, targets, natural_max=None, pool=None, counts_for=None, after_fusion=False, *,
           mode='Chances maximales', prices=None, remaining_budget=None, profile_complete=True,item=None,
           contextual_for=None,experience_for=None,simulation_for=None,allow_minimal_overshoot=False,predictive_policy=False,price_book=None,
           level=None,context_for=None):
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
    if mode=='Budget optimisé' and price_book is None and prices:
        from forgely_pricing import book_from_settings
        price_book=book_from_settings(dict(prices=prices))
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
    if item and (natural_max is None or not profile_complete):
        return blocked('Profil naturel à confirmer',
                       'Le profil naturel complet de cet objet est nécessaire pour vérifier les contraintes avant de conseiller une rune.')
    if item and not set(natural_max).issubset(jets):
        return blocked('Jet incomplet',
                       'Toutes les lignes du profil naturel doivent être lues avant de conseiller une rune ; une ligne absente de l’OCR ne vaut pas zéro.')
    contextual_cache = {}
    def measured_for(rune):
        if rune not in contextual_cache:
            contextual_cache[rune] = contextual_for(rune) if contextual_for else None
        return contextual_cache[rune]
    experience_cache={}
    simulation_cache={}
    def simulated_for(rune):
        if rune not in simulation_cache:
            simulation_cache[rune]=simulation_for(rune) if simulation_for else None
        return simulation_cache[rune]
    def experienced_for(rune):
        if rune not in experience_cache:
            experience_cache[rune]=experience_measurement(experience_for(rune)) if experience_for else None
        return experience_cache[rune]
    options = candidates(jets, targets, natural_max, pool, counts_for, mode=mode,
                         profile_complete=profile_complete,item=item,
                         contextual_for=measured_for,experience_for=experienced_for,simulation_for=simulated_for,
                         allow_minimal_overshoot=allow_minimal_overshoot,price_book=price_book,level=level,context_for=context_for)
    matrix=None
    if predictive_policy:
        from forgely_predictive import rank_options,matrix_payload
        options,meta=rank_options(options,jets,natural_max,pool,profile_complete)
        matrix=matrix_payload(options,jets,natural_max,pool,meta)
    if not options:
        return Proposal(None,'bloqué','Aucune rune compatible avec la phase de puits' if matrix else 'Aucune rune à proposer',
                        matrix['reason'] if matrix else 'Vérifie les valeurs cibles, les bornes naturelles, les malus et les plafonds de lignes.',
                        'matrice utilisateur' if matrix else 'aucune',{'matrix':matrix} if matrix else None)
    score, rune, stat, kind, ref, base, obs, weight, current, goal = options[0]
    recorded=lookup(item,jets,pool,rune) if item else None
    local=simulated_for(rune)
    sampled=recorded or local
    contextual = contextual_measurement(measured_for(rune))
    experience=experienced_for(rune) if contextual is None else None
    source_comparison=combine_candidate_evidence(sampled,measured_for(rune),experience=experience,local=local)
    exposure = max(0., ref.weight - pool)
    prediction=base.get('prediction')
    explanation = (f'{mode} · {stat} : {current:g} → minimum {goal:g}. '
                   f'{rune} : gain nominal +{ref.gain:g}, poids {ref.weight:g}, reliquat {pool:g}. '
                   f'Poids non couvert par le reliquat : {exposure:g} (exposition, pas perte prédite). '
                   f'Type : {kind}. ')
    if natural_max is None or not profile_complete:
        explanation += 'Profil naturel incomplet : absence de ligne et légalité globale non certifiées. '
    if kind in ('exo', 'over'):
        explanation += 'Finition fragile : les poses suivantes peuvent dégrader cet ajout. '
    explanation += 'Classement par progression vers le jet souhaité, palier de rune, équilibre des lignes et protection du jet. '
    if prediction is not None:
        explanation+=(f"Modèle vidéo estimé : SC {prediction['SC']:.2f} %, SN {prediction['SN']:.2f} %, EC {prediction['EC']:.2f} %. "
                      f"Calibration : {prediction['calibration_n']} résultats réels comparables ; "
                      + '; '.join(prediction['assumptions'])+'. ')
    n = obs['n'] if obs else 0
    if n:
        explanation += f'{n} observations agrégées : descriptives, non utilisées comme probabilités du prochain essai. '
    if contextual:
        explanation += (f"Classement ajusté par {contextual['n']} observations locales de ce même état de départ, "
                        "avec une influence limitée et une borne de confiance prudente. "
                        "Ces mesures OCR restent exploratoires, sans garantie de réussite. ")
    if source_comparison['discordant']:
        explanation+='Écart entre les relevés Dofocus et les observations réelles comparables : fiabilité à vérifier. '
    if len(source_comparison['sources'])==2:
        explanation+='Référence simulée et observations réelles croisées dans un seul ajustement, sans double comptage. '
    if source_comparison['weights']=={'simulation':.4,'real':.6}:
        explanation+='Pondération du conseil : 40 % simulations, 60 % statistiques réelles comparables. '
    elif source_comparison['fallback']=='simulation_only':
        explanation+='Statistiques réelles comparables insuffisantes : simulation seule provisoirement (réglage prévu : 40 % simulations, 60 % réel). '
    if experience:
        explanation+=(f"Ajustement par l’expérience locale : {experience['n']} tentative(s) comparable(s), "
            f"dont {experience.get('exact',0)} au même état exact. Influence progressive et limitée ; "
            "score indicatif, sans probabilité de réussite déduite de ces voisins. ")
    if local and not local['blocked']:
        display=local['display']
        explanation+=(f"Calcul du modèle local Dofocus : SC {display['SC']} %, SN {display['SN']} %, EC {display['EC']} %. "
            "Simulation hors ligne, pas une probabilité officielle du jeu. ")
        outlook=local.get('outlook')
        if outlook:
            explanation+=(f"{outlook['trials']} essais virtuels pour cette rune : perte moyenne de progression cible "
                f"{outlook['mean_target_loss']:.2f} points de poids. Ces essais ne sont pas des tentatives réelles. ")
        sequence=sequence_measurement(local)
        if sequence:
            calibration=sequence.get('calibration')
            if calibration:
                explanation+=(f"Première pose calibrée avec {calibration['observations']} observations comparables ; "
                    "mélange 60 % réel / 40 % modèle, correction réduite selon la fiabilité. ")
                if calibration['discordant']:
                    explanation+="Écart détecté entre modèle et observations : correction prudente, mécanisme des pertes non calibré. "
            explanation+=(f"Anticipation sur {sequence['horizon']} poses : {sequence['completed']}/{sequence['trials']} "
                "suites virtuelles ont atteint toutes les cibles. Les poses suivantes sont adaptées aux résultats ; "
                "ce bilan court du simulateur n’est pas un taux de réussite en jeu. ")
        trained=local.get('trained_policy')
        if trained:
            explanation+=(f"Entraînement compatible : {trained['episodes']} sessions virtuelles ; "
                "ajustement appliqué uniquement dans la part simulation du conseil. ")
    if recorded and not recorded['blocked']:
        sampled=recorded
        display=sampled['display']
        explanation+=(f"Simulation Dofocus relevée le {sampled['captured_on']}, même jet complet et même reliquat : "
                      f"SC {display['SC']} %, SN {display['SN']} %, EC {display['EC']} %. "
                      "Valeurs affichées arrondies, non validées comme probabilités du jeu. ")
    elif not local:
        explanation+='Aucun relevé Dofocus pour ce contexte exact : pourcentages non disponibles. '
    for note in risk_notes(current,current+ref.gain,ref.weight,pool,
                          natural_max.get(stat,0) if natural_max is not None and profile_complete else None):
        explanation+=note+' '
    explanation+='Politique Forgely : gardes conservatrices de plafond par ligne et d’exos cumulés à 101 ; pas une formule Dofocus publiée. '
    explanation+='Choix de rune indicatif selon l’objectif, sans garantie de réussite.'
    from forgely_reasoning import explain_choice, strategic_options
    reasoning=explain_choice(rune,jets,targets,natural_max,pool)
    strategy_options=strategic_options(jets,targets,natural_max,pool)
    if reasoning:explanation+=' '+reasoning
    preparatory=[o for o in strategy_options if o['experimental']]
    if preparatory:
        explanation+=' Options préparatoires à comparer dans l’entraîneur : '+', '.join(o['rune'] for o in preparatory[:3])+'. Leur gain sur le jet complet n’est pas démontré ; elles ne remplacent pas ce conseil.'
    pricing=None
    if price_book is not None:
        from forgely_pricing import estimate_line_cost
        probabilities=(sampled or {}).get('probabilities',{})
        sc,sn=probabilities.get('SC'),probabilities.get('SN')
        success=(sc+sn)/100 if finite_number(sc) and finite_number(sn) else None
        pricing=estimate_line_cost(rune,current=current,target=goal,gain=ref.gain,success=success,book=price_book)
        if pricing['unit_price_kamas'] is None:
            explanation+=' Prix unitaire inconnu pour cette rune. '
        else:
            explanation+=f" Prix moyen unitaire : {pricing['unit_price_kamas']:g} kamas ({price_book.server}, relevé du {price_book.observed_on})."
            if pricing['estimated_cost_kamas'] is not None:
                explanation+=f" Remontée de cette ligne : environ {pricing['estimated_cost_kamas']:.0f} kamas à taux constant, hors pertes collatérales et réparations ; estimation indicative."
    alternatives = [{'rune': row[1], 'stat': row[2], 'score': round(row[0], 6),'prediction':row[5].get('prediction'),
                     **({'price':price_book.unit_price(row[1])} if price_book is not None else {})} for row in options[:5]]
    return Proposal(rune, kind, f'À envisager : {rune}', explanation, 'Dofocus · référence de base ; classement Forgely',
                    {'observed': obs, 'benchmark': base,'dofocus':recorded, 'local_simulation':local,'prediction':prediction,
                     **({'matrix':matrix} if matrix is not None else {}),
                     'contextual': contextual,'experience':experience,
                     'source_comparison':source_comparison,
                     'reasoning':{'version':'fm-reasoning-1','selected':reasoning,'options':strategy_options},
                     **({'pricing':pricing} if pricing is not None else {}),
                     'objective': {'mode': mode,
                                   'exposed_weight': exposure, 'alternatives': alternatives,
                                   'sequence': sequence_measurement(local), 'goal_probability': None}}, n)
