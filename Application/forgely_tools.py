"""Forgely local workbench. No game automation, networking or fabricated probabilities.

Catalogue natural bounds are imported only from user-verified CSV. Simulations
are illustrative cost/risk scenarios and never write to observation tables.
"""
from __future__ import annotations
import csv
import json
import os
import sqlite3
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

from forgely_data import DB_FILE, DATA_DIR, RUNES, connect
from forgely_items import key_for

SETTINGS_PATH = DATA_DIR / 'atelier_preferences.json'
BOUNDS_PATH = DATA_DIR / 'jets_naturels_verifies.csv'
STRATEGIES = ('Prudent', 'Économique', 'Rapide', 'Jet parfait')

def settings_default():
    return {'strategy':'Prudent','budget_kamas':0,'prices':{}}

def read_settings(path=SETTINGS_PATH):
    try:
        raw=json.loads(Path(path).read_text(encoding='utf8'))
        if not isinstance(raw,dict):raise ValueError('structure invalide')
    except (OSError,ValueError,TypeError):raw={}
    cfg=settings_default()
    cfg.update({k:raw[k] for k in ('strategy','budget_kamas','prices') if k in raw})
    if cfg['strategy'] not in STRATEGIES:cfg['strategy']='Prudent'
    if not isinstance(cfg['prices'],dict):cfg['prices']={}
    cfg['prices']={str(k):int(v) for k,v in cfg['prices'].items() if str(v).isdigit() and int(v)>=0}
    try: cfg['budget_kamas']=max(0,int(cfg['budget_kamas']))
    except (ValueError,TypeError):cfg['budget_kamas']=0
    return cfg

def save_settings(settings,path=SETTINGS_PATH):
    if settings.get('strategy') not in STRATEGIES:raise ValueError('Stratégie inconnue')
    if not isinstance(settings.get('budget_kamas'),int) or settings['budget_kamas']<0:raise ValueError('Budget invalide')
    prices=settings.get('prices')
    if not isinstance(prices,dict) or any(k not in RUNES or not isinstance(v,int) or v<0 for k,v in prices.items()):
        raise ValueError('Prix de runes invalides')
    target=Path(path);target.parent.mkdir(parents=True,exist_ok=True)
    tmp=target.with_suffix('.tmp')
    tmp.write_text(json.dumps(settings,ensure_ascii=False,indent=2),encoding='utf8')
    tmp.replace(target)

def import_bounds_csv(source,target=BOUNDS_PATH):
    """Only explicit user-supplied natural min/max; never guess item identity."""
    entries={}
    with open(source,newline='',encoding='utf-8-sig') as f:
        reader=csv.DictReader(f)
        required={'equipement','statistique','min','max'}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):raise ValueError('En-têtes requis : equipement,statistique,min,max')
        for record in reader:
            item=(record['equipement'] or '').strip()
            stat=(record['statistique'] or '').strip()
            if not key_for(item) or not stat:raise ValueError('Objet ou statistique manquant')
            low=int(record['min']);high=int(record['max'])
            if low < -30000 or high < low or high > 30000:raise ValueError('Bornes naturelles invalides')
            key=(key_for(item),stat.casefold())
            if key in entries:raise ValueError('Doublon dans les jets naturels')
            entries[key]=(item,stat,low,high)
    if not entries:raise ValueError('Fichier vide')
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    with open(target.with_suffix('.tmp'),'w',newline='',encoding='utf8') as f:
        writer=csv.writer(f);writer.writerow(['equipement','statistique','min','max'])
        writer.writerows(entries.values())
    target.with_suffix('.tmp').replace(target)
    return len(entries)

def natural_bounds(item,path=BOUNDS_PATH):
    result={}
    try:
        with open(path,newline='',encoding='utf8') as f:
            for row in csv.DictReader(f):
                if key_for(row['equipement'])==key_for(item):result[row['statistique']]=(int(row['min']),int(row['max']))
    except (OSError,ValueError,KeyError):return {}
    return result

def export_observations_csv(target,db_file=DB_FILE,only_item=None):
    """CSV export of real observations, not simulated scenarios."""
    with connect(db_file) as db:
        if only_item:
            rows=db.execute('SELECT captured_at,item,rune,outcome,source FROM observations WHERE item=? ORDER BY id',(only_item,)).fetchall()
        else:
            rows=db.execute('SELECT captured_at,item,rune,outcome,source FROM observations ORDER BY id').fetchall()
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['date_utc','equipement','rune','resultat','source']);writer.writerows(rows)
    return len(rows)

