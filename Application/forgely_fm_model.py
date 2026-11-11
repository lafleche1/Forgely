"""Single provisional FM probability model; coefficients are not server rules."""
from math import exp
from forgely_dofocus import WEIGHT_PER_POINT, normalise_jet

VERSION='forgely-unified-fm-2026-11-08-v1'
MIN_REAL=30
PRIOR_STRENGTH=200


def base_probabilities(jets,natural_max,stat,gain,weight,*,level=None,profile_complete=True):
    jets,bounds=normalise_jet(jets),normalise_jet(natural_max)
    if (not jets or bounds is None or stat not in jets or gain is None or weight is None
            or not set(bounds)<=jets.keys()
            or any(s not in WEIGHT_PER_POINT or v<0 for s,v in (*bounds.items(),*jets.items()))):
        return None
    assumptions=['Modèle FM partagé provisoire, pas une formule serveur',
                 'Q : moyenne des ratios de remplissage des lignes naturelles',
                 'SN reconstruit par morceaux : hypothèse à calibrer']
    if not profile_complete:assumptions.append('profil partiel : qualité approchée et exos non certifiés')
    ratios=[min(1.,max(0.,jets[s]/maximum)) for s,maximum in bounds.items() if maximum>0]
    quality=sum(ratios)/len(ratios) if ratios else 0.
    if profile_complete and any(s not in bounds and jets.get(s,0)>0 for s in ('PA','PM','Portée')):quality=1.
    if level is not None and (type(level) is not int or not 1<=level<=200):return None
    if stat not in bounds:
        if not profile_complete:return None
        if weight>20:
            sc,sn,ec=1.,0.,99.
            kind='exo_lourd_reference_communautaire'
            assumptions.append('Exo lourd : référence communautaire 1 %, non officielle')
        else:
            # Retained low-density hypothesis, shared by every caller.
            density=(jets[stat]+gain)*weight/gain
            base=57 if density<=2 else 57-(density-2)*38/13 if density<=15 else 19-(density-15)*1.9 if density<25 else 0
            if level is not None and level<100 and density<=50:base=max(base,8-5*(density-25)/25)
            if base<=0:sc,sn,ec=1.,0.,99.
            else:
                adjusted=max(1,.077*base)+.923*base
                logistic=adjusted/(100-adjusted)*exp(1.2*(.85-quality))
                success=max(1,100*logistic/(1+logistic));sc=max(1,.077*success)
                sn=success-sc;ec=100-success
            kind='exo_leger_estimation'
            assumptions.append('Exo léger : courbe empirique héritée, non officielle')
        return dict(SC=sc,SN=sn,EC=ec,kind=kind,version=VERSION,difficulty=None,
                    quality=quality,terms={},assumptions=assumptions,calibration_n=0,real_weight=0.)
    maximum=bounds[stat]
    if maximum<=0:return None
    current=jets[stat];over=current+gain>maximum
    terms={'base':5.,'threshold':45. if current>=.8*maximum else 0.,
           'over':65.+4.*max(0.,current+gain-maximum)*WEIGHT_PER_POINT[stat] if over else 0.,
           'tier':12.*max(0.,current/gain-14.),'level':0.,'quality':60.*quality**12}
    if level is None:assumptions.append('niveau inconnu : bonus sous 170 non appliqué')
    elif level<170:terms['level']=-20.*max(0.,1.1-quality)
    difficulty=sum(terms.values());x=(100-difficulty)/2
    sc=min(100.,max(2.,x))
    sn=(min(50.,100-sc) if x>=0 else max(15.,50-.75*abs(x)))-(10. if over else 0.)
    sn=max(0.,min(100-sc,sn))
    return dict(SC=sc,SN=sn,EC=100-sc-sn,kind='fm_shared_estimation',version=VERSION,
                difficulty=difficulty,quality=quality,terms=terms,assumptions=assumptions,
                calibration_n=0,real_weight=0.)


def calibrate_prediction(prediction,observation):
    if prediction is None or not observation or observation.get('verified') is not True:return prediction
    counts=observation.get('counts',{})
    if not isinstance(counts,dict):return prediction
    values=[counts.get(k,0) for k in ('SC','SN','EC')]
    if any(type(v) is not int or v<0 for v in values):return prediction
    n=sum(values)
    if n<MIN_REAL:return prediction
    result=dict(prediction)
    result.update({k:(PRIOR_STRENGTH*prediction[k]+100*counts.get(k,0))/(PRIOR_STRENGTH+n) for k in ('SC','SN','EC')})
    result.update(calibration_n=n,real_weight=n/(PRIOR_STRENGTH+n),kind='fm_calibre_reel')
    return result


# Preserve the established classification API alongside the shared odds model.
from forgely_fm_classification import (LineState, classify, classify_item,
    extra_weight_total, check_budget, simulate_distribution, chance_independent_chain)
