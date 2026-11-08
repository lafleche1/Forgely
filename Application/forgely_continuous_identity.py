"""Continuous, passive identification of the item in the CURRENT workshop slot.

The history can contain an older item's name. A slot icon is evidence of the
current object, but NOT of its name. Anonymous visual records are kept separate
from the named catalogue until there is independent name evidence.
"""
from __future__ import annotations
from forgely_sqlite import database_connection
import json
import re
import sqlite3
from pathlib import Path
from PIL import Image, ImageStat
from forgely_item_icons import normalize_icon, icon_distance
from forgely_items import key_for
from forgely_data import DB_FILE
from dataclasses import dataclass


@dataclass(frozen=True)
class SlotEvidence:
    context: tuple
    icon: object
    count: int
    captured_ns: int


class RapidSlotTracker:
    """Icon stability from distinct captures, independent of slow text OCR."""
    def __init__(self):
        self.context=None
        self.tracker=CurrentSlotTracker()

    def observe(self,icon,context,captured_ns):
        icon=normalize_icon(icon)
        if context!=self.context or icon is None:
            self.context=context
            self.tracker.reset()
        if icon is None:return None
        self.tracker.observe(icon)
        return SlotEvidence(context,self.tracker.icon.copy(),self.tracker.count,captured_ns)


def prime_slot_tracker(tracker,evidence,icon,context,now_ns):
    """Reuse recent same-slot captures; natural-range checks still run in OCR."""
    if (not isinstance(evidence,SlotEvidence) or evidence.context!=context or
            evidence.count<3 or not 0<=now_ns-evidence.captured_ns<=2_000_000_000 or
            icon is None or icon_distance(evidence.icon,icon)>17):return False
    if tracker.icon is not None and icon_distance(tracker.icon,icon)>17:return False
    tracker.icon=evidence.icon.copy()
    tracker.count=max(tracker.count,tracker.frames-1)
    return True

SLOT_BOX = (.393, .195, .407, .223)  # item slot, from supplied 1648x928 DOFUS capture


def crop_current_item(image):
    w, h = image.size
    return image.crop((round(SLOT_BOX[0]*w), round(SLOT_BOX[1]*h),
                       round(SLOT_BOX[2]*w), round(SLOT_BOX[3]*h)))


def current_icon(image):
    patch = normalize_icon(crop_current_item(image))
    if patch is None:
        return None
    # A blank slot has a flat blue-grey background; reject nearly flat crops.
    if max(ImageStat.Stat(patch).stddev) < 17:
        return None
    return patch


STAT_NAMES = ('vitalite', 'force', 'intelligence', 'chance', 'agilite',
              'sagesse', 'puissance', 'initiative', 'prospection',
              'resistance', 'dommages', 'tacle', 'fuite', 'portee',
              'invocation', 'pa', 'pm', 'soin', 'critique')


def effect_signature(text):
    """Stable min/max and characteristic names; NEVER include current jet.

    Requires an explicit Min/Max pair followed by a characteristic, so a bare
    OCR quantity or a PA/Ra inventory count cannot become a fingerprint.
    """
    import unicodedata
    pairs = set()
    for raw in (text or '').splitlines():
        folded = ''.join(c for c in unicodedata.normalize('NFKD', raw.lower())
                         if not unicodedata.combining(c))
        match = re.match(r'^\s*(\d{1,4})\s+(\d{1,4})\s+(.+)$', folded)
        if not match:
            continue
        lo, hi = int(match.group(1)), int(match.group(2))
        if lo > hi or hi > 10000:
            continue
        words = match.group(3)
        labels = [s for s in STAT_NAMES if re.search(r'\b'+s+r'\b', words)]
        if len(labels) == 1:
            pairs.add((labels[0], lo, hi))
    return tuple(sorted(pairs))


def strong_signature_change(a, b):
    """Several incompatible natural ranges indicate a replaced item, not FM.

    Compare stable min/max ranges, never the mutable current values.
    """
    a = {name:(lo,hi) for name,lo,hi in (a or ())}
    b = {name:(lo,hi) for name,lo,hi in (b or ())}
    if len(a) < 3 or len(b) < 3:
        return False
    conflicts = sum(a[k] != b[k] for k in a.keys() & b.keys())
    # Newly visible names are normal when scrolling. Only incompatible ranges
    # for shared characteristics support a change; artwork is checked separately.
    return conflicts >= 2