def export_item_summary(target,db_file=DB_FILE):
    with connect(db_file) as db:
        rows=db.execute('''SELECT item,rune,COUNT(*),SUM(outcome='SC'),SUM(outcome='SN'),SUM(outcome='EC')
                           FROM observations GROUP BY item,rune ORDER BY item,rune''').fetchall()
    with open(target,'w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['equipement','rune','essais','SC','SN','EC']);writer.writerows(rows)
    return len(rows)

def backup_local(target,db_file=DB_FILE,settings_path=SETTINGS_PATH,bounds_path=BOUNDS_PATH):
    """Consistent sqlite snapshot and configuration files. Never sends anywhere."""
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        snapshot=Path(d)/'observations_locales.sqlite3'
        with connect(db_file) as source, sqlite3.connect(str(snapshot)) as dest:
            source.backup(dest)
        with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as z:
            z.write(snapshot,'observations_locales.sqlite3')
            for p in (settings_path,bounds_path):
                p=Path(p)
                if p.exists():z.write(p,p.name)
            z.writestr('MANIFESTE.txt','Sauvegarde locale Forgely. Ne pas importer une base SQLite inconnue sans validation.\n')
    return target

def session_cost(item,settings=None,db_file=DB_FILE):
    """Approximate only: counts observed attempts, cannot know inventory or refund."""
    cfg=settings if settings is not None else read_settings()
    with connect(db_file) as db:
        rows=db.execute('SELECT rune,COUNT(*) FROM observations WHERE item=? GROUP BY rune',(item,)).fetchall()
    known_cost=sum(n*cfg['prices'][r] for r,n in rows if r in cfg['prices'])
    unknown=sum(n for r,n in rows if r not in cfg['prices'])
    return {'known_cost':known_cost,'unpriced_attempts':unknown,'total_attempts':sum(n for _,n in rows)}

def observed_distribution(item,rune,db_file=DB_FILE,min_samples=30):
    from forgely_data import stats
    n,counts=stats(item=item,rune=rune,db_file=db_file)
    if n<min_samples:return {'n':n,'counts':counts,'usable':False,'rates':None}
    return {'n':n,'counts':counts,'usable':True,'rates':{k:v/n for k,v in counts.items()}}

def illustrative_scenario(rune,attempts,price,sc,sn,ec,seed=11):
    """Hypothetical scenario: user-provided assumed probabilities, NOT fitted to DOFUS.

    Output intentionally not stored in observed data. Does not simulate item degradation.
    """
    import random
    if rune not in RUNES:raise ValueError('Rune inconnue')
    if not isinstance(attempts,int) or not 1<=attempts<=100000:raise ValueError('Essais invalides')
    if price<0 or min(sc,sn,ec)<0 or abs(sc+sn+ec-1)>1e-8:raise ValueError('Probabilités invalides')
    rng=random.Random(seed)
    counts={'SC':0,'SN':0,'EC':0}
    for _ in range(attempts):
        x=rng.random();counts['SC' if x<sc else 'SN' if x<sc+sn else 'EC']+=1
    return {'rune':rune,'scenarios':attempts,'counts':counts,'assumptions':{'SC':sc,'SN':sn,'EC':ec},'cost_kamas':attempts*price,'is_real_observation':False}

def advisory_status(plan,jets,pool,verified,item_bounds=None,stats_count=0):
    """Explicit safety gate for probability of final target and stop advice."""
    if not verified or not plan or not jets or pool is None:
        return {'stop':'Attendre : jet complet et reliquat non confirmés','goal_probability':None}
    bounds=item_bounds or {}
    if not bounds:return {'stop':'Jets naturels inconnus : conseil d’arrêt non fiable','goal_probability':None}
    wanted=plan.get('stats',{})
    if not wanted:return {'stop':'Définir un objectif','goal_probability':None}
    if any(k not in jets or k not in bounds for k in wanted):
        return {'stop':'Mesures ou jets naturels incomplets','goal_probability':None}
    complete=all(jets[k]>=v['target'] for k,v in wanted.items())
    if complete:return {'stop':'Objectif affiché atteint : envisager d’arrêter','goal_probability':1.0}
    return {'stop':'Objectif en cours : comparer les risques avant de continuer','goal_probability':None}
