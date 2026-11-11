"""Laboratoire FM local en arrière-plan, sans capture supplémentaire.

Lit uniquement les transitions déjà enregistrées. Les OCR automatiques restent
non vérifiés : statistiques exploratoires, jamais probabilités garanties.
"""
from __future__ import annotations
from forgely_sqlite import database_connection
import json, sqlite3, threading
from copy import deepcopy
from collections import Counter, defaultdict
from pathlib import Path
from forgely_data import DB_FILE
from forgely_probabilites import wilson
from forgely_rules import finite_number
from forgely_online_experience import OnlineExperience
from forgely_runtime_cache import database_revision


def pool_bucket(value):
    if value == 0: return '0'
    if value < 10: return '1-9'
    if value < 30: return '10-29'
    if value < 100: return '30-99'
    return '100+'


def jet_signature(jet):
    """Exact observed values, not only line names. No missing stat inferred as zero."""
    if not isinstance(jet,dict) or not jet or any(not isinstance(k,str) or not finite_number(v) for k,v in jet.items()):
        raise ValueError('Jet invalide')
    return tuple(sorted(jet.items()))


def compute_snapshot(db_file=DB_FILE, *, minimum=30):
    """One consistent read; no simulation or unknown observation sources."""
    path=Path(db_file)
    if not path.exists(): return {'groups':{}, 'observations':0, 'rejected':0}
    with database_connection(str(path), timeout=5) as db:
        exists=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='fusion_contexts'").fetchone()
        columns={r[1] for r in db.execute('PRAGMA table_info(fusion_contexts)')}
        flag='calibration_verified' if 'calibration_verified' in columns else '0'
        rows=db.execute(f'SELECT item,rune,outcome,before_json,source,{flag} FROM fusion_contexts').fetchall() if exists else []
    groups=defaultdict(Counter); calibration=defaultdict(Counter); rejected=0
    for item,rune,outcome,raw,source,qualified in rows:
        if source!='local_screen' or outcome not in ('SC','SN','EC'):
            rejected+=1;continue
        try:
            before=json.loads(raw)
            pool=before['pool'];jet=before['jet']
            if not isinstance(jet,dict) or not jet or not finite_number(pool,nonnegative=True) or not item or not rune:
                raise ValueError('invalid context')
            key=(item,rune,pool,jet_signature(jet))
            groups[key][outcome]+=1
            if qualified==1:
                calibration[(item,rune,float(pool),jet_signature(jet))][outcome]+=1
        except (TypeError,ValueError,KeyError,OverflowError): rejected+=1
    # Video evidence has a distinct, replaceable provenance. Re-read its current
    # qualified contributions so corrections/rejections cannot leave stale counts.
    from forgely_video_store import qualified_video_rows, item_profile
    video_rows=qualified_video_rows(db_file)
    for video_id,event_id,event in video_rows:
        item,_=item_profile(event['item_id'])
        before=event['before']
        calibration[(item.identity_name,event['rune'],float(before['pool']),jet_signature(before['jet']))][event['outcome']]+=1
    output={}
    for key,counts in groups.items():
        n=sum(counts.values())
        output[key]={'n':n,'counts':dict(counts),
                     'percentages':{o:round(100*counts[o]/n,1) for o in ('SC','SN','EC')} if n>=minimum else None,
                     'ci95_sc':tuple(round(100*x,1) for x in wilson(counts['SC'],n)) if n>=minimum else None,
                     'usable':n>=minimum,
                     'quality':'exploratoire_ocr_non_verifie'}
    return {'groups':output,'calibration':{k:{'counts':dict(v),'verified':True} for k,v in calibration.items()},'observations':sum(map(sum,(c.values() for c in groups.values()))),
            'rejected':rejected,'video_observations':len(video_rows)}


