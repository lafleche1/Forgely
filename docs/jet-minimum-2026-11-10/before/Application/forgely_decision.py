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
    if current<0 and proposed<=0 and natural_max is not None and stat in natural_max:
        return 'reduction_malus'
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
    posterior_n=sampled.get('empirical_n') if isinstance(sampled,dict) else None
    if type(posterior_n) is int and posterior_n>=30 and simulation_factor is not None:
        from forgely_fm_model import PRIOR_STRENGTH
        effective={'simulation':PRIOR_STRENGTH/(PRIOR_STRENGTH+posterior_n),'real':posterior_n/(PRIOR_STRENGTH+posterior_n)}
        factor=simulation_factor;real_factor=None;fallback='shared_posterior'
        sources=[s for s in sources if s not in ('observations_joueurs_contextuelles','experience_joueurs_locale')]
        sources.append('calibration_reelle_deja_incluse')
    elif simulation_factor is None and real_factor is None:
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


def tier_comparison(jets, targets, natural_max, pool, eligible, *, level=None, profile_complete=True, context_for=None):
    """Compare even excluded tiers; nominal SN gain is an upper estimate.

    Loss locations and partial SN gains are unknown without qualified transitions.
    Consequently this must never be presented as net expected target progression.
    """
    from forgely_predictive import estimate, calibrate
    signed=any(v<0 for mapping in (jets,targets,natural_max or {}) for v in mapping.values())
    result = {}
    for stat, goal in targets.items():
        if jets[stat] >= goal:
            continue
        rows = []
        for rune in RUNE_CHOICES.get(stat, ()):
            ref = reference(rune)
            if ref.gain is None or ref.weight is None:
                continue
            prediction = (None if signed else calibrate(estimate(jets, natural_max, rune, level=level,
                profile_complete=profile_complete), context_for(rune) if context_for else None))
            probability = ((prediction['SC'] + prediction['SN']) / 100 if prediction else None)
            proposed = jets[stat] + ref.gain
            modified = dict(jets, **{stat: proposed})
            legal = constraints(modified, natural_max, complete_profile=profile_complete)
            reason = None
            if rune not in eligible:
                reason = (legal['reason'] if legal['valid'] is False else
                    'Dépasse la cible / le maximum naturel : over non demandé' if proposed > goal else
                    'Exclue par les contraintes ou les sources disponibles')
            rows.append(dict(rune=rune, gain=ref.gain, weight=ref.weight,
                resulting_value=proposed, eligible=rune in eligible, exclusion_reason=reason,
                probabilities={o:prediction[o] for o in ('SC','SN','EC')} if prediction else None,
                source='nominal_signed' if signed else 'provisional_shared_model',
                expected_capped_progress=min(ref.gain, goal-jets[stat])*probability if probability is not None else None,
                expected_net_progress=None,
                degradation_exposure=max(0., ref.weight-pool),
                note='Gain nominal plafonné à la cible ; SN partiels et pertes collatérales inconnus. Exposition hors puits, pas perte moyenne.'))
        result[stat] = rows
    return result


