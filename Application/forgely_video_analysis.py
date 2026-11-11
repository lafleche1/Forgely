"""Image-only MP4 analysis, with conservative temporal pairing and resumable OCR."""
from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from functools import lru_cache

from forgely_video_store import VERSION, atomic_json, catalogue, item_profile

DEFAULT_ZONES = {'item': (.285,.148,.61,.19), 'jet': (.285,.175,.61,.825),
                 'rune': (.492,.27,.598,.377), 'history': (.168,.266,.289,.786),
                 'pool': (.325,.193,.394,.229)}


def rune_label(text):
    """Exact label in a user-defined rune slot, never a general screen search."""
    from forgely_detection import norm
    from forgely_dofocus import RUNE_REFERENCES
    clean=norm(text)
    matches=[r for r in RUNE_REFERENCES if clean in (norm(r),norm('Rune '+r))]
    return matches[0] if len(matches)==1 else None


@lru_cache(maxsize=1)
def reader_revision():
    digest=hashlib.sha256()
    root=Path(__file__).parent
    for name in ('forgely_video_analysis.py','forgely_jet.py','forgely_ocr_backend.py',
                 'forgely_detection.py','forgely_item_vision.py','forgely_atelier.py',
                 'references/poids_runes_client_3_7_13_17.json'):
        digest.update((root/name).read_bytes())
    return digest.hexdigest()


def validate_zones(zones):
    if set(zones) != set(DEFAULT_ZONES):
        raise ValueError('Définis les cinq zones : objet, jet, rune, journal et puits.')
    for box in zones.values():
        if (not isinstance(box, (list, tuple)) or len(box) != 4
                or not all(isinstance(v, (float,int)) and math.isfinite(v) and 0 <= v <= 1 for v in box)
                or box[2] <= box[0] or box[3] <= box[1]):
            raise ValueError('Zone invalide : trace un rectangle à l’intérieur de l’image.')


def video_info(path):
    import cv2
    path = Path(path)
    if not path.is_file() or path.suffix.lower() != '.mp4':
        raise ValueError('Choisis un fichier MP4 local existant.')
    cap = cv2.VideoCapture(str(path))
    try:
        fps = cap.get(cv2.CAP_PROP_FPS); count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        if not cap.isOpened() or not math.isfinite(fps) or fps <= 0 or count <= 0:
            raise ValueError('Vidéo illisible ou durée inconnue.')
        return {'fps': fps, 'frames': int(count), 'duration': count/fps,
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), 'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}
    finally:
        cap.release()


def apply_item_override(reading, item_id):
    if item_id is None:return reading
    item,profile=item_profile(item_id)
    if not item or not profile:raise ValueError('Objet manuel absent du catalogue.')
    reading=deepcopy(reading)
    if reading.get('item_id') is None:
        reading.update(item_id=item_id,natural_max=profile)
        reading.setdefault('raw',{})['identity_source']='manual_session_confirmation'
    return reading


def frame_at(path, second):
    import cv2
    from PIL import Image
    if not math.isfinite(second) or second < 0:
        raise ValueError('Position vidéo invalide')
    cap = cv2.VideoCapture(str(path))
    try:
        cap.set(cv2.CAP_PROP_POS_MSEC, second*1000)
        ok, frame = cap.read()
        if not ok:
            raise ValueError('Image vidéo indisponible à cet instant.')
        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    finally:
        cap.release()


class VisualReader:
    def __init__(self, zones, ocr=None):
        validate_zones(zones)
        from forgely_ocr_backend import extract_text
        self.zones = deepcopy(zones)
        self.ocr = ocr or extract_text
        self.cache = OrderedDict()
        self.registered = tuple((i.item_id, i.identity_name) for i in catalogue().items)
        self.names = {i.identity_name: i.item_id for i in catalogue().items}
        from forgely_vision import RuneLibrary
        from forgely_dofocus import RUNE_REFERENCES
        from forgely_data import DATA_DIR
        self.icons = RuneLibrary(DATA_DIR/'icones_runes', tuple(RUNE_REFERENCES))
        self._rune_patch = None

    def __call__(self, image):
        from forgely_atelier import choose_reliquat
        from forgely_detection import normalize_rune_name
        from forgely_dofocus import RUNE_REFERENCES, normalise_jet
        from forgely_item_vision import identify_known
        from forgely_jet import parse_jet, read_effects_ocr
        raw = {}
        for name, box in self.zones.items():
            patch = image.crop(tuple(round(v*image.size[i%2]) for i,v in enumerate(box)))
            if name == 'rune':
                self._rune_patch = patch
            digest = (name, patch.size, hashlib.sha256(patch.tobytes()).digest())
            if digest not in self.cache:
                text = read_effects_ocr(patch, self.ocr) if name == 'jet' else self.ocr(patch)
                self.cache[digest] = text
                if len(self.cache) > 128:
                    self.cache.popitem(last=False)
            raw[name] = self.cache[digest]
        heading = raw['history'].splitlines()[0] if raw['history'].splitlines() else ''
        item_name = identify_known(raw['item'], self.registered) or identify_known(heading, self.registered)
        item_id = self.names.get(item_name)
        _, profile = item_profile(item_id)
        rune = rune_label(raw['rune']) or normalize_rune_name(raw['rune'], tuple(RUNE_REFERENCES))
        if not rune and self._rune_patch is not None:
            rune = self.icons.predict(self._rune_patch).rune
        return {'item_id': item_id, 'natural_max': profile, 'jet': normalise_jet(parse_jet(raw['jet'])) or {},
                'pool': choose_reliquat(raw['jet'], raw['pool']),
                'rune': rune,
                'history': raw['history'], 'raw': raw}


