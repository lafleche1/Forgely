"""Laboratoire FM local en arrière-plan, sans capture supplémentaire.

Lit uniquement les transitions déjà enregistrées. Les OCR automatiques restent
non vérifiés : statistiques exploratoires, jamais probabilités garanties.
"""
from __future__ import annotations
import json, sqlite3, threading
from collections import Counter, defaultdict
from pathlib import Path
from forgely_data import DB_FILE
from forgely_probabilites import wilson
from forgely_rules import finite_number


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
    with sqlite3.connect(str(path), timeout=5) as db:
        exists=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='fusion_contexts'").fetchone()
        if not exists: return {'groups':{}, 'observations':0, 'rejected':0}
        rows=db.execute('SELECT item,rune,outcome,before_json,source FROM fusion_contexts').fetchall()
    groups=defaultdict(Counter); rejected=0
    for item,rune,outcome,raw,source in rows:
        if source!='local_screen' or outcome not in ('SC','SN','EC'):
            rejected+=1;continue
        try:
            before=json.loads(raw)
            pool=before['pool'];jet=before['jet']
            if not isinstance(jet,dict) or not jet or not finite_number(pool,nonnegative=True) or not item or not rune:
                raise ValueError('invalid context')
            key=(item,rune,pool_bucket(pool),jet_signature(jet))
            groups[key][outcome]+=1
        except (TypeError,ValueError,KeyError,OverflowError): rejected+=1
    output={}
    for key,counts in groups.items():
        n=sum(counts.values())
        output[key]={'n':n,'counts':dict(counts),
                     'percentages':{o:round(100*counts[o]/n,1) for o in ('SC','SN','EC')} if n>=minimum else None,
                     'ci95_sc':tuple(round(100*x,1) for x in wilson(counts['SC'],n)) if n>=minimum else None,
                     'usable':n>=minimum,
                     'quality':'exploratoire_ocr_non_verifie'}
    return {'groups':output,'observations':sum(map(sum,(c.values() for c in groups.values()))),
            'rejected':rejected}


class LiveLaboratory:
    """Background worker, publishes immutable-by-convention snapshots atomically."""
    def __init__(self, db_file=DB_FILE, interval=3.0, minimum=30):
        self.db_file=db_file;self.interval=interval;self.minimum=minimum
        self._stop=threading.Event();self._wake=threading.Event()
        self._lock=threading.Lock();self._snapshot={'groups':{},'observations':0,'rejected':0}
        self.last_error=None;self._thread=None

    def start(self):
        if self._thread is None or not self._thread.is_alive():
            self._stop.clear();self._thread=threading.Thread(target=self._run,name='Forgely-Laboratoire',daemon=True)
            self._thread.start()

    def notify_observation(self):
        self._wake.set()

    def _run(self):
        while not self._stop.is_set():
            try:
                snapshot=compute_snapshot(self.db_file,minimum=self.minimum)
                with self._lock:
                    self._snapshot=snapshot;self.last_error=None
            except (sqlite3.Error,OSError,ValueError) as exc:
                with self._lock: self.last_error=str(exc)
            self._wake.wait(self.interval);self._wake.clear()

    def estimate(self,item,rune,jet,pool):
        if not item or not rune or not isinstance(jet,dict) or not jet or pool is None: return None
        try:
            if not finite_number(pool,nonnegative=True):return None
            key=(item,rune,pool_bucket(float(pool)),jet_signature(jet))
        except (ValueError,TypeError): return None
        with self._lock: return self._snapshot['groups'].get(key)

    def status(self):
        with self._lock:
            return {'observations':self._snapshot['observations'],
                    'rejected':self._snapshot['rejected'], 'groups':len(self._snapshot['groups']),
                    'error':self.last_error}

    def stop(self):
        self._stop.set();self._wake.set()
        if self._thread and self._thread.is_alive():self._thread.join(timeout=2)

