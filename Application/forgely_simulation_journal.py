"""Persistent virtual statistics, explicitly distinct from game observations."""
from hashlib import sha256
import json
from pathlib import Path
from forgely_sqlite import database_connection
from forgely_advice_history import measurements_only


class SimulationJournal:
    def __init__(self,path):self.path=Path(path)

    def record(self,key,results):
        if not results:return False
        if len(key)<2 or type(key[1]) is not int or key[1]<=0:raise ValueError('Objet invalide')
        counts={o:0 for o in ('SC','SN','EC')};total=0
        for result in results.values():
            if (result.get('kind')!='virtual_trials' or result.get('real_observations')!=0
                    or type(result.get('trials')) is not int or not 16<=result['trials']<=256):
                raise ValueError('Statistiques virtuelles invalides')
            values=[result.get('counts',{}).get(o,0) for o in counts]
            if any(type(v) is not int or v<0 for v in values) or sum(values)!=result['trials']:
                raise ValueError('Comptages invalides')
            for outcome,value in zip(counts,values):counts[outcome]+=value
            total+=result['trials']
        raw=json.dumps(key,ensure_ascii=False,allow_nan=False,separators=(',',':'))
        digest=sha256(raw.encode('utf-8')).hexdigest()
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with database_connection(str(self.path),timeout=2) as db:
            db.execute('CREATE TABLE IF NOT EXISTS virtual_runs('
                'state_hash TEXT PRIMARY KEY,item_id INTEGER NOT NULL,state_json TEXT NOT NULL,'
                'results_json TEXT NOT NULL,trials INTEGER NOT NULL,sc INTEGER NOT NULL,'
                'sn INTEGER NOT NULL,ec INTEGER NOT NULL,source TEXT NOT NULL CHECK(source="simulation"))')
            db.execute('CREATE INDEX IF NOT EXISTS virtual_item ON virtual_runs(item_id)')
            cursor=db.execute('INSERT OR IGNORE INTO virtual_runs VALUES(?,?,?,?,?,?,?,?,?)',
                 (digest,key[1],raw,json.dumps(measurements_only(results),ensure_ascii=False,allow_nan=False),total,
                 counts['SC'],counts['SN'],counts['EC'],'simulation'))
            return cursor.rowcount==1

    def totals(self,item_id=None):
        empty={'virtual':0,'SC':0,'SN':0,'EC':0}
        if not self.path.exists():return empty
        with database_connection(str(self.path),timeout=2) as db:
            if not db.execute("SELECT 1 FROM sqlite_master WHERE name='virtual_runs'").fetchone():return empty
            clause=' WHERE item_id=?' if item_id is not None else ''
            args=(item_id,) if item_id is not None else ()
            values=db.execute('SELECT coalesce(sum(trials),0),coalesce(sum(sc),0),'
                'coalesce(sum(sn),0),coalesce(sum(ec),0) FROM virtual_runs'+clause,args).fetchone()
        return dict(zip(empty,values))

    def totals_by_item(self):
        """Background-only snapshot for non-blocking UI counters."""
        if not self.path.exists():return {}
        with database_connection(str(self.path),timeout=2) as db:
            if not db.execute("SELECT 1 FROM sqlite_master WHERE name='virtual_runs'").fetchone():return {}
            return dict(db.execute('SELECT item_id,sum(trials) FROM virtual_runs GROUP BY item_id').fetchall())
