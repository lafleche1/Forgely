"""Shared, explainable FM candidates. Rules are hypotheses, never server odds.

Independently implemented from documented FM principles, without loading any bot.
"""
from forgely_dofocus import RUNE_CHOICES, WEIGHT_PER_POINT, reference
from forgely_rules import constraints, finite_number

VERSION='fm-reasoning-1'
LIGHT=('Vitalité','Force','Intelligence','Chance','Agilité')


def explain_choice(rune,jets,targets,natural_max,pool):
    ref=reference(rune)
    stat=next((s for s,rs in RUNE_CHOICES.items() if rune in rs),None)
    if stat not in jets or stat not in targets or ref.gain is None:return ''
    current=jets[stat];goal=targets[stat];proposed=current+ref.gain
    covered=min(pool,ref.weight)
    text=(f'Raisonnement : {rune} ajoute {ref.gain:g} {stat}, poids {ref.weight:g}. '
          f'Jet {current:g}, cible {goal:g}, valeur projetée {proposed:g}. '
          f'Puits disponible {pool:g} ; couverture théorique de {covered:g} de poids sur un résultat non critique. ')
    maximum=(natural_max or {}).get(stat)
    if maximum is not None and proposed>goal and proposed<=maximum:
        text+='La cible est un minimum : ce dépassement reste dans le maximum naturel. '
    elif maximum is not None and proposed>max(maximum,goal):
        text+='Cette pose créerait un surplus préparatoire, dont l’intérêt reste à mesurer sur le jet complet. '
    text+='Aucun passage ni protection totale n’est garanti ; un SC conserve le puits.'
    return text


def strategic_options(jets,targets,natural_max,pool,*,max_over_weight=3.):
    """Expose direct and limited preparatory actions without crediting future losses."""
    if (not isinstance(jets,dict) or not isinstance(targets,dict) or not targets
            or not isinstance(natural_max,dict) or not natural_max
            or not finite_number(pool,nonnegative=True) or not set(targets)<=jets.keys()
            or not set(natural_max)<=jets.keys()
            or any(not finite_number(v) for v in (*jets.values(),*targets.values(),*natural_max.values()))
            or any(v<0 for v in (*jets.values(),*natural_max.values()))
            or not finite_number(max_over_weight,nonnegative=True)):
        return []
    if all(jets[s]>=target for s,target in targets.items()):return []
    rows=[]
    for stat,current in jets.items():
        direct=stat in targets and current<targets[stat]
        preparatory=(not direct and stat in LIGHT and natural_max.get(stat,0)>0
                     and targets.get(stat,current)<=natural_max[stat])
        if not direct and not preparatory:continue
        choices=RUNE_CHOICES.get(stat,())
        if preparatory:choices=choices[:1]
        for rune in choices:
            ref=reference(rune);proposed=current+ref.gain
            if direct:
                ceiling=max(targets[stat],natural_max.get(stat,0))
                if proposed>ceiling:continue
            elif max(0,proposed-natural_max[stat])*WEIGHT_PER_POINT[stat]>max_over_weight:
                continue
            checked=constraints({**jets,stat:proposed},natural_max)
            if checked['valid'] is not True:continue
            purpose=('temporary_surplus' if proposed>natural_max.get(stat,0) else 'support_line') if preparatory else 'reach_target'
            explanation=(explain_choice(rune,jets,{**targets,stat:targets.get(stat,current)},natural_max,pool))
            if preparatory:
                explanation+=' La perte éventuelle de ce surplus n’est pas du puits acquis ; seul le reliquat constaté après la tentative compte.'
            rows.append({'rune':rune,'stat':stat,'gain':ref.gain,'weight':ref.weight,
                         'purpose':purpose,'experimental':preparatory,'explanation':explanation,
                         'pool_gain_guaranteed':0,'is_game_probability':False})
    return rows