def candidates(jets, targets, natural_max=None, pool=None, counts_for=None, *,
               mode='Chances maximales', prices=None, remaining_budget=None, profile_complete=True,item=None,
               contextual_for=None,experience_for=None,simulation_for=None,allow_minimal_overshoot=False,price_book=None,
               level=None,context_for=None,decision_trace=None):
    # prices/remaining_budget are ignored compatibility inputs.
    mode = objective_mode(mode)
    # Currency inputs are compatibility-only under the target-first contract.
    price_book = None
    if (not targets or not jets or pool is None or not finite_number(pool, nonnegative=True)
            or any(stat not in jets for stat in targets)
            or any(not finite_number(v) for v in (*jets.values(), *targets.values()))
            or (natural_max is not None and any(not finite_number(v) for v in natural_max.values()))):
        return []
    signed=any(v<0 for mapping in (jets,targets,natural_max or {}) for v in mapping.values())
    pending_natural = any(current < targets.get(stat, current) and current < natural_max[stat]
                          for stat, current in jets.items() if natural_max and stat in natural_max)
    repair_deficits = {
        stat: (min(goal, natural_max[stat]) - jets[stat]) * WEIGHT_PER_POINT[stat]
        for stat, goal in targets.items()
        if natural_max and stat in natural_max and stat in WEIGHT_PER_POINT
        and jets[stat] < min(goal, natural_max[stat])
    }
    repair_scale = max(repair_deficits.values(), default=1.)
    mixed_weight_repair = len({WEIGHT_PER_POINT[s] for s in repair_deficits}) > 1
    source_context=lookup_context(item,jets,pool) if item and not signed else None
    available = []
    planning = {}
    real_adjustments = {}
    for stat, goal in targets.items():
        current = jets[stat]
        if current >= goal:
            continue
        for rune in RUNE_CHOICES.get(stat, ()):
            ref = reference(rune)
            if ref.weight is None or ref.gain is None:
                continue
            proposed = current + ref.gain
            # Targets are minima. The smallest tier may finish a natural line
            # when its indivisible gain crosses the cap; all legality checks
            # below still apply and this remains a fragile over, not a repair.
            smallest=min((reference(r).gain for r in RUNE_CHOICES.get(stat,())
                          if reference(r).gain is not None),default=0)
            minimal_finish=(ref.gain==smallest and (
                signed and current<goal and goal-current<smallest or
                allow_minimal_overshoot and natural_max is None or
                profile_complete and natural_max is not None and stat in natural_max
                and current<goal<=natural_max[stat] and goal-current<smallest))
            # A larger tier can leave a sacrificial surplus while
            # other targeted lines still need repair. Never bank it as pool.
            uncovered_pa=bool(natural_max and stat in natural_max and rune.startswith('Pa ')
                and stat in ('Force','Intelligence','Chance','Agilité')
                and current>=max(20,.9*natural_max[stat]))
            reserve_over=bool(profile_complete and natural_max and stat in natural_max
                and stat in ('Vitalité','Force','Intelligence','Chance','Agilité','Sagesse')
                and rune.startswith(('Pa ','Ra ')) and (ref.weight<=pool or uncovered_pa)
                and current<goal==natural_max[stat]<proposed
                and any(s!=stat for s in repair_deficits))
            if proposed > goal and not (minimal_finish or reserve_over or (natural_max is not None and stat in natural_max
                                         and proposed <= natural_max[stat])):
                continue
            modified = dict(jets)
            modified[stat] = proposed
            checked = constraints(modified, natural_max, complete_profile=profile_complete)
            if checked['valid'] is False:
                continue
            limit=line_limit(item,stat) if item else None
            if limit is not None and proposed>limit:continue
            local=simulation_for(rune) if simulation_for and not signed else None
            if local and local.get('blocked'):continue
            # Recorded Dofocus captures remain descriptive references. Active
            # ranking uses the shared model, never an older matrix probability.
            sampled=local
            if sampled and sampled.get('blocked'):continue
            if sampled and sampled.get('kind')!='local_dofocus_model' and not isinstance(sampled.get('display'),dict):
                sampled=None
            kind = classify(stat, current, proposed, natural_max, profile_complete=profile_complete)
            counts = counts_for(rune) if counts_for else None
            obs = empirical(counts) if counts is not None else None
            base={'SC':None,'SN':None,'EC':None,'kind':'dofocus_non_documente',
                  'note':'Aucun taux fixe extrapolé depuis une autre source.'}
            base.update(signed_profile=signed,constraint_status=checked)
            from forgely_predictive import estimate,calibrate
            calibration=context_for(rune) if context_for else None
            prediction=(None if signed else calibrate(
                estimate(jets,natural_max,rune,level=level,profile_complete=profile_complete),calibration))
            if local and isinstance(local.get('prediction'),dict):
                prediction=local['prediction']
                if not prediction.get('calibration_n'):
                    prediction=calibrate(prediction,calibration)
            base['prediction']=prediction
            # Show verified comparable attempts even before calibration starts;
            # aggregate or nearby OCR experience must not inflate this count.
            real_counts=calibration.get('counts') if isinstance(calibration,dict) and calibration.get('verified') is True else None
            if isinstance(real_counts,dict):
                values=[real_counts.get(k,0) for k in ('SC','SN','EC')]
                if all(type(v) is int and v>=0 for v in values):
                    base['real_observations']=sum(values)
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
            if kind == 'fm_classique' and stat in repair_deficits:
                # Compare restored target mass in common units. Fraction of a
                # line completed otherwise rewards finishing tiny light gaps
                # while substantial weighted natural deficits remain.
                progress = min(ref.gain * WEIGHT_PER_POINT[stat], repair_deficits[stat]) / repair_scale
                balance = .15 * repair_deficits[stat] / repair_scale
            non_sc=(100-prediction['SC'])/100 if video_rank else 1.
            utility = (progress + balance) / (1 + .7 * exposure*non_sc + .5 * tier_pressure + overshoot)
            utility /= 1 + finish_penalty
            heuristic_score=utility-.04*ref.weight/100-finish_penalty
            record=contextual_for(rune) if contextual_for else None
            experience=experience_for(rune) if experience_for else None
            combined=combine_candidate_evidence(sampled,record,experience=experience,local=local)
            utility*=combined['factor']
            if prediction is not None and sampled is None:
                utility*=(prediction['SC']+prediction['SN'])/100
            score = utility - .04 * ref.weight / 100 - finish_penalty
            sequence=sequence_measurement(local)
            if sequence is not None:planning[rune]=sequence
            trace=dict(heuristic_score=heuristic_score,evidence=combined,evidence_score=score,
                       reserve_over=reserve_over,
                       weighted_repair=mixed_weight_repair and kind == 'fm_classique',
                       weighted_deficit=repair_deficits.get(stat, 0.),
                       sequence_available=sequence is not None,sequence_used=False,
                       phase_kept=False,final_rank=None)
            base['decision_trace']=trace
            if decision_trace is not None:decision_trace['candidates'][rune]=trace
            if combined['real_factor'] is not None and combined['simulation_factor']:
                # Real experience is a bounded relative correction, not a
                # competing immediate-progress score on a different scale.
                ratio=combined['real_factor']/combined['simulation_factor']
                real_adjustments[rune]=.4+.6*min(1.1,max(.85,ratio))
            available.append((score, rune, stat, kind, ref, base, obs,
                              extra_mass(modified, natural_max), current, goal))
    from forgely_finish_paths import compare_finish_paths
    finish_paths = compare_finish_paths(available,jets,targets,natural_max,pool,
        level=level,profile_complete=profile_complete)
    for row in available:
        if row[1] in finish_paths:
            row[5]['decision_trace']['nominal_sequence'] = finish_paths[row[1]]
    # Restore available targeted natural lines before final over/exo attempts.
    if pending_natural and any(row[3]=='fm_classique' for row in available):
        available=[row for row in available if row[3] not in ('exo','over')
                   or row[5]['decision_trace'].get('reserve_over')]
    if available and all(row[1] in planning for row in available):
        # Calibrated rollouts already mix real/model root outcomes: no second
        # application of the real share. Uncalibrated local experience stays bounded.
        available=[(planning[row[1]]['value']*(1. if planning[row[1]].get('calibration')
                    else real_adjustments.get(row[1],1.)),*row[1:]) for row in available]
        for row in available:
            row[5]['decision_trace'].update(sequence_used=True,sequence_score=row[0],
                sequence_calibrated=bool(planning[row[1]].get('calibration')),
                sequence_correction=1. if planning[row[1]].get('calibration') else real_adjustments.get(row[1],1.))
        validated={entry['validation'].get('selected') for entry in planning.values()
                   if isinstance(entry.get('validation'),dict) and entry['validation'].get('accepted')}
        winner=next(iter(validated)) if len(validated)==1 else None
        from forgely_pricing import price_ties
        def priority(row):
            return (row[1]!=winner if winner else False,-row[0],planning[row[1]]['mean_steps'])
        from forgely_pricing import economic_scores
        available=economic_scores(available,price_book,mode)
        ordered=sorted(available,key=lambda row:(*priority(row),row[1]))
        ordered=price_ties(ordered,price_book,priority=priority)
        for rank,row in enumerate(ordered,1):
            row[5]['decision_trace'].update(economic_score=row[0],rank_before_phase=rank,
                validated_sequence_winner=row[1]==winner)
        return ordered
    from forgely_pricing import price_ties,economic_scores
    available=economic_scores(available,price_book,mode)
    ordered=price_ties(sorted(available, key=lambda x: (-x[0], x[1])),price_book)
    for rank,row in enumerate(ordered,1):
        row[5]['decision_trace'].update(economic_score=row[0],rank_before_phase=rank)
    return ordered


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
    # Currency inputs are compatibility-only under the target-first contract.
    price_book = None
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
    signed=any(v<0 for mapping in (jets,targets,natural_max or {}) for v in mapping.values())
    if signed:
        # Live signed advice is nominal, not a restored virtual-loss model.
        simulation_for=None
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
    from forgely_training import COPILOT_SELECTOR_VERSION
    decision_trace=dict(selector_version=COPILOT_SELECTOR_VERSION,selected=None,candidates={},
                        pool_policy='conservative_no_free_weight',mode=mode,
                        contract='target-first-2026-11-08',
                        order=['legality','natural_targets','evidence_or_sequences','pool_preference','final_ranking'])
    options = candidates(jets, targets, natural_max, pool, counts_for, mode=mode,
                         profile_complete=profile_complete,item=item,
                         contextual_for=measured_for,experience_for=experienced_for,simulation_for=simulated_for,
                         allow_minimal_overshoot=allow_minimal_overshoot,price_book=price_book,level=level,context_for=context_for,
                         decision_trace=decision_trace)
    had_candidates=bool(options)
    comparison=tier_comparison(jets,targets,natural_max,pool,{r[1] for r in options},
        level=level,profile_complete=profile_complete,context_for=context_for)
    matrix=None
    if predictive_policy:
        from forgely_predictive import rank_options,matrix_payload
        options,meta=rank_options(options,jets,natural_max,pool,profile_complete)
        matrix=matrix_payload(options,jets,natural_max,pool,meta)
        decision_trace['phase']=meta
    for rank,row in enumerate(options,1):
        row[5]['decision_trace'].update(phase_kept=True,final_rank=rank)
    if not options:
        return Proposal(None,'bloqué','Aucune rune compatible avec la phase de puits' if matrix and had_candidates else 'Aucune rune compatible avec les cibles et limites',
                        matrix['reason'] if matrix and had_candidates else 'Vérifie les valeurs cibles, les bornes naturelles, les malus et les plafonds de lignes.',
                        'matrice utilisateur' if matrix else 'aucune',{'matrix':matrix,'decision_trace':decision_trace})
    score, rune, stat, kind, ref, base, obs, weight, current, goal = options[0]
    decision_trace['selected']=rune
    recorded=lookup(item,jets,pool,rune) if item and not signed else None
    local=simulated_for(rune)
    sampled=local
    contextual = contextual_measurement(measured_for(rune))
    experience=experienced_for(rune) if contextual is None else None
    source_comparison=combine_candidate_evidence(sampled,measured_for(rune),experience=experience,local=local)
    from forgely_pool_ledger import attempted_charge
    effective_charge = attempted_charge(stat,current,ref.gain,ref.weight)
    exposure = max(0., (ref.weight if effective_charge is None else effective_charge) - pool)
    prediction=base.get('prediction')
    explanation = (f'{mode} · {stat} : {current:g} → minimum {goal:g}. '
                   f'{rune} : gain nominal +{ref.gain:g}, poids {ref.weight:g}, reliquat {pool:g}. '
                   f'Poids non couvert par le reliquat : {exposure:g} (exposition, pas perte prédite). '
                   f'Type : {kind}. ')
    if signed:
        explanation+=('Profil avec malus pris en charge par classement nominal des runes. '
            'Les signes et les cibles sont conservés. Probabilités SC/SN/EC et pertes sur malus '
            'non extrapolées ; aucune simulation automatique. La charge de pose ne '
            'préjuge pas du débit net du puits. '
            'La suppression d’un malus ne constitue pas du reliquat acquis. ')
        if effective_charge is not None:
            explanation+=(f'Charge de pose hors SC : {effective_charge:g} ; '
                'le débit net dépend des pertes constatées. Les malus remontés peuvent '
                'se dégrader même avec du puits disponible. ')
        if base['constraint_status']['valid'] is None:
            explanation+='Les contraintes spécifiques des lignes signées restent partiellement non vérifiables. '
    if natural_max is None or not profile_complete:
        explanation += 'Profil naturel incomplet : absence de ligne et légalité globale non certifiées. '
    if kind in ('exo', 'over'):
        explanation += 'Finition fragile : les poses suivantes peuvent dégrader cet ajout. '
    if base.get('decision_trace',{}).get('reserve_over'):
        explanation+=(f'Over de réserve : {current:g} → {current+ref.gain:g}. '
                      'Surplus sacrifiable pendant les remontées restantes ; ce surplus ne constitue pas du puits acquis. ')
    elif (natural_max and stat in natural_max and current<goal<=natural_max[stat]<current+ref.gain):
        explanation+=(f'Finition par la plus petite rune : {current:g} → {current+ref.gain:g}, '
                      f"soit un over de {current+ref.gain-natural_max[stat]:g} au-dessus du maximum naturel. ")
    explanation += 'Classement par progression vers le jet souhaité, palier de rune, équilibre des lignes et protection du jet. '
    excluded_tiers=[r for r in comparison.get(stat,[]) if not r['eligible']]
    if excluded_tiers:
        explanation+='Comparaison des paliers : '+ '; '.join(
            f"{r['rune']} → {r['resulting_value']:g} : {r['exclusion_reason']}" for r in excluded_tiers)+'. '
    explanation+='L’espérance nette de progression reste inconnue sans distribution fiable des pertes et des gains partiels. '
    if prediction is not None:
        explanation+=(f"Modèle FM partagé estimé : SC {prediction['SC']:.2f} %, SN {prediction['SN']:.2f} %, EC {prediction['EC']:.2f} %. "
                      f"Calibration : {prediction['calibration_n']} résultats réels comparables ; "
                      + '; '.join(prediction['assumptions'])+'. ')
    n = obs['n'] if obs else 0
    if n:
        explanation += f'{n} observations agrégées : descriptives, non utilisées comme probabilités du prochain essai. '
    if contextual and source_comparison['fallback']!='shared_posterior':
        explanation += (f"Classement ajusté par {contextual['n']} observations locales de ce même état de départ, "
                        "avec une influence limitée et une borne de confiance prudente. "
                        "Ces mesures OCR restent exploratoires, sans garantie de réussite. ")
    elif source_comparison['fallback']=='shared_posterior':
        explanation+='Les observations réelles qualifiées sont déjà intégrées une seule fois dans le modèle ; aucun second ajustement par ces mêmes essais. '
    if source_comparison['discordant']:
        explanation+='Écart entre le modèle partagé et les observations réelles comparables : fiabilité à vérifier. '
    if len(source_comparison['sources'])==2:
        explanation+='Référence simulée et observations réelles croisées dans un seul ajustement, sans double comptage. '
    if source_comparison['weights']=={'simulation':.4,'real':.6}:
        explanation+='Ajustement intermédiaire du score : 40 % simulations, 60 % données réelles comparables ; ce mélange ne décrit pas à lui seul le choix final. '
    elif source_comparison['fallback']=='simulation_only':
        explanation+='Statistiques réelles comparables insuffisantes : simulation seule provisoirement (réglage prévu : 40 % simulations, 60 % réel). '
    if experience and source_comparison['fallback']!='shared_posterior':
        explanation+=(f"Ajustement par l’expérience locale : {experience['n']} tentative(s) comparable(s), "
            f"dont {experience.get('exact',0)} au même état exact. Influence progressive et limitée ; "
            "score indicatif, sans probabilité de réussite déduite de ces voisins. ")
    if local and not local['blocked']:
        display=local['display']
        explanation+=(f"Calcul du modèle FM partagé : SC {display['SC']} %, SN {display['SN']} %, EC {display['EC']} %. "
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
                    "calibration commune réduite selon les effectifs vérifiés. ")
                if calibration['discordant']:
                    explanation+="Écart détecté entre modèle et observations : correction prudente ; les pertes sans observations suffisantes restent estimées. "
            explanation+=(f"Anticipation sur {sequence['horizon']} poses : {sequence['completed']}/{sequence['trials']} "
                "suites virtuelles ont atteint toutes les cibles. Les poses suivantes sont adaptées aux résultats ; "
                "ce bilan court du simulateur n’est pas un taux de réussite en jeu. ")
        trained=local.get('trained_policy')
        if trained:
            explanation+=(f"Entraînement compatible : {trained['episodes']} sessions virtuelles ; "
                "ajustement appliqué uniquement dans la part simulation du conseil. ")
    if recorded and not recorded['blocked']:
        display=recorded['display']
        explanation+=(f"Référence historique Dofocus relevée le {recorded['captured_on']}, même jet complet et même reliquat : "
                      f"SC {display['SC']} %, SN {display['SN']} %, EC {display['EC']} %. "
                      "Référence descriptive arrondie, non utilisée à la place du modèle partagé. ")
    elif not local:
        explanation+='Aucun relevé Dofocus pour ce contexte exact : pourcentages non disponibles. '
    for note in ([] if signed else risk_notes(current,current+ref.gain,ref.weight,pool,
                          natural_max.get(stat,0) if natural_max is not None and profile_complete else None)):
        explanation+=note+' '
    explanation+='Politique Forgely : gardes conservatrices de plafond par ligne et d’exos cumulés à 101 ; pas une formule Dofocus publiée. '
    explanation+='Choix de rune indicatif selon l’objectif, sans garantie de réussite.'
    from forgely_reasoning import explain_choice, strategic_options
    reasoning=explain_choice(rune,jets,targets,natural_max,pool) if not signed else ''
    strategy_options=strategic_options(jets,targets,natural_max,pool)
    if reasoning:explanation+=' '+reasoning
    preparatory=[o for o in strategy_options if o['experimental']]
    if preparatory:
        explanation+=' Options préparatoires à comparer dans l’entraîneur : '+', '.join(o['rune'] for o in preparatory[:3])+'. Leur gain sur le jet complet n’est pas démontré ; elles ne remplacent pas ce conseil.'
    selected_trace=decision_trace['candidates'][rune]
    nominal=selected_trace.get('nominal_sequence')
    if nominal:
        explanation+=' Chemin nominal comparé : '+' → '.join(nominal['path'])+'. '
        explanation+='Coût indicatif en essais et exposition, sans prix ; pertes collatérales inconnues. Recalcul nécessaire après chaque résultat. '
    explanation+=' Classement final : '
    if matrix:
        explanation+=matrix['reason']+' Classement selon les sources disponibles. '
    else:
        explanation+='score disponible après contraintes, sans prix. '
    if selected_trace['sequence_used']:
        explanation+='Le score de séquence remplace le score immédiat ; les sources ne sont pas appliquées une seconde fois. '
    explanation+=(f"Score initial {selected_trace['heuristic_score']:.4f}, "
                  f"après sources {selected_trace['evidence_score']:.4f}, "
                  f"avant phase {selected_trace['economic_score']:.4f} ; rang final 1/{len(options)}. ")
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
    return Proposal(rune, kind, f'À envisager : {rune}', explanation,
                    'Classement nominal signé · taux indisponibles' if signed else 'Modèle FM partagé · classement Forgely',
                    {'observed': obs, 'benchmark': base,'dofocus':recorded, 'local_simulation':local,'prediction':prediction,
                     'signed_profile':signed,
                     'attempted_weight':effective_charge,
                     'tier_comparison':comparison,
                     **({'matrix':matrix} if matrix is not None else {}),
                     'contextual': contextual,'experience':experience,
                     'source_comparison':source_comparison,
                     'decision_trace':decision_trace,
                     'reasoning':{'version':'fm-reasoning-1','selected':reasoning,'options':strategy_options},
                     **({'pricing':pricing} if pricing is not None else {}),
                     'objective': {'mode': mode,
                                   'exposed_weight': exposure, 'alternatives': alternatives,
                                   'sequence': sequence_measurement(local), 'goal_probability': None}}, n)
