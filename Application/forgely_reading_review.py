"""Local human-labelled visual references. Never write FM outcomes or live jets.

OCR suggestions are metadata only. Native binary shapes require two distinct
human-confirmed examples before use; contradictory labels quarantine a shape.
"""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sqlite3
import cv2
import numpy as np
from forgely_cv.numbers import number_mask, parse_number, NumericField, NumericReader, NumericReading
from forgely_cv.geometry import Rect
from forgely_cv.glyphs import GlyphReader, segment_glyphs


def png(image):
    ok, data = cv2.imencode('.png', image)
    if not ok:
        raise ValueError('Image impossible à enregistrer')
    return data.tobytes()


def decode(data, gray=False):
    image = cv2.imdecode(np.frombuffer(data,np.uint8), cv2.IMREAD_GRAYSCALE if gray else cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError('Image de référence illisible')
    return image


class ReviewStore:
    def __init__(self, path, limit=100):
        self.path, self.limit = Path(path), limit
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connection() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS examples (
                  id TEXT PRIMARY KEY, scale TEXT NOT NULL, image BLOB NOT NULL,
                  kind TEXT NOT NULL, suggestion TEXT, context TEXT,
                  state TEXT NOT NULL DEFAULT 'pending', number TEXT, label TEXT,
                  number_box TEXT, label_box TEXT, created TEXT DEFAULT CURRENT_TIMESTAMP);
                CREATE TABLE IF NOT EXISTS votes (
                  example TEXT NOT NULL, position INTEGER NOT NULL, shape TEXT NOT NULL,
                  char TEXT NOT NULL, pixels BLOB NOT NULL,
                  PRIMARY KEY(example,position));
                CREATE TABLE IF NOT EXISTS metadata (id INTEGER PRIMARY KEY, revision INTEGER);
                INSERT OR IGNORE INTO metadata VALUES (1,0);
            ''')
            if 'origin' not in {r[1] for r in db.execute('PRAGMA table_info(examples)')}:
                db.execute("ALTER TABLE examples ADD COLUMN origin TEXT NOT NULL DEFAULT 'human'")

    @contextmanager
    def connection(self):
        db=sqlite3.connect(self.path,timeout=3)
        db.row_factory=sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def revision(self):
        with self.connection() as db:
            return db.execute('SELECT revision FROM metadata WHERE id=1').fetchone()[0]

    def offer(self, image, *, scale, suggestion='', context='', kind='stat'):
        if kind not in ('stat','pool') or not scale or image.ndim!=3 or image.shape[2]!=3:
            raise ValueError('Exemple visuel invalide')
        if image.dtype!=np.uint8 or not image.size or image.shape[0]>180 or image.shape[1]>1200:
            raise ValueError('La file conserve uniquement des petites zones ciblées')
        mask=number_mask(image)
        if cv2.countNonZero(mask)<3:
            return None
        key=hashlib.sha256((scale+str(mask.shape)+kind).encode()+mask.tobytes()).hexdigest()
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            previous=db.execute('SELECT state,suggestion FROM examples WHERE id=?',(key,)).fetchone()
            if previous:
                if (previous['state'] in ('pending','needs_review','auto_pending') and
                        suggestion and suggestion[:500]!=(previous['suggestion'] or '')):
                    db.execute("UPDATE examples SET suggestion=?,state='pending' WHERE id=?",(suggestion[:500],key))
                return key
            if (db.execute("SELECT count(*) FROM examples WHERE state IN ('pending','needs_review','auto_pending')").fetchone()[0]>=self.limit
                or db.execute('SELECT count(*) FROM examples').fetchone()[0]>=5000):
                return None
            db.execute('INSERT INTO examples(id,scale,image,kind,suggestion,context) VALUES (?,?,?,?,?,?)',
                       (key,scale,png(image),kind,suggestion[:500],str(context)[:500]))
        return key

    def pending(self):
        with self.connection() as db:
            return [dict(r) for r in db.execute("SELECT id,kind,suggestion,context,state FROM examples WHERE state IN ('pending','needs_review') ORDER BY created,id")]

    def automatic_pending(self):
        with self.connection() as db:
            return [dict(r) for r in db.execute("SELECT id,kind,scale,suggestion FROM examples WHERE state='auto_pending' ORDER BY created,id")]

    def defer_automatic(self,ident):
        with self.connection() as db:
            db.execute("UPDATE examples SET state='auto_pending' WHERE id=? AND state='pending'",(ident,))

    def confirmed(self):
        with self.connection() as db:
            return [dict(r) for r in db.execute("SELECT id,label,number,scale,state FROM examples WHERE state='confirmed' ORDER BY created DESC")]

    def get(self, ident):
        with self.connection() as db:
            row=db.execute('SELECT * FROM examples WHERE id=?',(ident,)).fetchone()
        if row is None:
            raise ValueError('Exemple introuvable')
        return dict(row)

    def reject(self, ident):
        self._state(ident,'rejected')

    def disable(self, ident):
        self._state(ident,'disabled')

    def retire(self, ident):
        """Retire an unusable machine candidate without calling it user-rejected."""
        with self.connection() as db:
            changed=db.execute("UPDATE examples SET state='superseded' WHERE id=? AND state IN ('pending','needs_review','auto_pending')",(ident,)).rowcount
            if changed:db.execute('UPDATE metadata SET revision=revision+1 WHERE id=1')

    def _state(self, ident, state):
        with self.connection() as db:
            db.execute('UPDATE examples SET state=? WHERE id=?',(state,ident))
            db.execute('UPDATE metadata SET revision=revision+1 WHERE id=1')

    def confirm(self, ident, number, label, number_box, label_box, *, origin='human'):
        row=self.get(ident)
        if origin not in ('human','automatic_numeric_agreement'):
            raise ValueError('Origine de validation inconnue')
        if row['state'] not in ('pending','needs_review','auto_pending'):
            raise ValueError('Cet exemple a déjà été traité')
        from forgely_jet import STATS
        from forgely_dofocus import canonical_stat
        value=parse_number(number,row['kind'])
        if value is None or row['kind']=='stat' and label not in STATS:
            raise ValueError('Valeur ou caractéristique invalide')
        label=canonical_stat(label) if row['kind']=='stat' else 'Puits'
        image=decode(row['image'])
        a,b=Rect(*number_box),Rect(*label_box)
        if not (a.x+a.w<=b.x or b.x+b.w<=a.x or a.y+a.h<=b.y or b.y+b.h<=a.y):
            raise ValueError('Les deux zones doivent être distinctes')
        mask=number_mask(a.crop(image)); guard=number_mask(b.crop(image))
        parts=segment_glyphs(mask)
        if (len(parts)!=len(number) or len({p.line for p in parts})!=1 or
            cv2.countNonZero(guard)<3 or any(q.box.x-p.box.x-p.box.w>3 for p,q in zip(parts,parts[1:]))):
            raise ValueError('Découpage ambigu : encadre seulement le nombre complet, signes compris')
        templates={}
        for char,part in zip(number,parts):
            templates.setdefault(char,[]).append(part.pixels)
        test=GlyphReader(templates,max_error=0)
        if ''.join(test.recognize(p.pixels).text for p in parts)!=number:
            raise ValueError('Deux caractères différents ont la même forme : référence ambiguë')
        field=NumericField(label,row['kind'],a,b,guard,guard_error=0)
        reconstructed=NumericReader(test,[field]).read_visible(image)
        obtained=reconstructed.pool if row['kind']=='pool' else reconstructed.jet.get(label)
        if obtained!=value:
            raise ValueError('La relecture complète ne retrouve pas cette valeur : vérifie les deux zones et les caractères voisins')
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            current=db.execute('SELECT state FROM examples WHERE id=?',(ident,)).fetchone()
            if not current or current[0] not in ('pending','needs_review','auto_pending'):
                raise ValueError('Cet exemple a déjà été traité')
            for index,(char,part) in enumerate(zip(number,parts)):
                shape=hashlib.sha256(row['scale'].encode()+str(part.pixels.shape).encode()+part.pixels.tobytes()).hexdigest()
                db.execute('INSERT INTO votes VALUES (?,?,?,?,?)',(ident,index,shape,char,png(part.pixels)))
            db.execute("UPDATE examples SET state='confirmed',number=?,label=?,number_box=?,label_box=?,origin=? WHERE id=?",
                       (number,label,json.dumps(number_box),json.dumps(label_box),origin,ident))
            db.execute('UPDATE metadata SET revision=revision+1 WHERE id=1')

    def reader(self, scale):
        with self.connection() as db:
            rows=list(db.execute("SELECT * FROM examples WHERE scale=? AND state='confirmed'",(scale,)))
            votes=list(db.execute('''SELECT v.* FROM votes v JOIN examples e ON e.id=v.example
                                    WHERE e.scale=? AND e.state='confirmed' ''',(scale,)))
        shapes={}
        for vote in votes:
            shapes.setdefault(vote['shape'],[]).append(vote)
        templates={}
        active=set()
        for shape,group in shapes.items():
            if len({v['char'] for v in group})==1 and len({v['example'] for v in group})>=2:
                templates.setdefault(group[0]['char'],[]).append(decode(group[0]['pixels'],True))
                active.add(shape)
        if not templates:
            return None
        glyphs=GlyphReader(templates,max_error=0)
        readers=[];seen=set();guards={};prepared={};guard_sources={}
        for row in rows:
            image=decode(row['image']);a,b=Rect(*json.loads(row['number_box'])),Rect(*json.loads(row['label_box']))
            guard=number_mask(b.crop(image))
            key=(row['kind'],guard.shape,guard.tobytes())
            guards.setdefault(key,set()).add(row['label'])
            guard_sources.setdefault(key,set()).add(row['id'])
            prepared[row['id']]=(a,b,guard,key)
        for row in rows:
            own=[v for v in votes if v['example']==row['id']]
            if not own or not all(v['shape'] in active for v in own):
                continue
            a,b,guard,guard_key=prepared[row['id']]
            if len(guards[guard_key])!=1:
                continue
            if row['origin']=='automatic_numeric_agreement' and len(guard_sources[guard_key])<2:
                continue
            key=(row['label'],row['kind'],guard.shape,guard.tobytes(),a.x-b.x,a.y-b.y,a.w,a.h)
            if key in seen:
                continue
            seen.add(key)
            readers.append(NumericReader(glyphs,[NumericField(row['label'],row['kind'],a,b,guard,guard_error=0)]))
        return ReviewReader(readers) if readers else None


class ReviewReader:
    def __init__(self, readers):
        self.readers=readers

    def read_visible(self, image):
        choices={}; details={};pool_values=set()
        for reader in self.readers:
            result=reader.read_visible(image)
            for name,value in result.jet.items():
                choices.setdefault(name,set()).add(value)
            if result.pool is not None:
                pool_values.add(result.pool)
            for name,detail in result.fields.items():
                if detail.get('accepted') or name not in details:
                    details[name]=detail
        jet={k:next(iter(v)) for k,v in choices.items() if len(v)==1}
        pool=next(iter(pool_values)) if len(pool_values)==1 else None
        # This is a set of supported fields, never proof that the item's jet is complete.
        return NumericReading(jet,pool,details,False)
