"""Public DOFUS 3 equipment natural effect importer. Explicit user action only.

The catalogue is a reference, never an observed jet. No OCR values are fabricated.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from forgely_jet import SORTED_STATS, norm
from forgely_tools import import_bounds_csv, BOUNDS_PATH

ENDPOINT = 'https://api.dofusdu.de/dofus3/v1/fr/items/equipment'

def fetch_page(skip, limit=100, fetch=None):
    url=ENDPOINT+'?'+urlencode({'page[size]':limit,'page[number]':skip//limit+1,'fields[item]':'effects'})
    if fetch is None:
        req=Request(url,headers={'Accept':'application/json','User-Agent':'Forgely/20.70'})
        with urlopen(req,timeout=25) as r:
            raw=r.read(6_000_001)
    else: raw=fetch(url)
    if len(raw)>6_000_000:raise ValueError('Page trop volumineuse')
    result=json.loads(raw)
    if isinstance(result,list):return result
    if isinstance(result,dict):
        for key in ('items','results','data'):
            if isinstance(result.get(key),list):return result[key]
            if isinstance(result.get(key),dict):
                for nested in ('items','results','data'):
                    if isinstance(result[key].get(nested),list):return result[key][nested]
    raise ValueError('Format de réponse API inconnu')

def canonical_stat(label):
    text=norm(label).strip().replace('resistances','resistance')
    text=text.replace('points de ', '').replace('point de ', '').replace('bonus de ', '')
    aliases={'vitalite':'Vitalité','initiative':'Initiative','dommage feu':'Dommages Feu','dommage terre':'Dommages Terre','dommage air':'Dommages Air','dommage eau':'Dommages Eau','dommage neutre':'Dommages Neutre','% resistance eau':'% Résistance Eau','% resistance feu':'% Résistance Feu','% resistance terre':'% Résistance Terre','% resistance air':'% Résistance Air','% resistance neutre':'% Résistance Neutre'}
    if text in aliases:return aliases[text]
    for stat in SORTED_STATS:
        if norm(stat)==text:return stat
    return None

def parse_effect(effect):
    if not isinstance(effect,dict):return None
    # API names can vary between releases: fail closed on unknown structures.
    label=effect.get('type',{})
    if isinstance(label,dict):label=label.get('name') or label.get('fr')
    if isinstance(label,dict):label=label.get('fr') or label.get('name')
    if not isinstance(label,str):label=effect.get('name') or effect.get('effect')
    if isinstance(label,dict):label=label.get('fr') or label.get('name')
    if not isinstance(label,str):return None
    stat=canonical_stat(label)
    if not stat:return None
    low=next((effect[k] for k in ('int_minimum','min','minimum','min_value') if effect.get(k) is not None),None)
    high=next((effect[k] for k in ('int_maximum','max','maximum','max_value') if effect.get(k) is not None),None)
    # Some one-point effects provide only a minimum; never infer an absent max
    # unless the API explicitly marks the effect as fixed.
    if high is None and effect.get('is_fixed') is True:high=low
    if not isinstance(low,int) or isinstance(low,bool) or not isinstance(high,int) or isinstance(high,bool):return None
    if not (-30000<=low<=high<=30000):return None
    return stat,low,high

def extract_item(item):
    if not isinstance(item,dict) or not isinstance(item.get('name'),str):return []
    name=item['name'].strip()
    if not name or len(name)>180:return []
    effects=item.get('effects')
    if not isinstance(effects,list):return []
    found={}
    for effect in effects:
        parsed=parse_effect(effect)
        if parsed:
            stat,low,high=parsed
            if stat in found and found[stat]!=(low,high):found.pop(stat,None)
            elif stat not in found:found[stat]=(low,high)
    return [(name,stat,lo,hi) for stat,(lo,hi) in found.items()]

def download_references(destination=BOUNDS_PATH,fetch=None,max_pages=100):
    """Download into a temporary CSV; only replace user data after validated nonempty import.

    Returns (item_count,stat_count). No implicit online sync.
    """
    rows={}; seen=set(); total_items=0; received=0; unmapped=set()
    for page in range(max_pages):
        items=fetch_page(page*100,fetch=fetch)
        if not items:break
        received+=len(items)
        new=0
        for item in items:
            ident=item.get('ankama_id') if isinstance(item,dict) else None
            if ident is None:continue
            if ident in seen:continue
            seen.add(ident);new+=1
            parsed=extract_item(item)
            if parsed:total_items+=1
            for name,stat,lo,hi in parsed:rows[(name.casefold(),stat.casefold())]=(name,stat,lo,hi)
        if len(items)<100:break
        if new==0:raise ValueError('Pagination répétée par l’API')
    if not rows:
        raise ValueError(f'{received} équipements reçus mais aucun effet compatible reconnu. Vérifiez les champs effects et les noms de caractéristiques de l’API. Base existante conservée.')
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    staging=destination.with_name(destination.stem+'.import.csv')
    try:
        with staging.open('w',newline='',encoding='utf8') as f:
            w=csv.writer(f);w.writerow(['equipement','statistique','min','max']);w.writerows(rows.values())
        import_bounds_csv(staging,target=destination)
    finally:
        staging.unlink(missing_ok=True)
    return total_items,len(rows)
