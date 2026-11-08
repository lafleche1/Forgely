"""Extract genuine inventory sprites from a user-installed DOFUS 3 (read-only).

Developer utility: requires UnityPy==1.23.0; not imported by the application.
Usage: python extract_equipment_assets.py PATH_TO_DOFUS_DATA
"""
import argparse
import json
import re
from pathlib import Path
from forgely_equipment_catalog import EquipmentCatalog,ROOT


def extract(data_dir,destination=ROOT/'assets'/'equipment_icons'):
    import UnityPy
    from PIL import Image
    data_dir=Path(data_dir)
    header=(data_dir/'globalgamemanagers').read_bytes()[:200]
    version=re.search(rb'\d{4}\.\d+\.\d+[abfp]\d+',header)
    if not version:raise ValueError('Version Unity introuvable')
    UnityPy.config.FALLBACK_UNITY_VERSION=version[0].decode()
    catalogue=EquipmentCatalog()
    required={str(item.icon_id) for item in catalogue.items}
    target=Path(destination);target.mkdir(parents=True,exist_ok=True)
    env=UnityPy.load(str(data_dir/'StreamingAssets/Content/Picto/Items/item_assets_1x.bundle'))
    found=set()
    for obj in env.objects:
        if obj.type.name!='Sprite':continue
        sprite=obj.read()
        if sprite.m_Name not in required:continue
        image=sprite.image.convert('RGBA')
        image.thumbnail((96,96),Image.Resampling.LANCZOS)
        image.save(target/(sprite.m_Name+'.png'))
        found.add(sprite.m_Name)
    manifest={'source':'DOFUS 3 installé, Content/Picto/Items/item_assets_1x.bundle',
        'unity_version':version[0].decode(),'equipment_count':len(catalogue.items),
        'icons':len(found),'missing':sorted(required-found,key=int)}
    (target/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    return manifest

# Characteristic identifiers and operators are read from installed game data.
# These labels match Forgely's supported rune characteristics; other effects
# (weapon damage, spell effects, conditions) are intentionally not converted.
CHARACTERISTICS={1:'PA',10:'Force',11:'Vitalité',12:'Sagesse',13:'Chance',14:'Agilité',
 15:'Intelligence',16:'Dommages',18:'Coups Critiques',19:'Portée',23:'PM',25:'Puissance',
 26:'Invocations',27:'Esquive PA',28:'Esquive PM',33:'% Résistance Terre',34:'% Résistance Feu',
 35:'% Résistance Eau',36:'% Résistance Air',37:'% Résistance Neutre',40:'Pods',44:'Initiative',
 48:'Prospection',49:'Soins',54:'Résistance Terre',55:'Résistance Feu',56:'Résistance Eau',
 57:'Résistance Air',58:'Résistance Neutre',69:'Puissance Pièges',70:'Dommages Pièges',
 78:'Fuite',79:'Tacle',82:'Retrait PA',83:'Retrait PM',84:'Dommages Poussée',
 85:'Résistance Poussée',86:'Dommages Critiques',87:'Résistance Critique',88:'Dommages Terre',
 89:'Dommages Feu',90:'Dommages Eau',91:'Dommages Air',92:'Dommages Neutre'}


def effect_bounds(effect,dice):
    stat=CHARACTERISTICS.get(effect.get('characteristic'))
    category=effect.get('category')
    if (not stat or not (category==0 or category==1 and stat.startswith('% Résistance '))
            or not effect.get('useDice') or effect.get('characteristicOperator') not in ('+','-')
            or type(dice.get('diceNum')) is not int or type(dice.get('diceSide',0)) is not int):
        return None
    lo=dice['diceNum'];hi=dice.get('diceSide') or lo
    if lo>hi:lo,hi=hi,lo
    if effect['characteristicOperator']=='-':lo,hi=-hi,-lo
    return stat,lo,hi


def extract_bounds(data_dir,destination=ROOT/'assets'/'equipment_bounds.csv'):
    import csv
    import UnityPy
    base=Path(data_dir)/'StreamingAssets/Content/Data'
    def read_root(name):
        env=UnityPy.load(str(base/f'data_assets_{name}dataroot.asset.bundle'))
        tree=next(o.read_typetree() for o in env.objects if o.type.name=='MonoBehaviour')
        return tree['references']['RefIds']
    effects={x['data']['id']:x['data'] for x in read_root('effects')}
    refs=read_root('items');by_rid={x['rid']:x['data'] for x in refs}
    catalogue=EquipmentCatalog();by_id={x.item_id:x for x in catalogue.items}
    rows=[]
    for ref in refs:
        item=ref['data'];entry=by_id.get(item.get('id'))
        if not entry or 'possibleEffects' not in item:continue
        stats={}
        for link in item['possibleEffects']:
            dice=by_rid.get(link['rid'],{})
            effect=effects.get(dice.get('actionId'),{})
            parsed=effect_bounds(effect,dice)
            if parsed is None:continue
            stat,lo,hi=parsed
            if stat in stats:
                stats[stat]=None # Ambiguous duplicate lines must not fabricate a range.
            else:stats[stat]=(lo,hi)
        for stat,bounds in stats.items():
            if bounds is not None:rows.append((entry.item_id,entry.name,stat,*bounds))
    target=Path(destination);target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.writer(stream);writer.writerow(['item_id','equipement','statistique','min','max']);writer.writerows(rows)
    return len(rows)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('data_dir')
    args=parser.parse_args()
    manifest=extract(args.data_dir)
    manifest['natural_effect_rows']=extract_bounds(args.data_dir)
    print(json.dumps(manifest,ensure_ascii=False))
