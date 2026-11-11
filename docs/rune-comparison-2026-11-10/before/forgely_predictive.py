"""User-requested pool policy; probability bands are explicit hypotheses.

No actual result, hidden baseline, rune price or guaranteed loss is invented.
"""
from decimal import Decimal
from forgely_dofocus import WEIGHT_PER_POINT,reference,canonical_stat

LIGHT={'Vitalité','Force','Intelligence','Chance','Agilité'}
INTERMEDIATE={'Sagesse','Soins','Dommages Critiques'}


def number(value):
    return format(Decimal(str(value)).normalize(),'f') if value is not None else 'inconnu'


def saturation(jets,natural):
    if not natural or not set(natural)<=jets.keys():return None
    positive={s:m for s,m in natural.items() if m>0}
    if not positive or any(s not in WEIGHT_PER_POINT for s in positive):return None
    maximum=sum(m*WEIGHT_PER_POINT[s] for s,m in positive.items())
    actual=sum(min(m,max(0,jets[s]))*WEIGHT_PER_POINT[s] for s,m in positive.items())
    return actual/maximum if maximum else None


def success_band(stat,current,gain,natural,sat,profile_complete=True):
    """Historical API only; active ranking/display use the shared prediction."""
    if natural is None:return None
    stat=canonical_stat(stat)
    if stat not in natural:
        if not profile_complete:return None
        return (1,1) if stat in ('PA','PM','Portée') else (10,15)
    maximum=natural[stat];proposed=current+gain
    if maximum<=0:return None
    if proposed>maximum:
        return (20,30) if (proposed-maximum)/maximum<.2 else (10,15)
    if sat is None:return None
    return (30,45) if sat>=.9 else (60,70)


def pool_phase(pool):
    if pool is None:return 'unknown'
    if 0<pool<1:return 'fractional'
    if pool>=51:return 'large'
    if pool>=20:return 'medium'
    if 0<pool<=5:return 'critical'
    if pool>0:return 'low'
    return 'zero'


