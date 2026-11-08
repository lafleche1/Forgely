"""Local-only Forgely storage and observation utilities. No network calls."""
from pathlib import Path
import os, sqlite3
from datetime import datetime, timezone

DATA_DIR = Path(os.getenv('LOCALAPPDATA') or Path.home()) / 'Forgely'
DB_FILE = DATA_DIR / 'observations_locales.sqlite3'

RUNES = ('Vi', 'Pa Vi', 'Ra Vi', 'Fo', 'Pa Fo', 'Ra Fo', 'Ine', 'Pa Ine', 'Ra Ine',
         'Cha', 'Pa Cha', 'Ra Cha', 'Age', 'Pa Age', 'Ra Age', 'Sa', 'Pa Sa', 'Ra Sa',
         'Pui', 'Pa Pui', 'Ra Pui', 'Ini', 'Pa Ini', 'Ra Ini', 'Prospe', 'Pa Prospe',
         'Pod', 'Pa Pod', 'Ra Pod', 'Po', 'Do', 'Ga Pa', 'Ga Pme', 'Cri', 'Invo',
         'So', 'Tac', 'Pa Tac', 'Fui', 'Pa Fui', 'Ré Pa', 'Ré Pme', 'Ret Pa', 'Ret Pme')

# Screenshot-labelled rune icon catalogue (105 entries); the previous list is retained.
from pathlib import Path as _CataloguePath
import json as _catalogue_json
try:
    _bundled = _catalogue_json.loads((_CataloguePath(__file__).parent/'catalogue_dofus3'/'index.json').read_text(encoding='utf8'))
    RUNES = tuple(dict.fromkeys((*RUNES, *(row['rune'] for row in _bundled))))
except (OSError, ValueError, KeyError, TypeError):
    pass

def connect(db_file=DB_FILE):
    path = Path(db_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=15)
    conn.execute('''CREATE TABLE IF NOT EXISTS observations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        captured_at TEXT NOT NULL,
        item TEXT NOT NULL,
        rune TEXT NOT NULL,
        outcome TEXT NOT NULL CHECK (outcome IN ('SC','SN','EC')),
        source TEXT NOT NULL CHECK (source IN ('ocr_confirmed','manual','ocr_auto')),
        evidence TEXT NOT NULL DEFAULT '')''')
    # Migrate previous v0.6 source CHECK constraint without deleting observations.
    schema = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='observations'").fetchone()[0]
    if 'ocr_auto' not in schema:
        conn.execute('ALTER TABLE observations RENAME TO observations_old')
        conn.execute("""CREATE TABLE observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            captured_at TEXT NOT NULL,
            item TEXT NOT NULL,
            rune TEXT NOT NULL,
            outcome TEXT NOT NULL CHECK (outcome IN ('SC','SN','EC')),
            source TEXT NOT NULL CHECK (source IN ('ocr_confirmed','manual','ocr_auto')),
            evidence TEXT NOT NULL DEFAULT '')""")
        conn.execute('INSERT INTO observations SELECT * FROM observations_old')
        conn.execute('DROP TABLE observations_old')
    conn.commit()
    return conn

def insert_observation(item, rune, outcome, source, evidence='', db_file=DB_FILE):
    if not item.strip() or rune not in RUNES or outcome not in {'SC','SN','EC'} or source not in {'ocr_confirmed','manual','ocr_auto'}:
        raise ValueError('Équipement, rune ou résultat invalide')
    with connect(db_file) as db:
        cursor=db.execute('INSERT INTO observations(captured_at,item,rune,outcome,source,evidence) VALUES(?,?,?,?,?,?)',
                   (datetime.now(timezone.utc).isoformat(), item.strip(), rune, outcome, source, evidence[:350]))
        return cursor.lastrowid

def stats(item='', rune='', db_file=DB_FILE):
    with connect(db_file) as db:
        where=[]; params=[]
        if item.strip(): where.append('item=?');params.append(item.strip())
        if rune.strip(): where.append('rune=?');params.append(rune.strip())
        query='SELECT outcome, count(*) FROM observations'+(' WHERE '+' AND '.join(where) if where else '')+' GROUP BY outcome'
        rows=db.execute(query,params).fetchall()
    counts={'SC':0,'SN':0,'EC':0}
    counts.update(dict(rows))
    return sum(counts.values()),counts

def recent(limit=8, db_file=DB_FILE):
    with connect(db_file) as db:
        return db.execute('SELECT captured_at, item, rune, outcome, source FROM observations ORDER BY id DESC LIMIT ?', (limit,)).fetchall()


def insert_unassigned(outcome, evidence='', db_file=DB_FILE):
    """Uncertain event is kept locally OUTSIDE observation probability tables."""
    if outcome not in {'SC','SN','EC'}:
        raise ValueError('Résultat invalide')
    with connect(db_file) as db:
        db.execute('''CREATE TABLE IF NOT EXISTS unassigned_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            captured_at TEXT NOT NULL,
            outcome TEXT NOT NULL CHECK (outcome IN ('SC','SN','EC')),
            evidence TEXT NOT NULL DEFAULT '')''')
        db.execute('INSERT INTO unassigned_actions(captured_at,outcome,evidence) VALUES(?,?,?)',
                   (datetime.now(timezone.utc).isoformat(),outcome,evidence[:350]))


def unassigned_total(db_file=DB_FILE):
    with connect(db_file) as db:
        db.execute('''CREATE TABLE IF NOT EXISTS unassigned_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, captured_at TEXT NOT NULL,
            outcome TEXT NOT NULL, evidence TEXT NOT NULL DEFAULT '')''')
        count=db.execute('SELECT count(*) FROM unassigned_actions').fetchone()[0]
    return count