class Timeline:
    """Only a stable, distinct inserted journal row authorizes a paired attempt."""
    def __init__(self):
        self.events = []
        self.boundaries = []
        self._reset()

    def _reset(self):
        self.item = None
        self.state_key = self.history_key = None
        self.state_count = self.history_count = 0
        self.state_changed_at = 0.
        self.stable = None
        self.baseline = None
        self.frozen = None
        self.pending = None

    def boundary(self, reason, second=None):
        if self.pending:
            self.pending['issues'].append(reason)
            self.events.append(self.pending)
        self.boundaries.append({'time': second, 'reason': reason})
        self._reset()

    def observe(self, second, reading, evidence):
        from forgely_detection import history_signature, new_row_shift, explicit_outcome, normalize_rune_name
        from forgely_dofocus import RUNE_REFERENCES
        item_id = reading.get('item_id')
        if not item_id or not reading.get('jet'):
            self.boundary('unreadable_or_unknown_item', second)
            return
        if self.item is not None and self.item != item_id:
            self.boundary('item_changed', second)
        self.item = item_id
        history = history_signature(reading.get('history',''))
        state = {'jet': deepcopy(reading['jet']), 'pool': reading.get('pool')}
        key = json.dumps(state, sort_keys=True)
        # Freeze the last known pre-state as soon as either journal or jet changes.
        if self.stable and self.frozen is None and (history != self.baseline or key != self.state_key):
            self.frozen = deepcopy(self.stable)
        if key != self.state_key:self.state_changed_at=second
        self.state_count = self.state_count+1 if key == self.state_key else 1
        self.state_key = key
        self.history_count = self.history_count+1 if history == self.history_key else 1
        self.history_key = history
        if history and self.history_count >= 2:
            if self.baseline is None:
                self.baseline = history
            elif history != self.baseline:
                shift = new_row_shift(self.baseline, history)
                header = self.baseline[0] == history[0] and not explicit_outcome(history[0])
                row = history[1] if header and len(history)>1 else history[0]
                outcome = explicit_outcome(row)
                overlapping = self.pending is not None
                if self.pending:
                    self.pending['issues'].append('multiple_events')
                    self.events.append(self.pending)
                    self.pending = None
                if outcome:
                    pre = None if overlapping else (self.frozen or self.stable)
                    explicit_rune = normalize_rune_name(row, tuple(RUNE_REFERENCES))
                    prior_rune = pre.get('rune') if pre else None
                    rune = explicit_rune or prior_rune
                    issues = []
                    if overlapping:issues.append('multiple_events')
                    if shift != 1:
                        issues.append('multiple_events' if shift > 1 else 'unproven_history_shift')
                    if pre is None or second - pre['time'] > 8:
                        issues.append('missing_recent_before')
                    if not explicit_rune and (not rune or rune != reading.get('rune')):
                        issues.append('ambiguous_rune')
                    ident = hashlib.sha256(f'{item_id}|{second:.3f}|{history}'.encode()).hexdigest()[:24]
                    self.pending = {'id': ident, 'time': second, 'before_time': pre['time'] if pre else None,
                        'after_time': None, 'item_id': item_id, 'natural_max': reading.get('natural_max', {}),
                        'rune': rune, 'outcome': outcome, 'before': deepcopy(pre['snapshot']) if pre else None,
                        'after': None, 'event_confirmed': shift == 1, 'stable': False,
                        'issues': issues, 'status': 'candidate',
                        'evidence': {'before': pre['evidence'] if pre else None, 'after': None},
                        'raw': {'before': deepcopy(pre.get('raw',{})) if pre else {}, 'after': reading.get('raw',{})}}
                self.baseline = history
        if self.state_count >= 2 and self.history_count >= 2:
            self.stable = {'snapshot': state, 'time': second, 'evidence': evidence,
                           'rune': reading.get('rune'), 'raw': reading.get('raw',{})}
            if (self.pending and second-self.pending['time']>=.5
                    and second-self.state_changed_at>=.5):
                self.pending.update(after=deepcopy(state), after_time=second, stable=True)
                self.pending['evidence']['after'] = evidence
                self.pending['raw']['after'] = reading.get('raw',{})
                self.events.append(self.pending)
                self.pending = None
                self.frozen = None
            # Effects may settle before the journal is redrawn. Keep the old
            # pre-state until its event is paired, or discard the pairing after
            # the bounded attribution window rather than substituting the post.
            elif self.frozen and second-self.frozen['time']>8:
                self.frozen = None
        if self.pending and second - self.pending['time'] > 8:
            self.pending['issues'].append('missing_stable_after')
            self.events.append(self.pending)
            self.pending = None

    def finish(self):
        if self.pending:
            self.pending['issues'].append('end_before_stable_after')
            self.events.append(self.pending)
            self.pending = None


