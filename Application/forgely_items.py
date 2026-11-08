"""Local item registry; conservative deduplication and per-item observation tables."""
from __future__ import annotations
from forgely_sqlite import database_connection, transaction as closing_transaction
import re, sqlite3, unicodedata
from PIL import Image
from pathlib import Path
from forgely_data import DB_FILE


def key_for(name):
    text = ''.join(c for c in unicodedata.normalize('NFKD', name or '') if not unicodedata.combining(c))
    text = re.sub(r'[^a-z0-9]+', ' ', text.casefold()).strip()
    return re.sub(r'\s+', ' ', text)


def _init(db):
    db.execute('''CREATE TABLE IF NOT EXISTS equipment (
        id INTEGER PRIMARY KEY, name TEXT NOT NULL, identity_key TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, last_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)''')
    db.execute('''CREATE TABLE IF NOT EXISTS equipment_aliases (
        identity_key TEXT PRIMARY KEY, equipment_id INTEGER NOT NULL REFERENCES equipment(id))''')
    db.execute('''CREATE TABLE IF NOT EXISTS equipment_icons (
        equipment_id INTEGER PRIMARY KEY REFERENCES equipment(id),
        image_file TEXT NOT NULL,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)''')
    db.execute('''CREATE TABLE IF NOT EXISTS item_candidates (
        identity_key TEXT PRIMARY KEY, text TEXT NOT NULL, occurrences INTEGER NOT NULL DEFAULT 1,
        last_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)''')


def item_list(db_file=DB_FILE):
    with database_connection(str(db_file)) as db:
        _init(db)
        return db.execute('SELECT id, name FROM equipment ORDER BY last_seen DESC, name').fetchall()


def find_item(name, db_file=DB_FILE):
    key=key_for(name)
    if not key: return None
    with database_connection(str(db_file)) as db:
        _init(db)
        row=db.execute('SELECT id,name FROM equipment WHERE identity_key=?',(key,)).fetchone()
        if not row:
            row=db.execute('SELECT e.id,e.name FROM equipment e JOIN equipment_aliases a ON e.id=a.equipment_id WHERE a.identity_key=?',(key,)).fetchone()
        return row


def register_item(name, db_file=DB_FILE):
    name=' '.join((name or '').split())
    key=key_for(name)
    if not key or len(name)>100 or key in {'objet non identifie', 'inconnu'}:
        raise ValueError('Nom d’équipement invalide')
    with database_connection(str(db_file)) as db:
        _init(db)
        db.execute('INSERT OR IGNORE INTO equipment(name, identity_key) VALUES(?,?)',(name,key))
        row=db.execute('SELECT id,name FROM equipment WHERE identity_key=?',(key,)).fetchone()
        if row:
            db.execute('UPDATE equipment SET last_seen=CURRENT_TIMESTAMP WHERE id=?',(row[0],))
        return row


class IconIdentityConflict(ValueError):
    """Visual identity is already linked to a different equipment."""


def item_icon(name, db_file=DB_FILE):
    """Return the local icon path for a known item, or None."""
    row = find_item(name, db_file)
    if not row:
        return None
    with database_connection(str(db_file)) as db:
        _init(db)
        found = db.execute('SELECT image_file FROM equipment_icons WHERE equipment_id=?',
                           (row[0],)).fetchone()
    path = Path(found[0]) if found else None
    return path if path and path.is_file() else None


def register_item_with_icon(name, image, db_file=DB_FILE, icons_dir=None):
    """Store a stable name/icon pair locally. Caller confirms repeated OCR frames."""
    from forgely_item_icons import normalize_icon, icon_distance
    icon = normalize_icon(image)
    if icon is None:
        raise ValueError('Logo de l’objet absent ou illisible')
    name = ' '.join((name or '').split())
    key = key_for(name)
    if not key or len(name) > 100 or key in {'objet non identifie', 'inconnu'}:
        raise ValueError('Nom d’équipement invalide')
    db_file = Path(db_file)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    icons_dir = Path(icons_dir) if icons_dir else db_file.parent / 'icones_equipements'
    with database_connection(str(db_file), timeout=15) as db:
        _init(db)
        row = db.execute('SELECT id,name FROM equipment WHERE identity_key=?', (key,)).fetchone()
        if not row:
            row = db.execute('SELECT e.id,e.name FROM equipment e '
                'JOIN equipment_aliases a ON a.equipment_id=e.id '
                'WHERE a.identity_key=?', (key,)).fetchone()
        item_id = row[0] if row else None
        for other_id, filename in db.execute('SELECT equipment_id,image_file FROM equipment_icons'):
            path = Path(filename)
            if not path.is_file():
                continue
            try:
                with Image.open(path) as stored:
                    distance = icon_distance(icon, stored)
            except (OSError, ValueError):
                continue
            if other_id == item_id:
                if distance > 18:
                    raise IconIdentityConflict('Le logo ne correspond pas à celui déjà enregistré pour cet objet')
            elif distance <= 9:
                raise IconIdentityConflict('Ce logo ressemble à celui d’un autre objet enregistré')
        if row is None:
            db.execute('INSERT INTO equipment(name,identity_key) VALUES (?,?)', (name,key))
            item_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
            row = (item_id,name)
        db.execute('UPDATE equipment SET last_seen=CURRENT_TIMESTAMP WHERE id=?',(item_id,))
        exists = db.execute('SELECT 1 FROM equipment_icons WHERE equipment_id=?', (item_id,)).fetchone()
        if not exists:
            icons_dir.mkdir(parents=True, exist_ok=True)
            dest = icons_dir / f'item_{item_id}.png'
            icon.save(dest, 'PNG')
            db.execute('INSERT INTO equipment_icons(equipment_id,image_file) VALUES (?,?)',
                       (item_id,str(dest)))
        return row

def add_alias(alias, item_id, db_file=DB_FILE):
    key=key_for(alias)
    if not key: raise ValueError('Alias vide')
    with database_connection(str(db_file)) as db:
        _init(db)
        if not db.execute('SELECT id FROM equipment WHERE id=?',(item_id,)).fetchone():
            raise ValueError('Équipement inconnu')
        current=db.execute('SELECT id FROM equipment WHERE identity_key=?',(key,)).fetchone()
        if current and current[0] != item_id:
            raise ValueError('Cet alias appartient déjà à un autre équipement')
        db.execute('INSERT OR REPLACE INTO equipment_aliases(identity_key,equipment_id) VALUES (?,?)',(key,item_id))


def remember_candidate(text, db_file=DB_FILE):
    text=' '.join((text or '').split())[:100]
    key=key_for(text)
    if not key or len(text)<4 or len(text)>100 or find_item(text,db_file): return
    with database_connection(str(db_file)) as db:
        _init(db)
        db.execute('''INSERT INTO item_candidates(identity_key,text) VALUES (?,?)
          ON CONFLICT(identity_key) DO UPDATE SET occurrences=occurrences+1,last_seen=CURRENT_TIMESTAMP''',(key,text))


def pending_items(db_file=DB_FILE):
    with database_connection(str(db_file)) as db:
        _init(db)
        return db.execute('SELECT text,occurrences FROM item_candidates ORDER BY last_seen DESC LIMIT 30').fetchall()


def item_history(item_name, limit=100, db_file=DB_FILE):
    # Existing observations schema is compatible; no destructive migrations.
    from forgely_data import connect
    with closing_transaction(connect(db_file)) as db:
        return db.execute('''SELECT captured_at,rune,outcome,source FROM observations
                             WHERE item=? ORDER BY id DESC LIMIT ?''',(item_name,limit)).fetchall()
