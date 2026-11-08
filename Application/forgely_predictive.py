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
    if pool>=51:return 'large'
    if pool>=20:return 'medium'
    if pool>0:return 'low'
    return 'zero'


def rank_options(options,jets,natural,pool,profile_complete=True):
    phase=pool_phase(pool);sat=saturation(jets,natural) if profile_complete else None
    rows=list(options);why=''
    original_order={row[1]:i for i,row in enumerate(rows)}
    if phase=='large':
        rows=[r for r in rows if (r[2] in ('PA','PM','Portée','Invocations','Dommages')
              or r[2].startswith('Dommages ') or r[2].startswith('% Résistance '))
              and natural is not None and r[2] in natural and r[8]<natural[r[2]]
              and r[4].weight<=pool]
        why='Très gros puits : priorité aux lignes lourdes naturelles à remonter ; petites runes écartées.'
    elif phase=='medium':
        middle=[r for r in rows if r[2] in INTERMEDIATE and r[4].weight<=pool]
        rows=middle or [r for r in rows if r[4].weight<=pool]
        why='Puits moyen : sécuriser les lignes intermédiaires, puis comparer gain / poids consommé.'
    elif phase=='low':
        rows=[r for r in rows if r[2] in LIGHT and r[4].weight<=max(1,min(3,pool))]
        why='Faible puits : grignotage des statistiques légères ; runes lourdes écartées.'
    elif phase=='zero':
        cleanup=[r for r in rows if r[1].startswith('Ra ')] if sat is not None and sat<.75 else []
        rows=cleanup or rows
        why=('Hors puits : nettoyage risqué par une Ra compatible avec la cible. Une perte de ligne lourde reste seulement possible.'
             if cleanup else 'Hors puits : risque de pertes sur les autres lignes ; aucune création de puits prévisible.')
    def key(row):
        band=success_band(row[2],row[8],row[4].gain,natural,sat,profile_complete)
        probability=sum(band)/2 if band else -1
        efficiency=row[4].gain/row[4].weight if phase=='medium' and row[4].weight else 0
        return (-probability,-efficiency,-row[0],original_order[row[1]])
    return sorted(rows,key=key),dict(phase=phase,saturation=sat,reason=why,profile_complete=profile_complete)


def option_payload(row,natural,sat,pool,profile_complete=True):
    _,rune,stat,kind,ref,_,_,_,current,goal=row
    p=Decimal(str(pool));weight=Decimal(str(ref.weight))
    return dict(rune=rune,stat=stat,kind=kind,gain=ref.gain,weight=ref.weight,
                success_band=success_band(stat,current,ref.gain,natural,sat,profile_complete),
                success_outcomes=('SC uniquement' if profile_complete and natural is not None and stat not in natural
                                  and stat in ('PA','PM','Portée') else 'SC ou SN'),
                probability_source='user_theoretical_estimate',pool_SC=number(p),
                pool_SN_EC_without_losses=number(max(Decimal(0),p-weight)),
                exposed_weight=number(max(Decimal(0),weight-p)),
                gain_per_weight=ref.gain/ref.weight if ref.weight else None)


def matrix_payload(rows,jets,natural,pool,meta):
    values=[option_payload(r,natural,meta['saturation'],pool,meta['profile_complete']) for r in rows]
    optimal=values[0] if values else None
    # Alternative remains inside the same phase and existing legality guards.
    alternative=max(values[1:],key=lambda x:(float(x['exposed_weight']),x['weight'])) if len(values)>1 else None
    return {**meta,'optimal':optimal,'alternative':alternative,'natural_max':natural,
            'probability_source':'user_theoretical_estimate'}


def report_text(proposal,jets,targets,natural,pool,*,pool_origin='lu',compact=False):
    data=(proposal.estimates or {}).get('matrix',{})
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
        band=option['success_band']
        rate=(f'~{band[0]} %' if band and band[0]==band[1] else f'~{band[0]}–{band[1]} %') if band else 'non chiffrable sans profil naturel'
        return (f'{title} : passez 1× Rune {option["rune"]}. Réussite théorique indicative : {rate} ({option["success_outcomes"]}). '
                f'Puits : SC {option["pool_SC"]} ; SN/EC sans perte {option["pool_SN_EC_without_losses"]}. '
                f'Poids non couvert : {option["exposed_weight"]}.')
    recommendation='[RECOMMANDATION IA]\n'+scenario(data.get('optimal'),'Option optimale (meilleure chance estimée)')
    recommendation+='\n'+scenario(data.get('alternative'),'Option risquée (alternative)')
    if compact:
        opt=data.get('optimal');alt=data.get('alternative')
        rate=opt.get('success_band') if opt else None
        phase={'large':'Très gros puits','medium':'Puits moyen','low':'Faible puits','zero':'Hors puits','unknown':'Puits inconnu'}
        return ('[ÉTAT MATRICIEL] Puits '+number(pool)+' ('+pool_origin+')\n'
                '[PRÉDICTION DU TOUR] '+phase.get(data.get('phase'),'Relecture du jet')+'\n'
                '[RECOMMANDATION IA] '+(opt['rune'] if opt else proposal.summary)+
                (f' · ~{rate[0]}–{rate[1]} % théoriques' if rate else '')+
                ('\nAlternative : '+alt['rune'] if alt else '')+
                ('\n'+price_text if price_text else ''))
    return '\n\n'.join((state,prediction,recommendation))+('\n'+price_text if price_text else '')
