"""Simulation of the currently confirmed item. Worker never calls Tk."""
from copy import deepcopy
import queue
import threading
import tkinter as tk
from tkinter import messagebox
from forgely_dofocus import natural_profile
from forgely_tools import natural_bounds, read_settings, cost_since
from forgely_data import DB_FILE
from forgely_simulation_job import simulate_context


def confirmed_context(app):
    from forgely_measured_goals import MeasuredGoals,current_snapshot
    from forgely_learning import complete_learning_profile
    measured=getattr(app,'measured_goals',None)
    snapshot=current_snapshot(app) if isinstance(measured,MeasuredGoals) and measured.targets else None
    plan=getattr(app,'plan',None) or {}
    if not app.active_equipment_verified or not app.item.get().strip():
        raise ValueError('Confirme un équipement avant de simuler.')
    if isinstance(measured,MeasuredGoals) and measured.targets:
        if snapshot is None:raise ValueError('Attends la relecture confirmée du jet et du puits.')
        jets,pool=snapshot;targets=dict(measured.targets)
    else:
        if app.live_after_fusion or app.live_jet is None or app.live_pool is None or plan.get('item')!=app.item.get():
            raise ValueError('Confirme le jet, le puits et les objectifs avant de simuler.')
        jets,pool=app.live_jet,app.live_pool
        targets={s:v['target'] for s,v in plan.get('stats',{}).items() if v.get('target') is not None}
    if not targets:raise ValueError('Définis le jet souhaité avant de simuler.')
    item=app.item.get().strip()
    profile=natural_profile(item) or complete_learning_profile(item)
    complete=profile is not None
    if profile is None:profile={s:v[1] for s,v in natural_bounds(item).items()}
    if not profile:raise ValueError('Maxima naturels manquants pour cet objet.')
    cfg=read_settings();budget=None
    if cfg.get('budget_kamas'):
        cost=cost_since(app.budget_start_cursor,cfg['prices'])
        if not cost['complete']:raise ValueError('Dépenses incomplètes : complète les prix avant de simuler sous budget.')
        budget=max(0,cfg['budget_kamas']-cost['known_cost'])
    return deepcopy(dict(item=item,jets=jets,targets=targets,natural_max=profile,
        profile_complete=complete,pool=pool,prices=cfg['prices'],mode=cfg.get('strategy','Chances maximales'),
        level=plan.get('level') if plan.get('item')==item else None,budget=budget))


def mount_simulator(app,parent,window):
    label=app.label(parent,'SIMULATEUR — modèle dynamique du copilote',12,bold=True)
    label.pack(anchor='w',padx=17,pady=(18,5))
    app.label(parent,'Recalcule rune, difficulté et probabilités après chaque clic virtuel. Les résultats restent séparés des observations réelles.',10,wraplength=620).pack(anchor='w',padx=17)
    controls=tk.Frame(parent,bg=parent.cget('bg'));controls.pack(fill='x',padx=17,pady=8)
    sessions=tk.StringVar(value='100');approximate=tk.BooleanVar(value=False)
    app.label(controls,'Sessions (1–2000)',10).pack(side='left')
    tk.Entry(controls,textvariable=sessions,width=6).pack(side='left',padx=10)
    tk.Checkbutton(parent,text='Pertes approximatives si aucune transition réelle comparable',
        variable=approximate,bg=parent.cget('bg'),anchor='w').pack(anchor='w',padx=17)
    status=app.label(parent,'Par défaut, une perte inconnue interrompt la session sans inventer de résultat.',10,wraplength=620)
    status.pack(anchor='w',padx=17,pady=5)
    running=[False];cancel=threading.Event()
    def closed(event):
        if event.widget is window:cancel.set()
    window.bind('<Destroy>',closed,add='+')

    def start():
        if running[0]:return
        try:
            n=int(sessions.get())
            if not 1<=n<=2000:raise ValueError('Entre 1 et 2000 sessions par lancement.')
            context=confirmed_context(app)
            loss_mode='uniform' if approximate.get() else 'stop'
        except (ValueError,TypeError) as exc:
            messagebox.showerror('Simulation',str(exc),parent=window);return
        running[0]=True;cancel.clear();status.configure(text='Simulation de l’état capturé en cours…')
        results=queue.Queue(maxsize=1)
        def worker():
            try:results.put(('ok',simulate_context(context,db_file=DB_FILE,trials=n,
                max_attempts=100,loss_mode=loss_mode,cancel=cancel.is_set)))
            except Exception as exc:results.put(('error',str(exc)))
        threading.Thread(target=worker,name='Forgely-Simulation',daemon=True).start()
        def poll():
            if not window.winfo_exists():cancel.set();return
            try:kind,result=results.get_nowait()
            except queue.Empty:window.after(100,poll);return
            running[0]=False
            if kind=='error':status.configure(text='Simulation interrompue.');messagebox.showerror('Simulation',result,parent=window);return
            lo,hi=result['completion_bounds']
            text=(f"{result['trials']} sessions · {result['completed']} objectifs atteints · "
                  f"{result['unknown_transitions']} transitions inconnues.\n"
                  f"Bornes de réussite virtuelle : {100*lo:.1f}–{100*hi:.1f} % ; "
                  f"coût moyen compté jusqu’à l’arrêt : {result['mean_known_cost']:,.0f} kamas.\n"
                  + '\n'.join(result['warnings']))
            status.configure(text=text)
            messagebox.showinfo('Résultats virtuels — modèle du copilote',text,parent=window)
        window.after(100,poll)
    app.button(parent,'Simuler mon objectif',start,True).pack(anchor='w',padx=17,pady=10)