def rank_options(options,jets,natural,pool,profile_complete=True):
    phase=pool_phase(pool);sat=saturation(jets,natural) if profile_complete else None
    rows=list(options);why=''
    legal=list(rows)
    original_order={row[1]:i for i,row in enumerate(rows)}
    # A nominal budget is not evidence of successful progression. Preserve
    # comparable full-target rollouts before considering a pool repair plan.
    if rows and all(r[5].get('decision_trace', {}).get('sequence_used') is True for r in rows):
        return rows, dict(phase=phase, saturation=sat,
            reason='Priorite au jet complet : classement des sequences conserve ; phase de puits descriptive.',
            profile_complete=profile_complete, fallback=False, preferred=[], excluded=[],
            sequence_preserved=True)
    paths={r[1]:r[5].get('decision_trace',{}).get('nominal_sequence') for r in rows}
    paths={r:p for r,p in paths.items() if p}
    dominated=set()
    for stat in {r[2] for r in rows if r[1] in paths}:
        group=[r for r in rows if r[2]==stat and r[1] in paths]
        winner=min(group,key=lambda r:(paths[r[1]]['cost'],-r[0],r[1]))
        dominated.update(r[1] for r in group if paths[r[1]]['cost']>paths[winner[1]]['cost']+1e-9)
    repair_rows=[r for r in rows if r[1] not in dominated]
    reserves=[r for r in rows if r[5].get('decision_trace',{}).get('reserve_over')
              and r[4].weight<=pool]
    heavy_covered=any(r[3]=='fm_classique' and r[4].weight<=pool
                      and r[2] not in LIGHT for r in rows)
    if reserves and not heavy_covered:
        # Prefer the least surplus mass: retain a modest reserve rather than
        # consuming the entire pool on an unnecessarily large over.
        from forgely_rules import WEIGHTS
        reserve=min(reserves,key=lambda r:((r[8]+r[4].gain-natural[r[2]])*WEIGHTS[r[2]],
                                          r[4].weight,-r[0],r[1]))
        rows.sort(key=lambda r:(r[1]!=reserve[1],original_order[r[1]]))
        return rows,dict(phase=phase,saturation=sat,profile_complete=profile_complete,
            reason='Over de réserve couvert par le puits ; surplus sacrifiable, jamais compté comme reliquat acquis.',
            fallback=False,preferred=[reserve[1]],excluded=[],reserve_over_preferred=True)
    # Near a natural cap, a Pa may be more plausible than repeatedly trying
    # a saturated simple rune, even without enough pool. Keep the exposure
    # explicit and require a better shared prediction than natural repairs.
    natural_success=max((_shared_success(r) for r in rows if r[3]=='fm_classique'),default=-1)
    exposed_reserves=[r for r in rows if r[5].get('decision_trace',{}).get('reserve_over')
                     and r[4].weight>pool and _shared_success(r)>natural_success]
    if exposed_reserves:
        reserve=min(exposed_reserves,key=lambda r:(-_shared_success(r),r[4].weight,-r[0],r[1]))
        rows.sort(key=lambda r:(r[1]!=reserve[1],original_order[r[1]]))
        return rows,dict(phase=phase,saturation=sat,profile_complete=profile_complete,
            reason='Pa de réserve près du maximum : estimation supérieure aux runes naturelles disponibles ; poids hors puits exposé, pertes collatérales inconnues.',
            fallback=False,preferred=[reserve[1]],excluded=[],reserve_over_preferred=True)
    if pool is not None and pool>=1:
        from forgely_pool_repair import pool_repair_plan
        plan,spent=pool_repair_plan(repair_rows,pool,natural)
        if plan:
            rows.sort(key=lambda row:(row[1]!=plan[0],original_order[row[1]]))
            return rows,dict(phase=phase,saturation=sat,
                reason='Utiliser le reliquat pour remonter le jet cible ; suite indicative recalculée après chaque résultat.',
                profile_complete=profile_complete,fallback=False,
                preferred=list(dict.fromkeys(plan)),excluded=[],pool_repair_preferred=True,
                pool_repair_sequence=list(plan),pool_repair_weight=spent,
                pool_repair_remainder=float(Decimal(str(pool))-Decimal(str(spent))))
    if paths:
        rows.sort(key=lambda r:(r[1] in dominated,original_order[r[1]]))
        return rows,dict(phase=phase,saturation=sat,profile_complete=profile_complete,
            reason='Comparer les chemins de finition : essais et exposition estimés, pertes collatérales inconnues ; recalcul après chaque pose.',
            fallback=False,preferred=[],excluded=[],nominal_paths=paths)
    if any(r[5].get('decision_trace', {}).get('weighted_repair') for r in rows):
        # Reserve coverage describes exposure; it must not eliminate weighted
        # natural repairs or replace their target value with next-rune odds.
        return rows, dict(phase=phase, saturation=sat,
            reason='Priorite aux reparations naturelles ponderees ; puits descriptif, exposition conservee.',
            profile_complete=profile_complete, fallback=False, preferred=[], excluded=[],
            weighted_repair_preserved=True)
    if phase=='fractional':
        why='Reliquat inférieur à 1 : comparer les remontées utiles sans exclure les runes de finition.'
    elif phase=='large':
        rows=[r for r in rows if (r[2] in ('PA','PM','Portée','Invocations','Dommages')
              or r[2].startswith('Dommages ') or r[2].startswith('% Résistance '))
              and natural is not None and r[2] in natural and r[8]<natural[r[2]]
              and r[4].weight<=pool]
        why='Très gros puits : préférence aux lignes lourdes naturelles couvertes.'
    elif phase=='medium':
        middle=[r for r in rows if r[2] in INTERMEDIATE and r[4].weight<=pool]
        rows=middle or [r for r in rows if r[4].weight<=pool]
        why='Puits moyen : sécuriser les lignes intermédiaires, puis comparer gain / poids consommé.'
    elif phase in ('low','critical'):
        rows=[r for r in rows if r[2] in LIGHT and r[4].weight<=max(1,min(3,pool))]
        why=('Puits 1–5 : petites runes préférées ; tout poids non couvert reste une exposition.'
             if phase=='critical' else 'Faible puits : préférence aux statistiques légères couvertes.')
    elif phase=='zero':
        cleanup=[r for r in rows if r[1].startswith('Ra ')] if sat is not None and sat<.75 else []
        rows=cleanup or rows
        why=('Hors puits : nettoyage risqué par une Ra compatible avec la cible. Une perte de ligne lourde reste seulement possible.'
             if cleanup else 'Hors puits : risque de pertes sur les autres lignes ; aucune création de puits prévisible.')
    fallback=bool(legal) and not rows
    if fallback:
        rows=legal
        why+=' Aucune rune préférée disponible : repli sur les cibles légales, avec exposition affichée.'
    def key(row):
        probability=_shared_success(row) if profile_complete else -1
        efficiency=row[4].gain/row[4].weight if phase=='medium' and row[4].weight else 0
        return (-probability,-efficiency,-row[0],original_order[row[1]])
    return sorted(rows,key=key),dict(phase=phase,saturation=sat,reason=why,profile_complete=profile_complete,
        fallback=fallback,preferred=[r[1] for r in rows] if not fallback else [],
        excluded=[r[1] for r in legal if r not in rows])


