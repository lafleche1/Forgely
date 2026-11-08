"""Forgely local workbench. No game automation, networking or fabricated probabilities.

Catalogue natural bounds are imported only from user-verified CSV. Simulations
are illustrative outcome scenarios and never write to observation tables.
"""
from __future__ import annotations
from forgely_sqlite import database_connection, transaction as closing_transaction
import csv
import json
import os
import sqlite3
import shutil
import zipfile
from collections import Counter
from functools import lru_cache
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

from forgely_data import DB_FILE, DATA_DIR, RUNES, connect
from forgely_items import key_for
from forgely_rules import MODES, objective_mode, finite_number

SETTINGS_PATH = DATA_DIR / 'atelier_preferences.json'
BOUNDS_PATH = DATA_DIR / 'jets_naturels_verifies.csv'
STRATEGIES = MODES + ('Budget optimisé', 'Prudent', 'Économique', 'Rapide', 'Jet parfait')

PRICE_METADATA = ('price_reference', 'price_server', 'price_reference_date', 'price_source')


def activate_tylezia_reference(path=SETTINGS_PATH):
    """Install the user's dated HDV reference once, without touching observations.

    A reference is explicitly server-specific. Keep an exact backup of the old
    preferences before replacing their price grid; never merge unidentified
    server prices into Tylezia or overwrite subsequent manual edits.
    """
    path = Path(path)
    cfg = read_settings(path)
    reference_id = 'tylezia-2026-11-08'
    if cfg.get('price_reference') == reference_id:
        return cfg
    source = Path(__file__).parent / 'prices' / (reference_id + '.json')
    reference = json.loads(source.read_text(encoding='utf8'))
    prices = reference['prices']
    if (reference['server'] != 'Tylezia' or reference['reference_id'] != reference_id
            or len(prices) != 105 or set(prices) != set(RUNES)
            or any(type(v) is not int or v < 0 for v in prices.values())):
        raise ValueError('Référence de prix Tylezia invalide')
    if path.exists():
        backup = path.with_suffix('.avant-tylezia-2026-11-08.json')
        if not backup.exists():
            shutil.copy2(path, backup)
    cfg.update(strategy='Budget optimisé', prices=dict(prices),
               price_reference=reference_id, price_server=reference['server'],
               price_reference_date=reference['recorded_on'], price_source=reference['source'])
    save_settings(cfg, path)
    return cfg


def price_reference_label(settings):
    if settings.get('price_server'):
        return (f"{settings['price_server']} · prix moyens unitaires · relevé reçu le "
                f"{settings.get('price_reference_date', 'date inconnue')}\n"
                'Références modifiables, sans actualisation automatique ; prix d’achat non garanti.')
    return 'Prix unitaires saisis manuellement ; serveur non renseigné.'

def settings_default():
    return {'strategy':'Chances maximales','budget_kamas':0,'prices':{}}

@lru_cache(maxsize=16)
def _settings_json(path, signature):
    # The signature includes replacement identity and nanosecond modification times.
    # Never expose this cached dict to callers; read_settings creates fresh values.
    return json.loads(path.read_text(encoding='utf8'))


def read_settings(path=SETTINGS_PATH):
    try:
        path = Path(path).absolute()
        info = path.stat()
        signature = (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
        raw = _settings_json(path, signature)
        if not isinstance(raw,dict):raise ValueError('structure invalide')
    except (OSError,ValueError,TypeError):raw={}
    cfg=settings_default()
    cfg.update({k:raw[k] for k in ('strategy','budget_kamas','prices',*PRICE_METADATA) if k in raw})
    if type(raw.get('stop_at_budget')) is bool:cfg['stop_at_budget']=raw['stop_at_budget']
    if cfg['strategy'] not in STRATEGIES:cfg['strategy']='Chances maximales'
    cfg['strategy']=objective_mode(cfg['strategy'])
    if not isinstance(cfg['prices'],dict):cfg['prices']={}
    cfg['prices']={str(k):int(v) for k,v in cfg['prices'].items() if str(v).isdigit() and int(v)>=0}
    try: cfg['budget_kamas']=max(0,int(cfg['budget_kamas']))
    except (ValueError,TypeError):cfg['budget_kamas']=0
    return cfg

def save_settings(settings,path=SETTINGS_PATH):
    merged=read_settings(path)
    merged.update(settings)
    settings=merged
    if 'stop_at_budget' in settings and type(settings['stop_at_budget']) is not bool:raise ValueError('Option de budget invalide')
    if settings.get('strategy') not in STRATEGIES:raise ValueError('Stratégie inconnue')
    if not isinstance(settings.get('budget_kamas'),int) or settings['budget_kamas']<0:raise ValueError('Budget invalide')
    prices=settings.get('prices')
    if not isinstance(prices,dict) or any(k not in RUNES or not isinstance(v,int) or v<0 for k,v in prices.items()):
        raise ValueError('Prix de runes invalides')
    settings['strategy']=objective_mode(settings['strategy'])
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

@lru_cache(maxsize=4)
def _bounds_index(path,revision):
    result={};invalid=set()
    with open(path,newline='',encoding='utf8') as f:
        for row in csv.DictReader(f):
            name=key_for(row['equipement'])
            try:
                result.setdefault(name,{})[row['statistique']]=(int(row['min']),int(row['max']))
            except (ValueError,KeyError):invalid.add(name)
    for name in invalid:result.pop(name,None)
    return result


def natural_bounds(item,path=BOUNDS_PATH):
    result={}
    if Path(path)==Path(BOUNDS_PATH):
        from forgely_equipment_catalog import bundled_bounds
        result=bundled_bounds(item)
    from forgely_runtime_cache import file_revision
    path=Path(path).absolute()
    try:result.update(_bounds_index(path,file_revision(path)).get(key_for(item),{}))
    except (OSError,ValueError,KeyError):pass
    return result


def export_observations_csv(target,db_file=DB_FILE,only_item=None):
    """CSV export of real observations, not simulated scenarios."""
    with closing_transaction(connect(db_file)) as db:
        if only_item:
            rows=db.execute('SELECT captured_at,item,rune,outcome,source FROM observations WHERE item=? ORDER BY id',(only_item,)).fetchall()
        else:
            rows=db.execute('SELECT captured_at,item,rune,outcome,source FROM observations ORDER BY id').fetchall()
    target=Path(target);target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['date_utc','equipement','rune','resultat','source']);writer.writerows(rows)
    return len(rows)

