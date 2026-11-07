"""Read-only, indexed simulation reference. Never opens the player observation DB."""
from __future__ import annotations
from contextlib import closing
from copy import deepcopy
from datetime import date
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import json
import os
import sqlite3
import tempfile
from forgely_dofocus import (key, canonical_stat, normalise_jet, finite_number,
                             validate_catalogue, SOURCE_URL, FAMILIES)

STORE_VERSION=1


def state_key(jets,pool):
    jets=normalise_jet(jets)
    if jets is None or not finite_number(pool) or pool<0:return None
    def ratio(value):
        return [value,1] if isinstance(value,int) else list(value.as_integer_ratio())
    # Exact rational encoding retains Python's numeric equality (1 == 1.0),
    # including signed zero, without rounding two different jets together.
    return json.dumps([[[stat,ratio(v)] for stat,v in sorted(jets.items())],ratio(pool)],
                      ensure_ascii=False,separators=(',',':'))


def build_database(source,destination):
    """Validate first; replace destination only after a complete successful build."""
    raw=Path(source).read_bytes()
    data=validate_catalogue(json.loads(raw))
    metadata={k:v for k,v in data.items() if k!='snapshots'}
    metadata['source_sha256']=sha256(raw).hexdigest()
    items={}
    for sample in data['snapshots']:
        name=key(sample['item'])
        profile={canonical_stat(r['stat']):r['max'] for r in sample['rows'] if r['max'] is not None}
        limits={}
        for row in sample['rows']:
            caps=[r['line_max'] for r in row['runes'].values() if r['blocked']]
            if caps:limits[canonical_stat(row['stat'])]=min(caps)
        identity=(sample['item_id'],sample['item'],sample['url'],profile)
        if name in items:
            previous=items[name]
            if tuple(previous[:4])!=identity:raise ValueError('Profils contradictoires pour un objet')
            for stat,cap in limits.items():previous[4][stat]=min(cap,previous[4].get(stat,cap))
        else:items[name]=[*identity,limits]
    destination=Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    fd,temporary=tempfile.mkstemp(prefix=destination.name+'.',suffix='.tmp',dir=destination.parent)
    os.close(fd)
    try:
        with closing(sqlite3.connect(temporary)) as conn:
            conn.executescript('''
                PRAGMA page_size=4096;
                PRAGMA user_version=1;
                CREATE TABLE metadata(payload TEXT NOT NULL);
                CREATE TABLE items(item_key TEXT PRIMARY KEY, item_id INTEGER NOT NULL,
                    name TEXT NOT NULL,url TEXT NOT NULL,profile TEXT NOT NULL,limits TEXT NOT NULL) WITHOUT ROWID;
                CREATE TABLE contexts(item_key TEXT NOT NULL,state_key TEXT NOT NULL,payload TEXT NOT NULL,
                    PRIMARY KEY(item_key,state_key)) WITHOUT ROWID;
            ''')
            dump=lambda obj:json.dumps(obj,ensure_ascii=False,separators=(',',':'))
            conn.execute('INSERT INTO metadata VALUES(?)',(dump(metadata),))
            for name,(ident,label,url,profile,limits) in sorted(items.items()):
                conn.execute('INSERT INTO items VALUES(?,?,?,?,?,?)',(name,ident,label,url,dump(profile),dump(limits)))
            for sample in data['snapshots']:
                jet={r['stat']:r['value'] for r in sample['rows']}
                conn.execute('INSERT INTO contexts VALUES(?,?,?)',
                             (key(sample['item']),state_key(jet,sample['pool']),dump(sample)))
            conn.commit()
            if conn.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('Base de référence invalide')
        os.replace(temporary,destination)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return {'items':len(items),'contexts':len(data['snapshots']),'bytes':destination.stat().st_size,
            'source_sha256':metadata['source_sha256']}


