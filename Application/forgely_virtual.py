"""Dynamic virtual sessions using the advisor's probabilities and rune ranking.

No observation writes. Missing loss distributions are censored by default;
optional uniform line loss is an explicit synthetic scenario, not server truth.
"""
from collections import Counter
from math import ceil
from random import Random
from statistics import mean
from forgely_decision import candidates, pool_transition
from forgely_dofocus import normalise_jet, reference, RUNE_CHOICES, WEIGHT_PER_POINT, natural_profile
from forgely_predictive import VERSION
from forgely_rules import finite_number, known_prices, constraints, objective_mode


def apply_outcome(jets, pool, rune, outcome, *, losses=None):
    jets=normalise_jet(jets)
    ref=reference(rune)
    stat=next((s for s,rs in RUNE_CHOICES.items() if rune in rs),None)
    if (not jets or stat not in jets or ref.weight is None or ref.gain is None
            or outcome not in ('SC','SN','EC') or not finite_number(pool,nonnegative=True)
            or any(s not in WEIGHT_PER_POINT or not finite_number(v,nonnegative=True) for s,v in jets.items())):
        raise ValueError('État, rune ou résultat non modélisé')
    if losses is None and outcome!='SC' and pool+1e-8<ref.weight:
        return None
    losses={} if losses is None else normalise_jet(losses)
    if losses is None or any(s not in jets or not finite_number(v,nonnegative=True) for s,v in losses.items()):
        raise ValueError('Pertes invalides')
    if outcome=='SC' and any(losses.values()):raise ValueError('SC incompatible avec des pertes')
    after=dict(jets)
    if outcome!='EC':after[stat]+=ref.gain
    if any(value>after[s]+1e-8 for s,value in losses.items()):raise ValueError('Perte supérieure au jet disponible')
    lost=sum(value*WEIGHT_PER_POINT[s] for s,value in losses.items())
    if outcome!='SC' and pool+lost+1e-8<ref.weight:
        # Fully depleted items can have no more density to lose.
        residual=sum(max(0.,after[s]-losses.get(s,0))*WEIGHT_PER_POINT[s] for s in after)
        if residual>1e-8:raise ValueError('Pertes insuffisantes pour ce reliquat')
    for s,value in losses.items():after[s]=round(max(0.,after[s]-value),6)
    return {'jet':after,'pool':pool_transition(pool,ref.weight,lost,outcome)}


def uniform_losses(jets,pool,rune,outcome,rng,*,natural_max=None,profile_complete=True):
    """Illustrative: choose positive lines uniformly; drop enough integer units."""
    ref=reference(rune)
    stat=next(s for s,rs in RUNE_CHOICES.items() if rune in rs)
    remaining=dict(jets)
    if outcome=='SN':remaining[stat]+=ref.gain
    # Explicit approximation: non-target over/exo lines before the pool.
    priority=[s for s,v in jets.items() if s!=stat and natural_max is not None
              and ((s in natural_max and v>natural_max[s])
                   or (profile_complete and s not in natural_max and v>0))]
    debt=ref.weight if priority else max(0.,ref.weight-pool)
    pool_pending=bool(priority)
    losses={}
    while debt>1e-8:
        preferred=[s for s in priority if remaining[s]>1e-8]
        if not preferred and pool_pending:
            debt=max(0.,debt-pool);pool_pending=False
            if debt<=1e-8:break
        eligible=preferred or [s for s,v in remaining.items() if v>1e-8]
        if not eligible:break
        selected=rng.choice(sorted(eligible))
        unit=WEIGHT_PER_POINT[selected]
        amount=min(remaining[selected],max(1,ceil((debt-1e-8)/unit)))
        remaining[selected]-=amount
        losses[selected]=losses.get(selected,0)+amount
        debt-=amount*unit
    return losses


