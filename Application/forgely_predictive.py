"""Versioned empirical video model, not the server's disclosed algorithm.

SC uses the final displayed formula. Q and SN require explicit reconstruction:
Q = mean filling ratio of all natural positive lines, clipped to [0,1];
SN uses the earlier piecewise shape applied to final SC's unfloored score.
These choices are hypotheses, exposed to callers, never hidden exact odds.
"""
from forgely_dofocus import reference, RUNE_CHOICES, WEIGHT_PER_POINT, normalise_jet

VERSION = 'video-2026-11-08-v2'
OUTCOMES = ('SC','SN','EC')
PRIOR_STRENGTH = 200
MIN_REAL = 30


def estimate(jets, natural_max, rune, *, level=None, profile_complete=True):
    jets, bounds = normalise_jet(jets), normalise_jet(natural_max)
    ref = reference(rune)
    stat = next((s for s, choices in RUNE_CHOICES.items() if rune in choices), None)
    if (not jets or bounds is None or stat not in jets or ref.gain is None
            or ref.weight is None or not set(bounds).issubset(jets)
            or any(s not in WEIGHT_PER_POINT or v < 0 for s,v in bounds.items())
            or any(s not in WEIGHT_PER_POINT or v < 0 for s,v in jets.items())):
        return None
    assumptions = ['Q : moyenne des ratios de remplissage des lignes naturelles (définition utilisateur)',
                   'SN reconstruit : règle par morceaux du premier écran appliquée au score final']
    if not profile_complete:
        assumptions.append('profil partiel : qualité approchée et exos non certifiés')
    absent = stat not in bounds
    if absent:
        # No exotic claim from a partial catalogue, no generic 2% floor here.
        if not profile_complete or ref.weight <= 20:
            return None
        return {'SC':1.,'SN':0.,'EC':99.,'kind':'exo_lourd_reference_communautaire',
                'version':VERSION,'difficulty':None,'quality':None,'terms':{},
                'assumptions':['Exo lourd sur ligne absente : référence communautaire distincte de la formule vidéo'],
                'calibration_n':0,'real_weight':0.}
    maximum = bounds[stat]
    if maximum <= 0:
        return None
    ratios = [min(1.,max(0.,jets[s]/v)) for s,v in bounds.items() if v>0]
    quality = sum(ratios)/len(ratios) if ratios else 0.
    if profile_complete and any(s not in bounds and jets.get(s,0)>0 for s in ('PA','PM','Portée')):
        quality=1.
    current = jets[stat]
    over = current + ref.gain > maximum
    terms = {'base':5., 'threshold':45. if current>=.8*maximum else 0.,
             'over':65.+4.*max(0.,current+ref.gain-maximum)*WEIGHT_PER_POINT[stat] if over else 0.,
             'tier':12.*max(0.,current/ref.gain-14.),
             'level':0., 'quality':60.*quality**12}
    if level is None:
        assumptions.append('niveau inconnu : bonus sous 170 non appliqué')
    elif type(level) is not int or not 1<=level<=200:
        return None
    elif level<170:
        terms['level']=-20.*max(0.,1.1-quality)
    difficulty=sum(terms.values())
    x=(100.-difficulty)/2.
    sc=min(100.,max(2.,x))
    sn=(min(50.,100.-sc) if x>=0 else max(15.,50.-.75*abs(x))) - (10. if over else 0.)
    sn=max(0.,min(100.-sc,sn))
    return {'SC':sc,'SN':sn,'EC':100.-sc-sn,'kind':'video_estimation',
            'version':VERSION,'difficulty':difficulty,'quality':quality,'terms':terms,
            'assumptions':assumptions,'calibration_n':0,'real_weight':0.}


def calibrate(prediction, observation):
    """Dirichlet posterior mean, never raw aggregate rates or simulation counts."""
    if prediction is None or not observation or observation.get('verified') is not True:
        return prediction
    counts=observation.get('counts',{})
    if not isinstance(counts,dict):return prediction
    values=[counts.get(k,0) for k in OUTCOMES]
    if any(type(v) is not int or v<0 for v in values):return prediction
    n=sum(values)
    if n<MIN_REAL:return prediction
    result=dict(prediction)
    result.update({k:(PRIOR_STRENGTH*prediction[k]+100*counts.get(k,0))/(PRIOR_STRENGTH+n)
                   for k in OUTCOMES})
    result.update(calibration_n=n,real_weight=n/(PRIOR_STRENGTH+n),kind='video_calibre_reel')
    return result
