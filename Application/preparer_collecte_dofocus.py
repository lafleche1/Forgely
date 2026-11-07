"""Offline collection worklist. Proposed inputs only, never simulated outcomes."""
from __future__ import annotations
from collections import Counter,defaultdict
from math import floor
from pathlib import Path
import argparse
import json
from forgely_dofocus import catalogue,validate_catalogue,canonical_stat,key,reference,FAMILIES
from forgely_dofocus_store import state_key


def collection_targets(data,limit=64):
    if type(limit) is not int or limit<0:raise ValueError('Limite entière positive ou nulle attendue')
    if limit==0:return []
    validate_catalogue(data)
    counts=Counter()
    existing=set()
    bases={}
    for sample in data['snapshots']:
        jet={canonical_stat(r['stat']):r['value'] for r in sample['rows']}
        for row in sample['rows']:
            stat=canonical_stat(row['stat']);counts[stat]+=len(row['runes'])
            for rune in row['runes']:existing.add((key(sample['item']),state_key(jet,sample['pool']),rune))
        bases.setdefault(key(sample['item']),sample)
    proposed={}
    def propose(sample,stat,rune,jet,pool,question):
        signature=(key(sample['item']),state_key(jet,pool),rune)
        if signature in existing or signature in proposed:return
        proposed[signature]={'kind':'collection_target','status':'not_collected',
            'item':sample['item'],'item_id':sample['item_id'],'url':sample['url'],
            'stat':stat,'rune':rune,'jets':jet,'pool':pool,'question':question,
            'recorded_family_cases':counts[stat]}
    for sample in bases.values():
        base={canonical_stat(r['stat']):r['value'] for r in sample['rows'] if r['max'] is not None}
        for row in sample['rows']:
            if row['max'] is None:continue
            stat=canonical_stat(row['stat'])
            for rune in row['runes']:
                ref=reference(rune)
                if ref.gain is None:continue
                for pool in (0,max(0,ref.weight-.5),ref.weight,ref.weight+.5):
                    propose(sample,stat,rune,dict(base),pool,'Comparer le reliquat au poids nominal de la rune')
                if row['max']>0:
                    for value,question in ((row['max']-ref.gain,'Comparer une restauration à proximité du maximum'),
                           (floor(.8*row['max']),'Explorer le palier affiché autour de 80 %'),
                           (20*ref.gain,'Comparer le comportement des petits paliers')):
                        jet={**base,stat:value}
                        propose(sample,stat,rune,jet,0,question)
                if row['value']<0:
                    for value in (-ref.gain,-1,0):
                        propose(sample,stat,rune,{**base,stat:value},ref.weight,
                                'Vérifier le coût du malus et le franchissement de zéro')
    # Simple known items expose gaps in rune families without fabricating new
    # equipment profiles. The extra line is an explicit simulator input (+Exo).
    for sample in bases.values():
        base={canonical_stat(r['stat']):r['value'] for r in sample['rows'] if r['max'] is not None}
        for stat,(rune,_,_,_) in FAMILIES.items():
            if stat not in base:
                propose(sample,stat,rune,{**base,stat:0},0,
                        'Relever une famille peu couverte via une ligne explicitement ajoutée dans le simulateur')
    # Diversity first: one candidate per family per round, least-covered first.
    groups=defaultdict(list)
    for target in proposed.values():groups[target['stat']].append(target)
    for values in groups.values():values.sort(key=lambda t:(len(t['jets']),key(t['item']),t['rune'],t['pool'],t['question']))
    ordered=sorted(groups,key=lambda stat:(counts[stat],key(stat)))
    result=[]
    while len(result)<limit and any(groups.values()):
        for stat in ordered:
            if groups[stat]:result.append(groups[stat].pop(0))
            if len(result)>=limit:break
    for number,target in enumerate(result,1):target['priority']=number
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit',type=int,default=64)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    targets=collection_targets(catalogue(),args.limit)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps({'kind':'collection_plan','real_attempts':0,
        'note':'Entrées proposées à vérifier dans Dofocus ; aucun résultat collecté par ce fichier.',
        'targets':targets},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'{len(targets)} situations à relever ; aucune probabilité générée.')


if __name__=='__main__':main()