def option_payload(row,natural,sat,pool,profile_complete=True):
    _,rune,stat,kind,ref,_,_,_,current,goal=row
    p=Decimal(str(pool));weight=Decimal(str(ref.weight))
    probability=_shared_success(row) if profile_complete else -1
    prediction=row[5].get('prediction') or {}
    probabilities={k:prediction[k] for k in ('SC','SN','EC')} if probability>=0 else None
    count=row[5].get('real_observations',prediction.get('calibration_n',0)) if probabilities else 0
    count=count if type(count) is int and count>=0 else 0
    community=prediction.get('kind')=='exo_lourd_reference_communautaire'
    finishing_over=bool(natural and stat in natural and current<goal<=natural[stat]<current+ref.gain)
    return dict(rune=rune,stat=stat,kind=kind,gain=ref.gain,weight=ref.weight,
                finishing_over=finishing_over,proposed=current+ref.gain,
                natural_over=current+ref.gain-natural[stat] if finishing_over else 0,
                probabilities=probabilities,real_observations=count,
                confidence=('non disponible' if probabilities is None else
                            'référence communautaire' if community and not count else
                            'calibrée, précision non validée' if prediction.get('calibration_n',0)>=30 else 'faible, modèle non calibré'),
                success_band=(probability,probability) if probability>=0 else None,
                success_outcomes=('SC uniquement' if probabilities and probabilities['SN']==0 else 'SC ou SN'),
                probability_source='shared_fm_model' if probability>=0 else 'unavailable',pool_SC=number(p),
                pool_SN_EC_without_losses=('inconnu' if row[5].get('signed_profile') else number(max(Decimal(0),p-weight))),
                exposed_weight=number(max(Decimal(0),weight-p)),
                gain_per_weight=ref.gain/ref.weight if ref.weight else None)


def _shared_success(row):
    from math import isfinite
    prediction=row[5].get('prediction')
    if not isinstance(prediction,dict):return -1
    sc,sn,ec=[prediction.get(k) for k in ('SC','SN','EC')]
    if any(type(v) not in (int,float) or not isfinite(v) or not 0<=v<=100 for v in (sc,sn,ec)):return -1
    if abs(sc+sn+ec-100)>1e-6:return -1
    return sc+sn


def matrix_payload(rows,jets,natural,pool,meta):
    values=[option_payload(r,natural,meta['saturation'],pool,meta['profile_complete']) for r in rows]
    optimal=values[0] if values else None
    # Preserve the advisor's complete-target ranking; diversify only the other
    # choices within its existing legality and phase guards.
    choices=[]
    if optimal:
        choices.append({**optimal,'role':'recommended','title':'Recommandée'})
        remaining=list({v['rune']:v for v in values[1:] if v['rune']!=optimal['rune']}.values())
        if remaining:
            prudent=min(remaining,key=lambda x:(float(x['exposed_weight']),x['weight']))
            safer=(float(prudent['exposed_weight']),prudent['weight']) < (float(optimal['exposed_weight']),optimal['weight'])
            choices.append({**prudent,'role':'prudent' if safer else 'alternative',
                            'title':'Moins exposée' if safer else 'Alternative'})
            remaining=[v for v in remaining if v['rune']!=prudent['rune']]
        if remaining:
            stronger=max(remaining,key=lambda x:x['weight'])
            heavier=stronger['weight']>optimal['weight']
            choices.append({**stronger,'role':'stronger' if heavier else 'alternative',
                            'title':'Plus forte' if heavier else 'Autre alternative'})
    alternative=max(values[1:],key=lambda x:(float(x['exposed_weight']),x['weight'])) if len(values)>1 else None
    return {**meta,'optimal':optimal,'alternative':alternative,'choices':choices,'natural_max':natural,
            'probability_source':'shared_fm_model'}