def signatures_compatible(a, b):
    """A single matching line is weak evidence; a contradiction is a veto."""
    a = {name:(lo,hi) for name,lo,hi in (a or ())}
    b = {name:(lo,hi) for name,lo,hi in (b or ())}
    shared = a.keys() & b.keys()
    return not any(a[name] != b[name] for name in shared)


class CurrentSlotTracker:
    def __init__(self, frames=3):
        self.frames = frames
        self.reset()

    def reset(self):
        self.icon = None
        self.count = 0
        self.misses = 0
        self.signature = ()
        self.generation = getattr(self, 'generation', 0) + 1

    def observe(self, icon, signature=()):
        icon = normalize_icon(icon)
        if icon is None:
            self.misses += 1
            if self.misses == 3:
                self.reset()
                self.misses = 3  # The caller must still see confirmed absence.
            return False, False
        changed = self.icon is not None and (
            icon_distance(icon, self.icon) > 17 or
            strong_signature_change(self.signature, signature))
        if changed:
            self.reset()
        if self.icon is None:
            self.count = 1
        else:
            self.count += 1
        self.icon = icon
        self.misses = 0
        if signature:
            if self.signature and not signatures_compatible(self.signature, signature):
                self.signature = tuple(signature)
            else:
                self.signature = tuple(signature)
        return self.count >= self.frames, changed


def _db_init(db):
    db.execute('''CREATE TABLE IF NOT EXISTS equipment_current_icons (
        equipment_id INTEGER PRIMARY KEY,
        image_file TEXT NOT NULL,
        effect_signature TEXT NOT NULL DEFAULT '[]')''')
    db.execute('''CREATE TABLE IF NOT EXISTS equipment_provisional (
        id INTEGER PRIMARY KEY,
        image_file TEXT NOT NULL,
        effect_signature TEXT NOT NULL DEFAULT '[]',
        last_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)''')


def _candidates(db, table, icon, signature):
    matches = []
    for row_id, filename, raw_signature in db.execute(
            f'SELECT {"equipment_id" if table == "equipment_current_icons" else "id"},image_file,effect_signature FROM {table}'):
        path = Path(filename)
        try:
            with Image.open(path) as existing:
                distance = icon_distance(icon, existing)
        except (OSError, ValueError):
            continue
        stored = tuple(tuple(x) for x in json.loads(raw_signature))
        if not signatures_compatible(signature, stored):
            continue
        matches.append((distance, row_id, stored))
    return sorted(matches)


def match_bundled_slot_icon(icon):
    """Identify using ONLY verified reference artwork of the workshop slot.

    Each bundled image must be labelled from an independently identified
    capture. Unknown items remain unknown; never infer a name from history.
    """
    icon = normalize_icon(icon)
    if icon is None:
        return None
    references = (("ANNEAU DU CYCLOÏDE", Path(__file__).parent / "assets" /
                   "equipment_slot_refs" / "anneau_du_cycloide.png"),)
    matches = []
    for name, filename in references:
        try:
            with Image.open(filename) as reference:
                matches.append((icon_distance(icon, reference), name))
        except (OSError, ValueError):
            continue
    matches.sort()
    if matches and matches[0][0] <= 13 and (len(matches) == 1 or matches[1][0] - matches[0][0] >= 8):
        return matches[0][1]
    return None


