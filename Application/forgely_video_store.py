"""Auditable video observations. Originals and screen observations are never altered."""
from __future__ import annotations

from copy import deepcopy
from contextlib import closing
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile

VERSION = 'visual-video-v1'


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name, suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class VideoStore:
    def __init__(self, directory):
        self.directory = Path(directory)

    def folder(self, video_id):
        if not isinstance(video_id, str) or not re.fullmatch('[a-f0-9]{64}', video_id):
            raise ValueError('Identifiant vidéo invalide')
        return self.directory / video_id

    def save_session(self, session, *, record_history=True):
        path = self.folder(session['id']) / 'session.json'
        data = deepcopy(session)
        if path.exists():
            previous = json.loads(path.read_text(encoding='utf-8'))
            history = previous.get('history', [])
            if record_history and previous.get('events') != data.get('events'):
                history.append({'at': now(), 'events': previous.get('events', [])})
            data['history'] = history
        data['version'] = VERSION
        data['updated_at'] = now()
        atomic_json(path, data)

    def load_session(self, video_id):
        return json.loads((self.folder(video_id) / 'session.json').read_text(encoding='utf-8'))

    def sessions(self):
        if not self.directory.exists():
            return []
        result = []
        for path in sorted(self.directory.glob('*/session.json')):
            try:
                result.append(self.load_session(path.parent.name))
            except (ValueError, OSError):
                continue
        return result


@lru_cache(maxsize=1)
def catalogue():
    from forgely_equipment_catalog import EquipmentCatalog
    return EquipmentCatalog()


def item_profile(item_id):
    from forgely_equipment_catalog import equipment_bounds
    if type(item_id) is not int:
        return None, {}
    item = catalogue().get(item_id)
    bounds = equipment_bounds(item) if item else {}
    return item, {name: pair[1] for name, pair in bounds.items()}


def qualify_event(event):
    """Recompute eligibility, including for manually corrected or imported JSON."""
    from forgely_expert import audit_transition
    from forgely_rules import finite_number
    reasons = []
    if event.get('status') == 'rejected':
        reasons.append('Rejeté par l’utilisateur')
    item, profile = item_profile(event.get('item_id'))
    if not item or not profile or event.get('natural_max') != profile:
        reasons.append('Profil naturel absent ou différent du catalogue')
    if event.get('event_confirmed') is not True or event.get('stable') is not True:
        reasons.append('Événement distinct et jets stables non confirmés')
    if event.get('issues'):
        reasons.append('Séquence ambiguë : ' + ', '.join(map(str, event['issues'])))
    before, after = event.get('before'), event.get('after')
    for snapshot in (before, after):
        if (not isinstance(snapshot, dict) or not isinstance(snapshot.get('jet'), dict)
                or not profile or not set(profile).issubset(snapshot['jet'])
                or not finite_number(snapshot.get('pool'), nonnegative=True)):
            reasons.append('Jet complet ou puits connu manquant')
    evidence = event.get('evidence', {})
    if not isinstance(evidence, dict) or not all(evidence.get(k) for k in ('before', 'after')):
        reasons.append('Images avant/après manquantes')
    audit = audit_transition(event.get('rune'), event.get('outcome'), before, after,
                             complete=not reasons)
    if audit['status'] != 'cohérent':
        reasons.append('Comptabilité non vérifiée : ' + audit['status'])
    return {'eligible': not reasons, 'reasons': reasons, 'audit': audit,
            'item': item.identity_name if item else None}


def _schema(db):
    db.execute('''CREATE TABLE IF NOT EXISTS video_observations (
        video_id TEXT NOT NULL, event_id TEXT NOT NULL, data_json TEXT NOT NULL,
        updated_at TEXT NOT NULL, source TEXT NOT NULL CHECK(source='video_verified'),
        PRIMARY KEY(video_id,event_id))''')


def transfer_session(session, db_file):
    """Replace a video's contributions atomically; repeated imports are idempotent."""
    VideoStore('.').folder(session['id'])
    accepted = []
    seen = set()
    for event in session.get('events', []):
        ident = event.get('id')
        if not isinstance(ident, str) or not ident or ident in seen:
            raise ValueError('Événement absent ou dupliqué')
        seen.add(ident)
        if qualify_event(event)['eligible']:
            accepted.append((ident, json.dumps(event, ensure_ascii=False, allow_nan=False)))
    path = Path(db_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(str(path), timeout=10)) as db, db:
        _schema(db)
        db.execute('DELETE FROM video_observations WHERE video_id=?', (session['id'],))
        db.executemany('INSERT INTO video_observations VALUES(?,?,?,?,?)',
                       [(session['id'], ident, raw, now(), 'video_verified') for ident, raw in accepted])
    return {'accepted': len(accepted), 'excluded': len(seen)-len(accepted), 'source': 'video_verified'}


def qualified_video_rows(db_file):
    """No creation during reads. Revalidate against current weights/profile."""
    path = Path(db_file)
    if not path.exists():
        return []
    with closing(sqlite3.connect(str(path), timeout=5)) as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='video_observations'").fetchone():
            return []
        rows = db.execute('SELECT video_id,event_id,data_json FROM video_observations WHERE source=?',
                          ('video_verified',)).fetchall()
    output = []
    for video_id, ident, raw in rows:
        try:
            event = json.loads(raw)
            if qualify_event(event)['eligible']:
                output.append((video_id, ident, event))
        except (ValueError, TypeError, KeyError):
            continue
    return output