def simulate_item(jets,targets,natural_max,pool,*,prices,level=None,profile_complete=True,
                  mode='Chances maximales',item=None,budget=None,trials=100,max_attempts=100,seed=19,
                  loss_mode='stop',losses_for=None,context_for=None,trace_limit=0,cancel=None):
    if not isinstance(prices,dict) or type(profile_complete) is not bool:
        raise ValueError('Prix : objet JSON ; profile_complete : booléen requis')
    jets,targets,bounds=normalise_jet(jets),normalise_jet(targets),normalise_jet(natural_max)
    documented=natural_profile(item) if item else None
    if documented is not None:bounds,profile_complete=documented,True
    if any(v<0 for mapping in (jets,targets,bounds) if mapping for v in mapping.values()):
        raise ValueError('Malus : transitions négatives non modélisées dans ce simulateur')
    if (not jets or not targets or bounds is None or not set(targets).issubset(jets)
            or not set(bounds).issubset(jets) or not finite_number(pool,nonnegative=True)
            or any(s not in WEIGHT_PER_POINT or not finite_number(v,nonnegative=True)
                   for mapping in (jets,targets,bounds) for s,v in mapping.items())
            or (level is not None and (type(level) is not int or not 1<=level<=200))
            or (budget is not None and not finite_number(budget,nonnegative=True))):
        raise ValueError('Jet, objectif, profil, niveau ou budget invalide/incomplet')
    if (type(trials) is not int or not 1<=trials<=50000 or type(max_attempts) is not int
            or not 1<=max_attempts<=10000 or trials*max_attempts>1_000_000
            or type(trace_limit) is not int or not 0<=trace_limit<=10000
            or type(seed) is not int or loss_mode not in ('stop','uniform')):
        raise ValueError('Limites invalides (au plus un million de clics virtuels par appel)')
    if constraints(jets,bounds,complete_profile=profile_complete)['valid'] is False:
        raise ValueError('Jet initial hors des gardes de Forgely')
    mode=objective_mode(mode)
    prices=known_prices(prices)
    rng=Random(seed)
    counts=Counter();stops=Counter();costs=[];attempts=0;completed=0;trace=[];loss_sources=Counter()
    for session in range(trials):
        state={'jet':dict(jets),'pool':float(pool)};spent=0.
        for attempt in range(max_attempts+1):
            if all(state['jet'][s]>=value for s,value in targets.items()):
                completed+=1;stops['goal']+=1;break
            if cancel is not None and cancel():
                stops['cancelled']+=1;break
            if attempt==max_attempts:stops['attempt_limit']+=1;break
            left=max(0.,budget-spent) if budget is not None else None
            if left==0:stops['budget']+=1;break
            callback=(lambda r:context_for(r,state['jet'],state['pool'])) if context_for else None
            options=candidates(state['jet'],targets,bounds,state['pool'],mode=mode,prices=prices,
                               remaining_budget=left,profile_complete=profile_complete,level=level,item=item,
                               context_for=callback)
            priced=[row for row in options if row[1] in prices and (left is None or prices[row[1]]<=left)]
            if not priced:stops['no_affordable_rune']+=1;break
            row=priced[0];rune=row[1];prediction=row[5].get('prediction')
            if prediction is None:stops['model_unavailable']+=1;break
            draw=rng.random()*100
            outcome='SC' if draw<prediction['SC'] else 'SN' if draw<prediction['SC']+prediction['SN'] else 'EC'
            before={'jet':dict(state['jet']),'pool':state['pool']}
            losses=None;origin='SC' if outcome=='SC' else 'pool'
            if outcome!='SC':
                if losses_for is not None:
                    losses=losses_for(before['jet'],before['pool'],rune,outcome,rng)
                    if losses is not None:origin='real_context'
                fragile=any((s in bounds and value>bounds[s])
                            or (profile_complete and s not in bounds and value>0)
                            for s,value in before['jet'].items())
                if losses is None and (fragile or before['pool']+1e-8<reference(rune).weight):
                    if loss_mode=='uniform':
                        losses=uniform_losses(before['jet'],before['pool'],rune,outcome,rng,
                                              natural_max=bounds,profile_complete=profile_complete);origin='uniform'
                    else:origin='unknown'
            after=None if origin=='unknown' else apply_outcome(before['jet'],before['pool'],rune,outcome,losses=losses)
            attempts+=1;counts[outcome]+=1;spent+=prices[rune];loss_sources[origin]+=1
            if len(trace)<trace_limit:
                trace.append({'session':session,'rune':rune,'prediction':prediction,'outcome':outcome,
                              'before':before,'after':after,'losses':losses,'loss_source':origin,'price':prices[rune]})
            if after is None:stops['unknown_loss']+=1;break
            state=after
        costs.append(spent)
        if cancel is not None and cancel():break
    n=len(costs)
    unknown=stops['unknown_loss']+stops['model_unavailable']+stops['cancelled']
    return {'source':'simulation_modele_dynamique','model_version':VERSION,'real_observations_written':0,
            'trials':n,'requested_trials':trials,'completed':completed,'attempts':attempts,
            'completion_bounds':[completed/n,(completed+unknown)/n] if n else [0.,1.],
            'unknown_transitions':stops['unknown_loss'],'mean_known_cost':mean(costs) if n else 0.,
            'counts':{k:counts[k] for k in ('SC','SN','EC')},'stops':dict(stops),
            'loss_sources':dict(loss_sources),'loss_mode':loss_mode,'trace':trace,
            'warnings':(['Profil naturel partiel : qualité approchée, exos non certifiés.'] if not profile_complete else [])+['Résultats virtuels, pas une mesure de réussite en jeu.',
                        'Les coûts et réussites sont limités aux sessions et transitions modélisées.']+
                       (['Pertes uniformes approximatives : hypothèse de scénario, pas loi du serveur.'] if loss_mode=='uniform' else
                        ['Pertes inconnues : sessions interrompues sans inventer une dégradation.'])}
