"""Fail-isolated session evaluation hooks and explicit local report export."""
import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox
from forgely_data import DB_FILE
from forgely_session_review import SessionRecorder, export_review


def install_recorder(app):
    app.session_recorder=None
    try:app.session_recorder=SessionRecorder(DB_FILE)
    except (OSError,sqlite3.Error,ValueError) as exc:app.session_review_error=str(exc)


def recorder(app):
    value=getattr(app,'session_recorder',None)
    return value if isinstance(value,SessionRecorder) else None


def capture_scope(app):
    mailbox=getattr(app,'frame_mailbox',None)
    if mailbox is None:return 'application:'+str(id(app))
    return str(id(mailbox))+':'+str(mailbox.generation())


def _guard(app,operation):
    try:return operation()
    except (OSError,sqlite3.Error,ValueError,TypeError,KeyError) as exc:
        app.session_review_error=str(exc)
        return None


def review_boundary(app):
    rec=recorder(app)
    if rec is None or rec.active is None:return
    def run():
        plan=app.plan or {}
        goals={s:v['target'] for s,v in plan.get('stats',{}).items() if v.get('target') is not None}
        identity=(app.item.get(),goals,plan.get('level'),capture_scope(app))
        if not app.active_equipment_verified or plan.get('item')!=app.item.get() or identity!=rec.active['identity']:
            rec.finish(jets=None,pool=None,confirmed=False,reason='objet_objectif_ou_capture_modifié')
    return _guard(app,run)


def review_tick(app,proposal=None):
    rec=recorder(app)
    if rec is None:return
    review_boundary(app)
    def run():
        plan=app.plan
        if (not plan or not app.active_equipment_verified or app.live_after_fusion
                or not app.live_jet or app.live_pool is None or plan.get('item')!=app.item.get()):return
        from forgely_tools import read_settings
        goals={s:v['target'] for s,v in plan['stats'].items() if v.get('target') is not None}
        cfg=read_settings()
        rec.ensure_session(item=app.item.get(),targets=goals,jets=app.live_jet,pool=app.live_pool,
                           prices=cfg['prices'],scope=capture_scope(app),level=plan.get('level'),mode=cfg.get('strategy'))
        if proposal is not None and proposal.rune:
            prediction=(proposal.estimates or {}).get('prediction')
            rec.forecast(proposal.rune,prediction,frame=app.latest_observation_id,scope=capture_scope(app))
    return _guard(app,run)


def review_event(app,obs_id,item,rune,outcome,frame,scope=None):
    rec=recorder(app)
    if rec is None:return
    return _guard(app,lambda:rec.event(obs_id,item,rune,outcome,frame=frame,
                                      scope=scope if scope is not None else capture_scope(app)))


def review_transition(app,obs_id,before,after,complete):
    rec=recorder(app)
    if rec is None:return
    return _guard(app,lambda:rec.transition(obs_id,before,after,qualified=complete))


def close_review(app):
    rec=recorder(app)
    if rec is not None and rec.active:
        return _guard(app,lambda:rec.finish(jets=None,pool=None,confirmed=False,reason='application_fermée'))


def show_review(app):
    rec=recorder(app)
    if rec is None:
        messagebox.showerror('Bilan indisponible',getattr(app,'session_review_error','Évaluation locale indisponible.'),parent=app);return
    review_boundary(app)
    if rec.active is None and rec.last_report is None:review_tick(app)
    try:
        confirmed=bool(rec.active and app.active_equipment_verified and not app.live_after_fusion
            and app.item.get()==rec.active['meta']['item'] and capture_scope(app)==rec.active['identity'][3])
        result=rec.finish(jets=app.live_jet,pool=app.live_pool,confirmed=confirmed)
    except (OSError,sqlite3.Error,ValueError,TypeError) as exc:
        messagebox.showerror('Bilan',str(exc),parent=app);return
    app.live_laboratory.notify_observation()
    win=tk.Toplevel(app);win.title('Forgely — Bilan de ma session');win.geometry('730x560')
    content=tk.Text(win,wrap='word',padx=18,pady=18)
    content.pack(fill='both',expand=True)
    evaluation=result['prediction_evaluation'];n=evaluation['n']
    outcome={'atteint':'Objectif atteint','non_atteint':'Objectif non atteint','inconnu':'Jet final à confirmer'}[result['goal']['status']]
    lines=[result['item']+' — '+outcome,
           f"{result['attempts']} tentatives enregistrées · coût de référence connu : {result['known_cost']:g} kamas.",
           f"{result['unpriced_attempts']} tentatives sans prix · {result['unassigned_actions']} actions sans rune sur cette période.",
           '', 'Runes utilisées : '+(', '.join(f'{k} ×{v}' for k,v in sorted(result['runes'].items())) or 'aucune enregistrée'),
           '',f'{n} prévisions antérieures au résultat et comparables.']
    if n:
        lines.append(f"Score Brier : {evaluation['brier']:.4f} (plus bas = meilleur ; ce n’est pas un pourcentage de fiabilité).")
        lines.extend(f"{k} : {evaluation['expected_counts'][k]:.2f} attendus / {evaluation['observed_counts'][k]} observés" for k in ('SC','SN','EC'))
    lines.extend(('',f"{result['learning']['qualified_transitions']} transitions réelles qualifiées enregistrées pour l’expérience locale.",
        'Les résultats fiables enrichissent la calibration existante. Un bilan n’est jamais réimporté comme de nouveaux clics.',
        '',*result['warnings'],'','Bilan enregistré localement :',result['json_path'],result['html_path']))
    content.insert('1.0','\n'.join(lines));content.configure(state='disabled')
    def export():
        path=filedialog.asksaveasfilename(parent=win,title='Exporter mon bilan',defaultextension='.zip',
            initialfile='Bilan-Forgely-'+result['session_id'][:8]+'.zip',filetypes=[('Archive ZIP','*.zip')])
        if not path:return
        try:export_review(result,path)
        except (OSError,ValueError) as exc:messagebox.showerror('Export',str(exc),parent=win);return
        messagebox.showinfo('Export terminé','Le ZIP contient le rapport lisible et les données du bilan. Tu peux le joindre à la conversation.',parent=win)
    tk.Button(win,text='Exporter le bilan (.zip)',command=export).pack(pady=12)
