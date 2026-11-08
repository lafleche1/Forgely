"""Local, auditable pre/post-fusion contexts; never blend simulation with observations.

Context-linked observations require a stable pre-fusion reading, recognised item,
recognised rune/result, and a different stable post-fusion reading. Partial OCR
samples are stored as diagnostics, NOT proof of a full item jet.
"""
from __future__ import annotations
from forgely_sqlite import database_connection
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from forgely_data import DB_FILE
from forgely_probabilites import wilson
from forgely_rules import finite_number


def normalize_snapshot(jet, pool):
    if not isinstance(jet, dict) or not jet or not finite_number(pool, nonnegative=True):
        return None
    clean = {}
    for name, amount in jet.items():
        if not isinstance(name,str) or not name or not finite_number(amount) or not -30000 <= amount <= 30000:
            return None
        clean[name] = amount
    return {'jet': dict(sorted(clean.items())), 'pool': float(pool)}


def snapshot_diff(before, after):
    if not before or not after: return None
    # Both snapshots must contain *exactly* the same measured statistics;
    # an OCR omission does not mean the stat fell to zero.
    if set(before['jet']) != set(after['jet']): return None
    changes={k:after['jet'][k]-v for k,v in before['jet'].items() if after['jet'][k]!=v}
    return {'changes':changes,'pool_delta':round(after['pool']-before['pool'],4)}


def init_context_db(db_file=DB_FILE):
    path=Path(db_file);path.parent.mkdir(parents=True,exist_ok=True)
    with database_connection(str(path)) as db:
        db.execute('''CREATE TABLE IF NOT EXISTS fusion_contexts (
            id INTEGER PRIMARY KEY,
            observed_at TEXT NOT NULL,
            item TEXT NOT NULL,
            rune TEXT NOT NULL,
            outcome TEXT NOT NULL CHECK(outcome IN ('SC','SN','EC')),
            before_json TEXT NOT NULL,
            after_json TEXT NOT NULL,
            deltas_json TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'local_screen',
            CHECK(source='local_screen')
        )''')
        db.execute('CREATE INDEX IF NOT EXISTS ctx_item_rune ON fusion_contexts(item,rune)')


def save_transition(item,rune,outcome,before,after,db_file=DB_FILE, *, event_confirmed=False):
    if not item or not rune or outcome not in ('SC','SN','EC'):
        raise ValueError('Item, rune et résultat requis')
    start=normalize_snapshot(before.get('jet'),before.get('pool')) if before else None
    end=normalize_snapshot(after.get('jet'),after.get('pool')) if after else None
    delta=snapshot_diff(start,end)
    if delta is None or (not delta['changes'] and delta['pool_delta']==0
                         and not (event_confirmed is True and outcome == 'EC')):
        raise ValueError('Deux snapshots cohérents et différents sont nécessaires')
    init_context_db(db_file)
    with database_connection(str(db_file)) as db:
        db.execute('INSERT INTO fusion_contexts(observed_at,item,rune,outcome,before_json,after_json,deltas_json) VALUES(?,?,?,?,?,?,?)',
            (datetime.now(timezone.utc).isoformat(),item,rune,outcome,json.dumps(start,ensure_ascii=False),json.dumps(end,ensure_ascii=False),json.dumps(delta,ensure_ascii=False)))
    return delta


def context_rates(item,rune,stat=None,pre_value=None,pre_pool=None,db_file=DB_FILE):
    """Condition on approximate *observed* pre-jet and pool; return no forecast if n<30."""
    init_context_db(db_file)
    with database_connection(str(db_file)) as db:
        rows=db.execute('SELECT outcome,before_json FROM fusion_contexts WHERE item=? AND rune=?',(item,rune)).fetchall()
    counts={'SC':0,'SN':0,'EC':0}
    for outcome,raw in rows:
        before=json.loads(raw)
        if stat is not None:
            if stat not in before['jet'] or pre_value is None or abs(before['jet'][stat]-pre_value)>max(1,abs(pre_value)*.1):
                continue
        if pre_pool is not None and abs(before['pool']-pre_pool)>max(2,pre_pool*.2):
            continue
        counts[outcome]+=1
    n=sum(counts.values())
    if n<30:
        return {'n':n,'counts':counts,'usable':False,'percentages':None,'ci95_sc':None}
    pct={k:round(100*v/n,1) for k,v in counts.items()}
    ci=tuple(round(100*x,1) for x in wilson(counts['SC'],n))
    return {'n':n,'counts':counts,'usable':True,'percentages':pct,'ci95_sc':ci}
