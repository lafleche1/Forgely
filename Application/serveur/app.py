"""API pilote Forgely: standard library, SQLite mono-instance, no screenshots."""
import hashlib, hmac, json, os, sqlite3, threading, time, uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

DB = Path(os.environ.get('FORGELY_DB', '/data/forgely.sqlite3'))
TOKEN = os.environ.get('FORGELY_INGEST_TOKEN', '')
MAX_BODY = 16_384
LOCK = threading.Lock()


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, *exc):
        try:
            return super().__exit__(*exc)
        finally:
            self.close()

def connect():
    DB.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(str(DB), timeout=20, factory=ClosingConnection)
    c.execute('PRAGMA journal_mode=WAL')
    c.execute("""CREATE TABLE IF NOT EXISTS attempts (
        event_id TEXT PRIMARY KEY, received_at TEXT NOT NULL, rune TEXT NOT NULL,
        outcome TEXT NOT NULL CHECK(outcome IN ('SC','SN','EC')),
        item_type TEXT NOT NULL, stat TEXT NOT NULL, rune_weight REAL NOT NULL,
        sink_before REAL NOT NULL, item_level INTEGER NOT NULL,
        verification TEXT NOT NULL CHECK(verification IN ('manual','ocr_confirmed')),
        schema_version INTEGER NOT NULL CHECK(schema_version=1))""")
    c.commit()
    return c

def validate(data):
    if not isinstance(data,dict): raise ValueError('object required')
    required={'schema_version','event_id','rune','outcome','item_type','stat','rune_weight','sink_before','item_level','verification'}
    if set(data)!=required: raise ValueError('invalid fields')
    if type(data['schema_version']) is not int or data['schema_version']!=1: raise ValueError('schema_version must be 1')
    try: uuid.UUID(data['event_id'])
    except (ValueError,TypeError,AttributeError): raise ValueError('event_id must be UUID')
    for field in ('rune','item_type','stat'):
        v=data[field]
        if not isinstance(v,str) or not (1<=len(v)<=80) or any(ord(x)<32 for x in v): raise ValueError('invalid '+field)
    if data['outcome'] not in ('SC','SN','EC'): raise ValueError('invalid outcome')
    if data['verification'] not in ('manual','ocr_confirmed'): raise ValueError('unverified data rejected')
    for field in ('rune_weight','sink_before'):
        v=data[field]
        if type(v) not in (int,float) or not (0<=v<=1000): raise ValueError('invalid '+field)
    if type(data['item_level']) is not int or not (1<=data['item_level']<=300): raise ValueError('invalid item_level')
    return data

class Handler(BaseHTTPRequestHandler):
    def reply(self, status, payload):
        b=json.dumps(payload,ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(b)))
        self.send_header('Cache-Control','no-store')
        self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        parsed=urlsplit(self.path)
        if parsed.path=='/health': return self.reply(200,{'status':'ok'})
        if parsed.path!='/v1/stats': return self.reply(404,{'error':'not found'})
        q=parse_qs(parsed.query)
        if set(q)-{'rune','stat','item_type'}: return self.reply(400,{'error':'unsupported filter'})
        if not q.get('rune') or len(q['rune'])!=1: return self.reply(400,{'error':'rune required'})
        for key in q:
            if len(q[key])!=1 or len(q[key][0])>80: return self.reply(400,{'error':'invalid filter'})
        where=['rune=?']; params=[q['rune'][0]]
        for field in ('stat','item_type'):
            if field in q: where.append(field+'=?'); params.append(q[field][0])
        with connect() as c:
            rows=c.execute('SELECT outcome, COUNT(*) FROM attempts WHERE '+ ' AND '.join(where)+' GROUP BY outcome',params).fetchall()
        counts=dict(rows); n=sum(counts.values())
        return self.reply(200,{'schema_version':1,'filters':{k:v[0] for k,v in q.items()},'n':n,'counts':{x:counts.get(x,0) for x in ('SC','SN','EC')},'note':'observations déclarées, non représentatives sans contrôle qualité; pas de probabilité garantie'})
    def do_POST(self):
        if self.path!='/v1/attempts': return self.reply(404,{'error':'not found'})
        if not TOKEN or not hmac.compare_digest(self.headers.get('Authorization',''), 'Bearer '+TOKEN): return self.reply(401,{'error':'unauthorized'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if not 1<=size<=MAX_BODY: return self.reply(413,{'error':'invalid body size'})
            data=validate(json.loads(self.rfile.read(size)))
        except (ValueError,UnicodeDecodeError,json.JSONDecodeError) as e: return self.reply(400,{'error':str(e)[:120]})
        with LOCK, connect() as c:
            cur=c.execute("""INSERT OR IGNORE INTO attempts
            (event_id,received_at,rune,outcome,item_type,stat,rune_weight,sink_before,item_level,verification,schema_version)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",(data['event_id'],datetime.now(timezone.utc).isoformat(),data['rune'],data['outcome'],data['item_type'],data['stat'],data['rune_weight'],data['sink_before'],data['item_level'],data['verification'],1))
            c.commit()
        return self.reply(201 if cur.rowcount else 200,{'accepted':True,'duplicate':not bool(cur.rowcount),'event_id':data['event_id']})

def main():
    if not TOKEN or len(TOKEN)<32: raise SystemExit('Set FORGELY_INGEST_TOKEN (32+ characters)')
    connect().close()
    host=os.environ.get('FORGELY_BIND','127.0.0.1')
    port=int(os.environ.get('FORGELY_PORT','8080'))
    ThreadingHTTPServer((host,port),Handler).serve_forever()
if __name__=='__main__': main()
