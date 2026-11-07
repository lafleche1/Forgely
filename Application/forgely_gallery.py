"""Local-only showcase queue. Not a public service, no upload or DOFUS automation."""
from __future__ import annotations
import json
import hashlib
import sqlite3
from pathlib import Path
from datetime import datetime,timezone
from forgely_data import DATA_DIR, DB_FILE,connect
from forgely_items import key_for


def verify_goal(plan, item, jets, pool, item_verified=False, stable=False, natural_bounds=None):
    """Only complete, stable, matched workshop readings qualify for a shareable success.

    Does not claim cryptographic authenticity; a player can modify local data.
    """
    if not item_verified or not stable or not isinstance(plan,dict) or not isinstance(jets,dict):
        return False,'Item ou jet non confirmé'
    if not item or key_for(item)!=key_for(plan.get('item','')):
        return False,'Objet différent du jet cible'
    goals=plan.get('stats')
    if not isinstance(goals,dict) or not goals:
        return False,'Aucun objectif défini'
    if pool is None or not isinstance(pool,(int,float)) or pool<0:
        return False,'Reliquat non confirmé'
    for stat,entry in goals.items():
        if not isinstance(entry,dict) or not isinstance(entry.get('target'),(int,float)):
            return False,'Objectif incomplet'
        if stat not in jets or not isinstance(jets[stat],(int,float)):
            return False,'Statistique non lue : '+stat
        if jets[stat] < entry['target']:
            return False,f'Objectif non atteint : {stat} ({jets[stat]} / {entry["target"]})'
    # Natural bounds are not required to prove the chosen target; they are
    # required elsewhere for classification FM/over/exo, not for a personal success.
    return True,'Toutes les caractéristiques sélectionnées sont atteintes'


def gallery_connect(db_file=DB_FILE):
    db=connect(db_file)
    db.execute('''CREATE TABLE IF NOT EXISTS success_gallery (
       id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
       item TEXT NOT NULL, target_json TEXT NOT NULL, actual_json TEXT NOT NULL,
       pool REAL NOT NULL, fingerprint TEXT NOT NULL UNIQUE,
       state TEXT NOT NULL DEFAULT 'local' CHECK(state='local'))''')
    db.commit()
    return db


def save_success(plan,item,jets,pool,verified=False,stable=False,db_file=DB_FILE):
    ok, reason=verify_goal(plan,item,jets,pool,verified,stable)
    if not ok:raise ValueError(reason)
    targets={k:float(v['target']) for k,v in plan['stats'].items()}
    values={k:float(jets[k]) for k in targets}
    serial=json.dumps({'item':key_for(item),'target':targets,'actual':values},sort_keys=True,ensure_ascii=False)
    fp=hashlib.sha256(serial.encode('utf8')).hexdigest()
    with gallery_connect(db_file) as db:
        db.execute('''INSERT OR IGNORE INTO success_gallery
            (created_at,item,target_json,actual_json,pool,fingerprint)
            VALUES (?,?,?,?,?,?)''',(datetime.now(timezone.utc).isoformat(),item,
            json.dumps(targets,ensure_ascii=False),json.dumps(values,ensure_ascii=False),float(pool),fp))
        row=db.execute('SELECT id FROM success_gallery WHERE fingerprint=?',(fp,)).fetchone()
    return row[0]


def list_successes(db_file=DB_FILE):
    with gallery_connect(db_file) as db:
        rows=db.execute('SELECT id,created_at,item,target_json,actual_json,pool FROM success_gallery ORDER BY id DESC').fetchall()
    return [{'id':r[0],'date':r[1],'item':r[2],'targets':json.loads(r[3]),
             'actual':json.loads(r[4]),'pool':r[5],'visibility':'locale'} for r in rows]


def export_gallery_json(path,db_file=DB_FILE):
    """Export only explicitly selected statistics; no character ID, screenshots or OCR."""
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    items=list_successes(db_file)
    document={'application':'Forgely','format':1,'status':'aperçu local à publier manuellement',
              'avertissement':'Données utilisateur non authentifiées, pas de vérification serveur',
              'reussites':items}
    path.write_text(json.dumps(document,ensure_ascii=False,indent=2),encoding='utf8')
    return len(items)