def report_measurements(proposal,jets,pool,*,readings=None,active=False):
    """Partial measurements may be displayed, never used to authorize advice."""
    if proposal.kind not in ('suspendu','calcul'):return jets or {},pool,'lu'
    from forgely_workshop_readings import WorkshopReadings
    if active and isinstance(readings,WorkshopReadings):
        states=readings.line_states
        visible={k:v for k,v in readings.display_jet.items() if states.get(k) in ('confirmed','offscreen')}
        return visible,readings.partial_pool,'provisoire · jet incomplet'
    return {},None,'non confirmé'


def report_text(proposal,jets,targets,natural,pool,*,pool_origin='lu',compact=False):
    if getattr(proposal,'kind',None)=='bloqué':
        reason=proposal.summary+'\n'+proposal.explanation
        if compact:
            return 'Puits '+number(pool)+' · Conseil indisponible\n'+reason
        return '[CONSEIL INDISPONIBLE]\n'+reason
    if getattr(proposal,'kind',None)=='calcul':
        reason=proposal.explanation or 'Jet et reliquat à confirmer'
        if compact:
            return 'Lecture à confirmer\n'+reason
        return '[LECTURE EN ATTENTE]\n'+reason+'\nAucune rune conseillée sans mesures confirmées.'
    data=(proposal.estimates or {}).get('matrix',{})
    signed=(proposal.estimates or {}).get('signed_profile',False)
    pricing=(proposal.estimates or {}).get('pricing')
    price_text=''
    if pricing:
        unit=pricing.get('unit_price_kamas')
        price_text=('Prix unitaire : inconnu' if unit is None else
            f"Prix unitaire : {number(unit)} kamas · {pricing['server']}")
        if not compact and unit is not None:
            price_text+=f" (relevé du {pricing['observed_on']})."
            estimate=pricing.get('estimated_cost_kamas')
            if estimate is not None:
                price_text+=f" Remontée indicative de cette ligne : {estimate:.0f} kamas, à taux constant, hors pertes et réparations."
    natural=natural or data.get('natural_max')
    rows=' · '.join(f'{s} {number(v)}/{number(natural.get(s)) if natural else "?"}' for s,v in jets.items()) or 'Jet en attente'
    state=f'[ÉTAT MATRICIEL]\n{rows}\nPuits : {number(pool)} ({pool_origin}).'
    sat=data.get('saturation',saturation(jets,natural))
    instability=None
    if natural and jets:
        instability=max(jets,key=lambda s:(max(0,jets[s]-natural.get(s,0))*100+
                         min(1,max(0,jets[s])/natural[s]) if natural.get(s,0)>0 else max(0,jets[s])*100)
                         *WEIGHT_PER_POINT.get(s,0),default=None)
    risk=data.get('reason') or proposal.summary
    prediction='[PRÉDICTION DU TOUR]\n'+risk
    if instability:prediction+=f' Ligne à surveiller : {instability} (indicateur de poids, pas une perte prédite).'
    if sat is not None:prediction+=f' Saturation indicative : {sat:.0%}.'
    def scenario(option,title):
        if not option:return f'{title} : aucune rune compatible — {proposal.summary}.'
        return (f'{title} : 1× Rune {option["rune"]} · +{number(option["gain"])} {option["stat"]} · poids {number(option["weight"])}. '
                f'{rates(option)} · {option.get("real_observations",0)} essais réels comparables. '
                f'Confiance : {option.get("confidence","non disponible")}. '
                f'Puits : SC {option["pool_SC"]} ; SN/EC sans perte {option["pool_SN_EC_without_losses"]}. '
                f'Poids non couvert : {option["exposed_weight"]} (exposition, pas perte prédite).')
    def rates(option):
        probabilities=option.get('probabilities')
        if not probabilities:return 'SC/SN/EC non disponibles'
        # Whole percentages avoid suggesting a precision this model has not earned.
        return ' · '.join(f'{k} ~{probabilities[k]:.0f} %' for k in ('SC','SN','EC'))
    choices=data.get('choices',[])
    pool_plan=''
    if data.get('pool_repair_sequence'):
        from collections import Counter
        runes=Counter(data['pool_repair_sequence'])
        pool_plan=('Remontée sur puits : '+', '.join(f'{rune} ×{count}' for rune,count in runes.items())+
                   f" · poids {number(data['pool_repair_weight'])}/{number(pool)}"+
                   f" · reste nominal {number(data['pool_repair_remainder'])}."+
                   ' Suite indicative, recalculée après chaque résultat.')
    caution=('Classement nominal ; probabilités et pertes sur malus inconnues, aucune simulation.' if signed else
             'Estimations expérimentales, pas des taux officiels ; arrondis indépendants.')
    recommendation='[RECOMMANDATION IA]\n'+caution+'\n'
    recommendation+=('\n'.join(scenario(x,x['title']) for x in choices) if choices else proposal.summary)
    if compact:
        qualifier=' · provisoire' if pool is not None and pool_origin.startswith('provisoire') else ''
        return ('Puits '+number(pool)+qualifier+(' · Classement nominal\n' if signed else ' · Estimations expérimentales\n')+
                ('\n'.join(f'{i}. {x["rune"]} · {rates(x)}\n'
                             f'+{number(x["gain"])} · poids {number(x["weight"])} · {x["real_observations"]} essais réels'+
                             (f' · finition à {number(x["proposed"])} (over {number(x["natural_over"])})' if x.get('finishing_over') else '')
                           for i,x in enumerate(choices,1)) if choices else proposal.summary)+
                  ('\n'+pool_plan if pool_plan else '')+
                  ('\n'+price_text if price_text else '')+
                  ('\nSC/SN/EC non disponibles · pertes sur malus inconnues' if signed else ''))
    trace=(proposal.estimates or {}).get('decision_trace')
    audit=''
    if trace and trace.get('selected'):
        chosen=trace['candidates'][trace['selected']]
        weights=chosen['evidence']['weights']
        audit=(f"[DÉTAIL DU CLASSEMENT]\n{trace['selected']} : score initial {chosen['heuristic_score']:.4f}, "
               f"après sources {chosen['evidence_score']:.4f}, avant phase {chosen['economic_score']:.4f}. "
               f"Sources effectives de l'ajustement : {100*weights['real']:.0f} % réel / "
               f"{100*weights['simulation']:.0f} % simulation. "
               + ('Score remplacé par une séquence virtuelle. ' if chosen['sequence_used'] else 'Aucune séquence ne remplace ce score. ')
               + ('La combinaison de remontée couverte par le puits détermine la première rune ; les scores départagent les combinaisons de même poids et longueur. ' if data.get('pool_repair_preferred') else
                  'Le classement des sequences est conserve ; le puits reste descriptif. ' if data.get('sequence_preserved') else 'La phase de puits puis les estimations locales et le score determinent le classement heuristique. ')
               + 'Ces facteurs ne sont pas une probabilité de réussite en jeu.')
    return '\n\n'.join(part for part in (state,prediction,pool_plan,recommendation,audit) if part)+('\n'+price_text if price_text else '')


"""Versioned empirical video model, not the server's disclosed algorithm.

SC uses the final displayed formula. Q and SN require explicit reconstruction:
Q = mean filling ratio of all natural positive lines, clipped to [0,1];
SN uses the earlier piecewise shape applied to final SC's unfloored score.
These choices are hypotheses, exposed to callers, never hidden exact odds.
"""
from forgely_dofocus import reference, RUNE_CHOICES, WEIGHT_PER_POINT, normalise_jet

from forgely_fm_model import VERSION, PRIOR_STRENGTH, MIN_REAL, base_probabilities, calibrate_prediction
OUTCOMES = ('SC','SN','EC')


def estimate(jets, natural_max, rune, *, level=None, profile_complete=True):
    ref=reference(rune)
    stat=next((s for s,choices in RUNE_CHOICES.items() if rune in choices),None)
    if stat is None:return None
    return base_probabilities(jets,natural_max,stat,ref.gain,ref.weight,
                             level=level,profile_complete=profile_complete)


def calibrate(prediction, observation):
    return calibrate_prediction(prediction,observation)