def match_current_item(icon, signature=(), db_file=DB_FILE):
    """Only return a unique, close visual match with no contradictory bounds."""
    icon = normalize_icon(icon)
    if icon is None:
        return None
    bundled = match_bundled_slot_icon(icon)
    if bundled:
        # Never allow a hardcoded image reference to overrule an incompatible
        # natural profile observed in the current workshop.
        from forgely_tools import natural_bounds
        from forgely_jet import norm
        bounds = natural_bounds(bundled)
        expected = {norm(k): tuple(v) for k,v in bounds.items()}
        conflicts = sum(1 for k,lo,hi in signature if k in expected and expected[k] != (lo,hi))
        extras = sum(1 for k,lo,hi in signature if k not in expected)
        if len(signature) >= 3 and (conflicts >= 2 or extras >= 3):
            return None
        return bundled
    with database_connection(str(db_file)) as db:
        _db_init(db)
        choices = _candidates(db, 'equipment_current_icons', icon, signature)
        if choices and choices[0][0] <= 10 and (len(choices) == 1 or choices[1][0] - choices[0][0] >= 8):
            row = db.execute('SELECT name FROM equipment WHERE id=?', (choices[0][1],)).fetchone()
            return row[0] if row else None
        # Backward compatibility with versions that saved only the history
        # artwork. A VERY close, unambiguous match can recover that catalogue
        # entry; never guess from a weak similarity.
        if not choices:
            legacy = []
            try:
                rows = db.execute('SELECT equipment_id,image_file FROM equipment_icons').fetchall()
            except sqlite3.OperationalError:
                rows = []
            for item_id, filename in rows:
                try:
                    with Image.open(filename) as old:
                        legacy.append((icon_distance(icon, old), item_id))
                except (OSError, ValueError):
                    continue
            legacy.sort()
            if legacy and legacy[0][0] <= 12 and (len(legacy) == 1 or legacy[1][0]-legacy[0][0] >= 9):
                row = db.execute('SELECT name FROM equipment WHERE id=?', (legacy[0][1],)).fetchone()
                return row[0] if row else None
        return None


def remember_current_item(name, icon, signature=(), db_file=DB_FILE, icons_dir=None):
    """Save the current slot icon only for an ALREADY verified named item."""
    icon = normalize_icon(icon)
    if icon is None:
        raise ValueError('Emplacement de l’objet illisible')
    db_file = Path(db_file)
    with database_connection(str(db_file)) as db:
        _db_init(db)
        row = db.execute('SELECT id FROM equipment WHERE identity_key=?', (key_for(name),)).fetchone()
        if row is None:
            raise ValueError('Nom non confirmé dans le catalogue')
        item_id = row[0]
        matches = _candidates(db, 'equipment_current_icons', icon, signature)
        for distance, other_id, _ in matches:
            if other_id != item_id and distance <= 10:
                raise ValueError('Icône déjà associée à un autre équipement')
        previous = db.execute('SELECT image_file FROM equipment_current_icons WHERE equipment_id=?', (item_id,)).fetchone()
        if previous:
            with Image.open(previous[0]) as old:
                if icon_distance(icon, old) > 17:
                    raise ValueError('Icône actuelle différente de la référence enregistrée')
        else:
            icons_dir = Path(icons_dir) if icons_dir else db_file.parent / 'icones_equipements_actifs'
            icons_dir.mkdir(parents=True, exist_ok=True)
            dest = icons_dir / f'current_{item_id}.png'
            icon.save(dest, 'PNG')
            db.execute('INSERT INTO equipment_current_icons VALUES (?,?,?)',
                       (item_id, str(dest), json.dumps(signature, ensure_ascii=False)))
        if previous and signature:
            db.execute('UPDATE equipment_current_icons SET effect_signature=? WHERE equipment_id=?',
                       (json.dumps(signature, ensure_ascii=False), item_id))
        # Once named, a matching anonymous record is no longer needed.
        for distance, provisional_id, _ in _candidates(db, 'equipment_provisional', icon, signature):
            if distance <= 10:
                db.execute('DELETE FROM equipment_provisional WHERE id=?', (provisional_id,))
        return item_id


def remember_provisional(icon, signature=(), db_file=DB_FILE, icons_dir=None):
    """Store a stable, *anonymous* slot; never fabricate an item name."""
    icon = normalize_icon(icon)
    if icon is None:
        return None
    db_file = Path(db_file)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    with database_connection(str(db_file)) as db:
        _db_init(db)
        matches = _candidates(db, 'equipment_provisional', icon, signature)
        if matches and matches[0][0] <= 10:
            record_id = matches[0][1]
            db.execute('UPDATE equipment_provisional SET last_seen=CURRENT_TIMESTAMP WHERE id=?', (record_id,))
            return record_id
        icons_dir = Path(icons_dir) if icons_dir else db_file.parent / 'objets_provisoires'
        icons_dir.mkdir(parents=True, exist_ok=True)
        cur = db.execute('INSERT INTO equipment_provisional (image_file,effect_signature) VALUES (?,?)',
                         ('', json.dumps(signature, ensure_ascii=False)))
        record_id = cur.lastrowid
        dest = icons_dir / f'provisoire_{record_id}.png'
        icon.save(dest, 'PNG')
        db.execute('UPDATE equipment_provisional SET image_file=? WHERE id=?', (str(dest), record_id))
        return record_id
