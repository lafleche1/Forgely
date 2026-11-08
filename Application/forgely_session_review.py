"""Local session reports and prospective forecast scoring; never synthetic learning.

Evaluation tables share the observation database, but never add observations or
alter its outcomes. A full coherent transition is required to score a forecast.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
import uuid
import zipfile
from forgely_data import connect, DB_FILE, DATA_DIR
from forgely_tools import observation_cursor
from forgely_dofocus import normalise_jet
from forgely_rules import finite_number, known_prices
from forgely_expert import audit_transition


def stamp():return datetime.now(timezone.utc).isoformat()
def dump(value):return json.dumps(value,ensure_ascii=False,sort_keys=True)


class SessionRecorder:
    def __init__(self,db_file=DB_FILE,report_dir=None):
        self.db_file=Path(db_file)
        self.report_dir=Path(report_dir) if report_dir else self.db_file.parent/'bilans_sessions'
        self.active=None;self.last_report=None;self.last_forecast_key=None
        observation_cursor(self.db_file)
        with self._db() as db:
            db.executescript('''CREATE TABLE IF NOT EXISTS evaluation_sessions (
                id TEXT PRIMARY KEY, meta TEXT NOT NULL, start_cursor TEXT NOT NULL,
                closed INTEGER NOT NULL DEFAULT 0, report TEXT);
                CREATE TABLE IF NOT EXISTS evaluation_forecasts (
                id INTEGER PRIMARY KEY, session TEXT NOT NULL, rune TEXT NOT NULL,
                prediction TEXT NOT NULL,state TEXT NOT NULL,frame INTEGER NOT NULL,
                scope TEXT NOT NULL,used INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS evaluation_trials (
                observation_id INTEGER PRIMARY KEY,session TEXT NOT NULL,forecast_id INTEGER,
                matched INTEGER NOT NULL DEFAULT 0,qualified INTEGER NOT NULL DEFAULT 0,
                reason TEXT NOT NULL DEFAULT 'transition_absente',before_state TEXT,after_state TEXT,event_frame INTEGER,in_scope INTEGER NOT NULL DEFAULT 1);''')
            columns={r[1] for r in db.execute('PRAGMA table_info(evaluation_trials)')}
            for name,kind in (('before_state','TEXT'),('after_state','TEXT'),('event_frame','INTEGER'),('in_scope','INTEGER NOT NULL DEFAULT 1')):
                if name not in columns:db.execute(f'ALTER TABLE evaluation_trials ADD COLUMN {name} {kind}')

    @contextmanager
    def _db(self):
        db=connect(self.db_file)
        try:
            with db:yield db
        finally:db.close()

    def ensure_session(self,*,item,targets,jets,pool,prices,scope,level=None,mode=None):
        targets,jets=normalise_jet(targets),normalise_jet(jets)
        if (not isinstance(item,str) or not item.strip() or not targets or not jets
                or not set(targets).issubset(jets) or not finite_number(pool,nonnegative=True)
                or not isinstance(scope,str) or not scope):
            raise ValueError('Objet, objectifs et état confirmés requis pour le bilan')
        identity=(item,targets,level,scope)
        if self.active and self.active['identity']!=identity:
            self.finish(jets=None,pool=None,confirmed=False,reason='objet_objectif_ou_capture_modifié')
        if self.active is None:
            sid=uuid.uuid4().hex
            meta={'item':item,'targets':targets,'level':level,'started_at':stamp(),
                  'prices':known_prices(prices),'mode':mode,'start':{'jet':jets,'pool':pool}}
            cursor=observation_cursor(self.db_file)
            with self._db() as db:db.execute('INSERT INTO evaluation_sessions(id,meta,start_cursor) VALUES(?,?,?)',
                                            (sid,dump(meta),dump(cursor)))
            self.active={'id':sid,'identity':identity,'meta':meta,'cursor':cursor}
            self.last_forecast_key=None
        self.active['snapshot']={'jet':dict(jets),'pool':pool}
        return self.active['id']

    def forecast(self,rune,prediction,*,frame,scope):
        if not self.active or scope!=self.active['identity'][3] or type(frame) is not int or frame<0:return
        if not isinstance(prediction,dict) or not rune:return
        rates=[prediction.get(k) for k in ('SC','SN','EC')]
        if any(not finite_number(v,nonnegative=True) or v>100 for v in rates) or abs(sum(rates)-100)>1e-6:return
        state=self.active['snapshot']
        key=dump([rune,prediction,state,scope])
        if key==self.last_forecast_key:return
        with self._db() as db:
            db.execute('INSERT INTO evaluation_forecasts(session,rune,prediction,state,frame,scope) VALUES(?,?,?,?,?,?)',
                       (self.active['id'],rune,dump(prediction),dump(state),frame,scope))
        self.last_forecast_key=key

    def event(self,observation_id,item,rune,outcome,*,frame,scope):
        if not self.active or item!=self.active['meta']['item'] or type(observation_id) is not int:return
        with self._db() as db:
            obs=db.execute('SELECT item,rune,outcome FROM observations WHERE id=?',(observation_id,)).fetchone()
            if obs!=(item,rune,outcome):return
            if db.execute('SELECT 1 FROM evaluation_trials WHERE observation_id=?',(observation_id,)).fetchone():return
            if scope!=self.active['identity'][3]:
                db.execute('INSERT INTO evaluation_trials(observation_id,session,in_scope,reason,event_frame) VALUES(?,?,0,?,?)',
                           (observation_id,self.active['id'],'capture_étrangère',frame if type(frame) is int else None))
                return
            row=db.execute('SELECT id,rune,frame,scope FROM evaluation_forecasts WHERE session=? AND used=0 ORDER BY id DESC LIMIT 1',
                           (self.active['id'],)).fetchone()
            matched=bool(row and row[1]==rune and type(frame) is int and row[2]<frame and row[3]==scope)
            db.execute('INSERT INTO evaluation_trials(observation_id,session,forecast_id,matched,reason,event_frame) VALUES(?,?,?,?,?,?)',
                       (observation_id,self.active['id'],row[0] if row else None,int(matched),
                        'transition_en_attente' if matched else 'prévision_absente_ou_non_comparable',frame if type(frame) is int else None))
            if row and type(frame) is int and row[2]<frame:
                db.execute('UPDATE evaluation_forecasts SET used=1 WHERE id=?',(row[0],))
        self.last_forecast_key=None

    def transition(self,observation_id,before,after,*,qualified):
        if type(observation_id) is not int:return
        with self._db() as db:
            row=db.execute('''SELECT t.forecast_id,t.matched,f.state,o.rune,o.outcome
                FROM evaluation_trials t JOIN observations o ON o.id=t.observation_id
                LEFT JOIN evaluation_forecasts f ON f.id=t.forecast_id WHERE t.observation_id=?''',(observation_id,)).fetchone()
            if row is None:return
            audit=audit_transition(row[3],row[4],before,after,complete=qualified is True)
            coherent=qualified is True and audit['status']=='cohérent'
            comparable=bool(row[1] and coherent and row[2] and json.loads(row[2])==before)
            reason='comparable' if comparable else ('contexte_non_comparable' if coherent else 'lecture_partielle_ou_contradictoire')
            db.execute('UPDATE evaluation_trials SET matched=?,qualified=?,reason=?,before_state=?,after_state=? WHERE observation_id=?',
                       (int(comparable),int(coherent),reason,dump(before),dump(after),observation_id))

    def finish(self,*,jets,pool,confirmed,reason='terminée_par_utilisateur'):
        if not self.active:
            if self.last_report:return self.last_report
            raise ValueError('Aucune session évaluée : confirme un objet et un objectif avant de commencer')
        current=self.active;meta=current['meta'];cursor=current['cursor']
        final=normalise_jet(jets)
        confirmed=bool(confirmed and final and set(meta['targets']).issubset(final)
                       and finite_number(pool,nonnegative=True))
        with self._db() as db:
            # Consistent closing snapshot; do not include other items or older trials.
            db.execute('BEGIN')
            end={table:db.execute(f'SELECT COALESCE(MAX(id),0) FROM {table}').fetchone()[0]
                 for table in ('observations','unassigned_actions')}
            rows=db.execute('SELECT id,rune,outcome,source,captured_at FROM observations WHERE id>? AND id<=? AND item=? AND id NOT IN (SELECT observation_id FROM evaluation_trials WHERE session=? AND in_scope=0)',
                            (cursor['observations'],end['observations'],meta['item'],current['id'])).fetchall()
            ignored=db.execute('SELECT count(*) FROM evaluation_trials WHERE session=? AND in_scope=0',(current['id'],)).fetchone()[0]
            unassigned=db.execute('SELECT count(*) FROM unassigned_actions WHERE id>? AND id<=?',
                                  (cursor['unassigned_actions'],end['unassigned_actions'])).fetchone()[0]
            trials=db.execute('''SELECT o.outcome,t.matched,t.qualified,t.reason,f.prediction,o.id,o.rune,t.before_state,t.after_state,f.state,f.frame,t.event_frame
                FROM evaluation_trials t JOIN observations o ON o.id=t.observation_id
                LEFT JOIN evaluation_forecasts f ON f.id=t.forecast_id WHERE t.session=? AND t.in_scope=1 AND o.id>? AND o.id<=?''',
                (current['id'],cursor['observations'],end['observations'])).fetchall()
        runes={};counts={'SC':0,'SN':0,'EC':0};sources={};known=0.;unpriced=0
        for obs_id,rune,outcome,source,captured_at in rows:
            runes[rune]=runes.get(rune,0)+1;counts[outcome]+=1;sources[source]=sources.get(source,0)+1
            if rune in meta['prices']:known+=meta['prices'][rune]
            else:unpriced+=1
        scores=[];expected={k:0. for k in counts};observed={k:0 for k in counts};diagnostics={}
        prediction_log=[]
        for outcome,matched,qualified,detail,prediction,obs_id,rune,before,after,forecast_state,frame,event_frame in trials:
            prediction_log.append({'observation_id':obs_id,'rune':rune,'outcome':outcome,
                'comparable':bool(matched and qualified),'qualified':bool(qualified),'diagnostic':detail,
                'forecast':json.loads(prediction) if prediction else None,
                'forecast_state':json.loads(forecast_state) if forecast_state else None,'forecast_frame':frame,'event_frame':event_frame,
                'before':json.loads(before) if before else None,'after':json.loads(after) if after else None})
            diagnostics[detail]=diagnostics.get(detail,0)+1
            if not matched or not qualified or not prediction:continue
            prediction=json.loads(prediction)
            probabilities={k:prediction[k]/100 for k in counts}
            scores.append(sum((probabilities[k]-(k==outcome))**2 for k in counts))
            for k in counts:expected[k]+=probabilities[k]
            observed[outcome]+=1
        n=len(scores)
        status=('atteint' if all(final[s]>=v for s,v in meta['targets'].items()) else 'non_atteint') if confirmed else 'inconnu'
        result={'schema':1,'session_id':current['id'],'item':meta['item'],'started_at':meta['started_at'],
                'finished_at':stamp(),'reason':reason,'level':meta['level'],'mode':meta.get('mode'),'start':meta['start'],
                'goal':{'targets':meta['targets'],'status':status,'final':{'jet':final,'pool':pool} if confirmed else None},
                'attempt_log':[{'id':r[0],'rune':r[1],'outcome':r[2],'source':r[3],'captured_at':r[4]} for r in rows],
                'prediction_log':prediction_log,'attempts':len(rows),'runes':runes,'outcomes':counts,'sources':sources,
                'ignored_scope_attempts':ignored,'known_cost':known,'unpriced_attempts':unpriced,'unassigned_actions':unassigned,
                'cost_complete':unpriced==0 and unassigned==0,'prices_at_start':meta['prices'],
                'prediction_evaluation':{'n':n,'brier':sum(scores)/n if n else None,
                    'expected_counts':expected,'observed_counts':observed},'diagnostics':diagnostics,
                'learning':{'qualified_transitions':sum(row[2] for row in trials),'minimum_context_samples':30,
                            'model_prior':200,'report_reimported_into_observations':False},
                'warnings':['Coût de référence des tentatives enregistrées, pas inventaire ni couverture OCR garantie.',
                    'Les actions sans rune ne sont pas attribuables à cet objet avec certitude.',
                    'Un échec isolé ne permet pas de distinguer mauvais conseil, mauvaise lecture et malchance.',
                    'Calibration automatique sur transitions réelles qualifiées ; amélioration non garantie après chaque session.']}
        self.report_dir.mkdir(parents=True,exist_ok=True)
        stem=self.report_dir/('bilan-'+current['id'])
        result.update(json_path=str(stem.with_suffix('.json')),html_path=str(stem.with_suffix('.html')))
        self._atomic(stem.with_suffix('.json'),dump(result))
        self._atomic(stem.with_suffix('.html'),render_report(result))
        with self._db() as db:db.execute('UPDATE evaluation_sessions SET closed=1,report=? WHERE id=?',(dump(result),current['id']))
        self.active=None;self.last_report=result;self.last_forecast_key=None
        return result

    @staticmethod
    def _atomic(path,text):
        temporary=path.with_suffix(path.suffix+'.tmp')
        temporary.write_text(text,encoding='utf8');temporary.replace(path)


def render_report(report):
    e=lambda value:escape(str(value))
    n=report['prediction_evaluation']['n'];brier=report['prediction_evaluation']['brier']
    lines=''.join(f'<tr><td>{e(r)}</td><td>{v}</td></tr>' for r,v in sorted(report['runes'].items()))
    return ('<!doctype html><html lang="fr"><meta charset="utf-8"><title>Bilan Forgely</title>'
        '<style>body{font:17px system-ui;max-width:900px;margin:40px auto;padding:0 20px;color:#29251f;background:#faf7f0}'
        'table{border-collapse:collapse;width:100%}td,th{padding:10px;border-bottom:1px solid #ccc;text-align:left}small{color:#555}</style>'
        f'<h1>Bilan de session · {e(report["item"])}</h1><p>Début UTC : {e(report["started_at"])}<br>Fin UTC : {e(report["finished_at"])}</p>'
        f'<h2>Objectif : {e(report["goal"]["status"])}</h2><p>Cibles : {e(report["goal"]["targets"])}<br>Jet final confirmé : {e(report["goal"]["final"])}</p>'
        f'<p>{report["attempts"]} tentatives enregistrées · coût connu : {report["known_cost"]:g} kamas de référence.</p>'
        f'<p>{report["unpriced_attempts"]} tentatives sans prix · {report["unassigned_actions"]} actions sans rune sur cette période.</p>'
        '<table><tr><th>Rune</th><th>Nombre</th></tr>'+lines+'</table>'
        f'<h2>Prévisions comparables : {n}</h2><p>Score Brier : {e(brier if brier is not None else "indisponible")}. '
        'Plus bas est meilleur ; ce score ne donne pas un pourcentage de fiabilité.</p>'
        f'<p>Transitions qualifiées pour l’expérience locale : {report["learning"]["qualified_transitions"]}.</p>'
        +''.join('<p><small>'+e(w)+'</small></p>' for w in report['warnings'])+'</html>')


def export_review(report,destination):
    destination=Path(destination)
    if any(destination.resolve()==Path(report[key]).resolve() for key in ('json_path','html_path')):
        raise ValueError('Choisis un fichier ZIP distinct des fichiers du bilan')
    for key in ('json_path','html_path'):
        if not Path(report[key]).is_file():raise ValueError('Bilan local introuvable')
    with zipfile.ZipFile(destination,'w',zipfile.ZIP_DEFLATED) as archive:
        for key in ('json_path','html_path'):
            file=Path(report[key]);archive.write(file,file.name)
    return destination
