"""Reproducible held-out comparison of a first recommendation and its continuation.

No game input or real observations. Outputs complete-target results, not rune odds.
"""
import argparse,json
from pathlib import Path
from forgely_sequence import plan_sequences,options,validate_choice
from forgely_equipment_catalog import EquipmentCatalog,equipment_bounds
from forgely_dofocus import canonical_stat,WEIGHT_PER_POINT
from forgely_probabilites import wilson


def compare(lines,pool,targets,*,level=200,episodes=64,horizon=8,seed=20261107):
    # Planning and evaluation use separate random seed ranges.
    planned=plan_sequences(lines,pool,targets,level=level,seed=seed,trials=16,horizon=horizon)
    baseline=options(lines,pool,targets,level=level)[0][1]
    validation_runs=plan_sequences(lines,pool,targets,level=level,seed=seed+10**12,trials=32,horizon=horizon)
    validation=validate_choice(planned,validation_runs,baseline)
    selected=validation['selected'] if validation['accepted'] else baseline
    holdout=plan_sequences(lines,pool,targets,level=level,seed=seed+2*10**12,
                           trials=episodes,horizon=horizon)
    def metrics(rune):
        row=holdout[rune]
        return {'first_rune':rune,'sessions':episodes,'complete_targets':row['completed'],
                'complete_target_ci95':wilson(row['completed'],episodes),
                'mean_runes':row['mean_steps'],'mean_target_value':row['value']}
    return {'source':'simulation','real_observations':0,'horizon':horizon,
            'planning_seed':seed,'validation_seed':seed+10**12,'evaluation_seed':seed+2*10**12,'validation':validation,
            'baseline':metrics(baseline),'sequence':metrics(selected),
            'scope':'First choice fixed before evaluation; following choices adapt using the original heuristic.',
            'limitations':'Short simulated sessions; does not establish superiority in DOFUS.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--episodes',type=int,default=64)
    args=parser.parse_args()
    item=EquipmentCatalog().get(14092)
    bounds={canonical_stat(s):pair for s,pair in equipment_bounds(item).items()}
    cases=[]
    for force,intelligence,pool in ((36,39,5),(39,36,0),(38,38,10)):
        jet={s:hi for s,(lo,hi) in bounds.items()};jet.update(Force=force,Intelligence=intelligence)
        lines=[{'stat':s,'value':v,'min':bounds[s][0],'max':bounds[s][1],'weight':WEIGHT_PER_POINT[s]} for s,v in jet.items()]
        cases.append({'initial':{'Force':force,'Intelligence':intelligence,'pool':pool},
                      **compare(lines,pool,{'Force':40,'Intelligence':40},level=item.level,episodes=args.episodes)})
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({'item':item.name,'cases':cases},indent=2),encoding='utf8')
    for row in cases:
        print(row['initial'], 'baseline',row['baseline']['first_rune'],row['baseline']['complete_targets'],
              'sequence',row['sequence']['first_rune'],row['sequence']['complete_targets'])

if __name__=='__main__':main()