class ReferenceStore:
    def __init__(self,path):
        self.path=Path(path)
        self._metadata=lru_cache(maxsize=1)(self._read_metadata)
        self._items=lru_cache(maxsize=32)(self._read_item)
        self._contexts=lru_cache(maxsize=64)(self._read_context)

    def _connect(self):
        conn=sqlite3.connect(self.path.resolve().as_uri()+'?mode=ro',uri=True,timeout=.1)
        conn.execute('PRAGMA query_only=ON')
        return conn

    def _read_metadata(self):
        try:
            with closing(self._connect()) as conn:
                if conn.execute('PRAGMA user_version').fetchone()[0]!=STORE_VERSION:return None
                data=json.loads(conn.execute('SELECT payload FROM metadata LIMIT 1').fetchone()[0])
            if (not isinstance(data,dict) or data.get('schema')!=1 or data.get('source')!='Dofocus'
                    or data.get('kind')!='simulation_reference' or type(data.get('real_attempts')) is not int
                    or data['real_attempts']!=0 or date.fromisoformat(data['captured_on']).isoformat()!=data['captured_on']):
                return None
            return data
        except (OSError,sqlite3.Error,ValueError,TypeError,KeyError,IndexError):return None

    def _read_item(self,name):
        if self._metadata() is None:return None
        try:
            with closing(self._connect()) as conn:
                row=conn.execute('SELECT item_id,name,url,profile,limits FROM items WHERE item_key=?',(name,)).fetchone()
            if row is None:return None
            ident,label,url,profile,limits=row
            profile=json.loads(profile);limits=json.loads(limits)
            clean=normalise_jet(profile)
            if (type(ident) is not int or ident<=0 or key(label)!=name or url!=SOURCE_URL+str(ident)
                    or clean is None or any(s not in FAMILIES for s in clean)
                    or not isinstance(limits,dict) or any(canonical_stat(s) not in FAMILIES
                        or not finite_number(v) for s,v in limits.items())):return None
            return {'item_id':ident,'item':label,'url':url,'profile':clean,
                    'limits':{canonical_stat(s):v for s,v in limits.items()}}
        except (OSError,sqlite3.Error,ValueError,TypeError,KeyError,IndexError):return None

    def _read_context(self,name,signature):
        metadata=self._metadata();item=self._items(name)
        if metadata is None or item is None:return None
        try:
            with closing(self._connect()) as conn:
                row=conn.execute('SELECT payload FROM contexts WHERE item_key=? AND state_key=?',(name,signature)).fetchone()
            if row is None:return None
            sample=json.loads(row[0])
            validate_catalogue({**metadata,'snapshots':[sample]})
            jets={r['stat']:r['value'] for r in sample['rows']}
            if (key(sample['item'])!=name or sample['item_id']!=item['item_id']
                    or state_key(jets,sample['pool'])!=signature):return None
            result={}
            for row in sample['rows']:
                for rune,values in row['runes'].items():
                    result[rune]={**values,'kind':'simulation_reference','source':'Dofocus',
                                  'url':sample['url'],'captured_on':metadata['captured_on'],
                                  'real_observation':False,'stat':canonical_stat(row['stat'])}
            return result
        except (OSError,sqlite3.Error,ValueError,TypeError,KeyError,IndexError):return None

    def context(self,item,jets,pool):
        signature=state_key(jets,pool)
        if signature is None:return None
        return deepcopy(self._contexts(key(item),signature))

    def rune(self,item,jets,pool,rune):
        signature=state_key(jets,pool)
        if signature is None:return None
        context=self._contexts(key(item),signature)
        return deepcopy(context.get(rune)) if context else None

    def profile(self,item):
        row=self._items(key(item))
        return dict(row['profile']) if row else None

    def limit(self,item,stat):
        row=self._items(key(item))
        return row['limits'].get(canonical_stat(stat)) if row else None

    def cache_info(self):
        return {'items':self._items.cache_info(),'contexts':self._contexts.cache_info()}