def export_item_summary(target,db_file=DB_FILE):
    with closing_transaction(connect(db_file)) as db:
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
        with closing_transaction(connect(db_file)) as source, database_connection(str(snapshot)) as dest:
            source.backup(dest)
        with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as z:
            z.write(snapshot,'observations_locales.sqlite3')
            for p in (settings_path,bounds_path):
                p=Path(p)
                if p.exists():z.write(p,p.name)
            z.writestr('MANIFESTE.txt','Sauvegarde locale Forgely. Ne pas importer une base SQLite inconnue sans validation.\n')
    return target

def observation_cursor(db_file=DB_FILE):
    """Consistent launch boundary for assigned AND unassigned attempts."""
    with closing_transaction(connect(db_file)) as db:
        db.execute('''CREATE TABLE IF NOT EXISTS unassigned_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, captured_at TEXT NOT NULL,
            outcome TEXT NOT NULL, evidence TEXT NOT NULL DEFAULT '')''')
        db.commit()
        db.execute('BEGIN')
        return {table:db.execute(f'SELECT COALESCE(MAX(id),0) FROM {table}').fetchone()[0]
                for table in ('observations','unassigned_actions')}


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
    if min(sc,sn,ec)<0 or abs(sc+sn+ec-1)>1e-8:raise ValueError('Probabilités invalides')
    rng=random.Random(seed)
    counts={'SC':0,'SN':0,'EC':0}
    for _ in range(attempts):
        x=rng.random();counts['SC' if x<sc else 'SN' if x<sc+sn else 'EC']+=1
    return {'rune':rune,'scenarios':attempts,'counts':counts,'assumptions':{'SC':sc,'SN':sn,'EC':ec},'is_real_observation':False}

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


def session_cost(item,settings=None,db_file=DB_FILE):
    """Approximate only: counts observed attempts, cannot know inventory or refund."""
    cfg=settings if settings is not None else read_settings()
    with connect(db_file) as db:
        rows=db.execute('SELECT rune,COUNT(*) FROM observations WHERE item=? GROUP BY rune',(item,)).fetchall()
    known_cost=sum(n*cfg['prices'][r] for r,n in rows if r in cfg['prices'])
    unknown=sum(n for r,n in rows if r not in cfg['prices'])
    return {'known_cost':known_cost,'unpriced_attempts':unknown,'total_attempts':sum(n for _,n in rows)}


def cost_since(cursor, prices, db_file=DB_FILE):
    """Recorded rune consumption since launch, not inventory or guaranteed coverage.

    All items in this application session share the budget. OCR events remain
    estimates of consumption. Repricing intentionally revalues the whole session.
    """
    # Legacy integer cursors conservatively include all unknown-rune attempts.
    boundary={'observations':cursor,'unassigned_actions':0} if isinstance(cursor,int) else cursor
    if (not isinstance(boundary,dict) or set(boundary)!= {'observations','unassigned_actions'}
            or any(not isinstance(v,int) or isinstance(v,bool) or v<0 for v in boundary.values())):
        raise ValueError('Début de session invalide')
    with connect(db_file) as db:
        db.execute('BEGIN')
        rows=db.execute('SELECT rune,COUNT(*) FROM observations WHERE id>? GROUP BY rune', (boundary['observations'],)).fetchall()
        exists=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='unassigned_actions'").fetchone()
        unassigned=db.execute('SELECT COUNT(*) FROM unassigned_actions WHERE id>?',
                              (boundary['unassigned_actions'],)).fetchone()[0] if exists else 0
    known=0.; unknown=unassigned
    for rune,n in rows:
        price=prices.get(rune)
        if not finite_number(price,nonnegative=True):
            unknown+=n
        else:
            known+=n*price
    return {'known_cost':known,'unpriced_attempts':unknown,
            'total_attempts':sum(n for _,n in rows)+unassigned,
            'unassigned_attempts':unassigned,'complete':unknown==0}