class LiveLaboratory:
    """Background worker, publishes immutable-by-convention snapshots atomically."""
    def __init__(self, db_file=DB_FILE, interval=3.0, minimum=30):
        self.db_file=db_file;self.interval=interval;self.minimum=minimum
        self._stop=threading.Event();self._wake=threading.Event()
        self._lock=threading.Lock();self._snapshot={'groups':{},'observations':0,'rejected':0}
        self.last_error=None;self._thread=None
        self._refresh_lock=threading.Lock()
        self._cursor=0;self._counts=defaultdict(Counter)
        self._experience=OnlineExperience()
        self._requests=0;self._last_request=-1;self._last_database_revision=None;self._revision=0
        self._empirical=None

    @property
    def revision(self):
        with self._lock:return self._revision

    def start(self):
        if self._thread is None or not self._thread.is_alive():
            self._stop.clear();self._thread=threading.Thread(target=self._run,name='Forgely-Laboratoire',daemon=True)
            self._thread.start()

    def notify_observation(self):
        with self._lock:self._requests+=1
        self._wake.set()

    def refresh_if_changed(self):
        signature=database_revision(self.db_file)
        with self._lock:
            request=self._requests
            if signature==self._last_database_revision and request==self._last_request:return False
        self.refresh()
        snapshot=compute_snapshot(self.db_file,minimum=self.minimum)
        from forgely_empirical_model import load_empirical_model
        model=load_empirical_model(self.db_file)
        with self._lock:
            self._snapshot['calibration']=snapshot.get('calibration',{})
            self._snapshot['video_observations']=snapshot.get('video_observations',0)
            self._empirical=model
            self.last_error=None;self._revision+=1
            self._last_database_revision=signature;self._last_request=request
        return True

    def _run(self):
        while not self._stop.is_set():
            self._wake.clear()
            try:
                self.refresh_if_changed()
            except (sqlite3.Error,OSError,ValueError) as exc:
                with self._lock: self.last_error=str(exc)
            self._wake.wait(self.interval)

    def refresh(self):
        """Publish committed new rows immediately; never re-read past attempts."""
        if not Path(self.db_file).exists():return 0
        with self._refresh_lock:
            with database_connection(str(self.db_file),timeout=5) as db:
                columns={row[1] for row in db.execute('PRAGMA table_info(fusion_contexts)')}
                if not columns:return 0
                after_column='after_json' if 'after_json' in columns else 'NULL'
                rows=db.execute(f'SELECT rowid,item,rune,outcome,before_json,{after_column},source '
                    'FROM fusion_contexts WHERE rowid>? ORDER BY rowid',(self._cursor,)).fetchall()
            added=0
            with self._lock:
                touched=set()
                for ident,item,rune,outcome,raw,after_raw,source in rows:
                    self._cursor=ident
                    try:
                        if source!='local_screen' or outcome not in ('SC','SN','EC'):
                            raise ValueError('invalid source')
                        before=json.loads(raw);pool=before['pool'];jet=before['jet']
                        if not finite_number(pool,nonnegative=True) or not item or not rune:
                            raise ValueError('invalid context')
                        key=(item,rune,pool,jet_signature(jet))
                        if after_column!='NULL':
                            after=json.loads(after_raw) if after_raw else None
                            if not self._experience.observe(ident,item,rune,outcome,before,after):
                                raise ValueError('incoherent post state')
                    except (ValueError,TypeError,KeyError,OverflowError):
                        self._snapshot['rejected']+=1
                        continue
                    self._counts[key][outcome]+=1;touched.add(key)
                    self._snapshot['observations']+=1;added+=1
                for key in touched:
                    counts=self._counts[key];n=sum(counts.values())
                    usable=n>=self.minimum
                    self._snapshot['groups'][key]={'n':n,'counts':dict(counts),'usable':usable,
                        'percentages':{o:round(100*counts[o]/n,1) for o in ('SC','SN','EC')} if usable else None,
                        'ci95_sc':tuple(round(100*x,1) for x in wilson(counts['SC'],n)) if usable else None,
                        'quality':'exploratoire_ocr_non_verifie'}
                self.last_error=None
            with self._lock:self._revision+=1
            return added

    def experience(self,item,rune,jet,pool,targets,bounds):
        with self._lock:
            return self._experience.evaluate(item,rune,jet,pool,targets,bounds)

    def estimate(self,item,rune,jet,pool):
        if not item or not rune or not isinstance(jet,dict) or not jet or pool is None: return None
        try:
            if not finite_number(pool,nonnegative=True):return None
            key=(item,rune,pool,jet_signature(jet))
        except (ValueError,TypeError): return None
        with self._lock:
            if self._empirical is not None:
                from forgely_empirical_model import resolve_item
                if resolve_item(item) is not None:
                    return self._empirical.observation(item,rune,jet,pool)
            qualified=self._snapshot.get('calibration',{}).get(key)
            if qualified:
                counts=qualified['counts'];n=sum(counts.values())
                return {'n':n,'counts':deepcopy(counts),'usable':n>=self.minimum,'quality':'local_verified','verified':True}
            return deepcopy(self._snapshot['groups'].get(key))

    def empirical_model(self):
        with self._lock:model=self._empirical
        if model is None:
            from forgely_empirical_model import EmpiricalModel
            return EmpiricalModel()
        return model

    def calibration(self,item,rune,jet,pool):
        if not finite_number(pool,nonnegative=True):return None
        try:key=(item,rune,float(pool),jet_signature(jet))
        except (ValueError,TypeError):return None
        with self._lock:
            if self._empirical is not None:
                from forgely_empirical_model import resolve_item
                if resolve_item(item) is not None:return self._empirical.observation(item,rune,jet,pool)
            return self._snapshot.get('calibration',{}).get(key)

    def status(self):
        with self._lock:
            return {'observations':self._snapshot['observations'],
                    'video_observations':self._snapshot.get('video_observations',0),
                    'rejected':self._snapshot['rejected'], 'groups':len(self._snapshot['groups']),
                    'error':self.last_error}

    def stop(self):
        self._stop.set();self._wake.set()
        if self._thread and self._thread.is_alive():self._thread.join(timeout=2)
