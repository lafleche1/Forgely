"""Unclassified, icon-anchored attempts, separate from SC/SN/EC learning."""
from datetime import datetime, timezone
from pathlib import Path
from forgely_data import DB_FILE
from forgely_sqlite import database_connection


def _init(db):
    db.execute('''CREATE TABLE IF NOT EXISTS observed_attempt_activity (
        id INTEGER PRIMARY KEY, event_key TEXT NOT NULL UNIQUE,
        captured_at TEXT NOT NULL, item TEXT NOT NULL DEFAULT '',
        evidence TEXT NOT NULL DEFAULT '',
        result_status TEXT NOT NULL DEFAULT 'undetermined'
          CHECK(result_status='undetermined'))''')


def record_activity(event_key, item='', evidence='', *, db_file=DB_FILE):
    if not isinstance(event_key,str) or not event_key or len(event_key)>250:
        raise ValueError('Identifiant de tentative invalide')
    Path(db_file).parent.mkdir(parents=True,exist_ok=True)
    with database_connection(str(db_file)) as db:
        _init(db)
        cursor=db.execute('INSERT OR IGNORE INTO observed_attempt_activity '
            '(event_key,captured_at,item,evidence) VALUES(?,?,?,?)',
            (event_key,datetime.now(timezone.utc).isoformat(),(item or '').strip(),str(evidence)[:1000]))
        return cursor.lastrowid if cursor.rowcount==1 else None


def activity_total(item='', *, include_unattributed=False, db_file=DB_FILE):
    Path(db_file).parent.mkdir(parents=True,exist_ok=True)
    with database_connection(str(db_file)) as db:
        _init(db)
        if item.strip():
            where="item=? OR item=''" if include_unattributed else 'item=?'
            return db.execute('SELECT count(*) FROM observed_attempt_activity WHERE '+where,
                              (item.strip(),)).fetchone()[0]
        return db.execute('SELECT count(*) FROM observed_attempt_activity').fetchone()[0]


def activity_recent(limit=100, *, db_file=DB_FILE):
    Path(db_file).parent.mkdir(parents=True,exist_ok=True)
    with database_connection(str(db_file)) as db:
        _init(db)
        return db.execute('SELECT captured_at,item FROM observed_attempt_activity ORDER BY id DESC LIMIT ?',
                          (max(0,min(1000,int(limit))),)).fetchall()