def analyze_video(path, store, zones, cancel, progress, reader=None, *, item_override=None):
    """Replays cached reads when resuming, preserving temporal state and reviewed edits."""
    import cv2
    import numpy as np
    from PIL import Image
    validate_zones(zones)
    path = Path(path).resolve()
    info = video_info(path)
    progress({'phase':'hash', 'time':0, 'duration': info['duration']})
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1024*1024):
            digest.update(block)
            if cancel.is_set():
                return {'status':'paused', 'path':str(path), 'events':[], 'cancelled_before_analysis':True}
    video_id = digest.hexdigest()
    folder = store.folder(video_id)
    apply_item_override({},item_override)
    config = {'zones': zones, 'version': VERSION, 'reader_revision': reader_revision(), 'item_override':item_override}
    config_id = hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()[:16]
    cache = folder / 'reads' / config_id
    cache.mkdir(parents=True, exist_ok=True)
    old = store.load_session(video_id) if (folder/'session.json').exists() else {}
    if old and old.get('config_id')!=config_id:
        # Keep previous configurations and every correction as an immutable
        # review archive before starting a different analysis.
        archive=folder/'archives'/(old.get('config_id','legacy')+'-'+old.get('updated_at','old').replace(':','-')+'.json')
        atomic_json(archive,old)
    edits = {e['id']: e for e in old.get('events',[]) if e.get('reviewed_at')} if old.get('config_id')==config_id else {}
    previous_events=old.get('events',[]) if old.get('config_id')==config_id else []
    def merged_events(events,cursor,final=False):
        merged={e['id']:deepcopy(e) for e in previous_events if e.get('reviewed_at') or (not final and e.get('time',0)>=cursor)}
        merged.update({e['id']:deepcopy(edits.get(e['id'],e)) for e in events})
        return sorted(merged.values(),key=lambda e:(e.get('time',0),e['id']))
    session = {'id':video_id, 'path':str(path), 'info':info, 'config':config, 'config_id':config_id,
               'events':[], 'status':'running', 'cursor':0, 'source':'real_video', 'audio_processed':False}
    reader = reader or VisualReader(zones)
    timeline = Timeline()
    cap = cv2.VideoCapture(str(path))
    second = 0.; previous = None; fine_until = -1.; saved_at = -10.
    try:
        while second < info['duration'] and not cancel.is_set():
            cap.set(cv2.CAP_PROP_POS_MSEC, second*1000)
            ok, frame = cap.read()
            if not ok:
                timeline.boundary('unreadable_frame',second)
                second += .5
                continue
            small = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY),(160,90)).astype(np.float32)/255
            change = float(np.mean(np.abs(small-previous))) if previous is not None else 0
            if previous is not None and change > .38:
                timeline.boundary('scene_cut_or_layout_change',second)
            if change > .01:
                fine_until = second + 1
            previous = small
            stamp = f'{round(second*1000):010d}'
            image_path = cache / (stamp+'.jpg')
            read_path = cache / (stamp+'.json')
            if read_path.exists() and image_path.exists():
                reading = json.loads(read_path.read_text(encoding='utf-8'))
            else:
                image = Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
                reading = apply_item_override(reader(image),item_override)
                image.save(image_path,quality=90)
                atomic_json(read_path,reading)
            timeline.observe(second,reading,str(image_path.relative_to(folder)))
            session.update(cursor=second, events=merged_events(timeline.events,second), boundaries=timeline.boundaries)
            if second-saved_at >= 5:
                store.save_session(session,record_history=False)
                saved_at = second
            progress({'phase':'analysis','time':second,'duration':info['duration'],'events':len(timeline.events)})
            second = round(second+(.125 if second<fine_until else .5),3)
        timeline.finish()
        session.update(events=merged_events(timeline.events,second,final=not cancel.is_set()), boundaries=timeline.boundaries,
                       status='paused' if cancel.is_set() else 'done')
        store.save_session(session,record_history=False)
        return session
    except Exception:
        session.update(status='error',events=merged_events(timeline.events,second))
        store.save_session(session,record_history=False)
        raise
    finally:
        cap.release()
