"""Desktop entry point for repeatable, offline Forgely training."""
from pathlib import Path
import argparse
import json
import os
import queue
import sys
import threading
import time
import traceback
import webbrowser


def output_directory():
    base = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent.parent
    return base / 'Entrainements'


def self_test(directory):
    from forgely_training import TrainingConfig, run_training
    result = run_training(TrainingConfig(item_id=14092, targets={'Force': 40},
        episodes=2, max_steps=5, evaluation_episodes=2), Path(directory))
    Path(directory, 'self-test.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0


class TrainingWindow:
    def __init__(self, root, output_root=None):
        import tkinter as tk
        from tkinter import ttk
        from forgely_equipment_catalog import EquipmentCatalog, equipment_bounds
        from forgely_dofocus import RUNE_CHOICES, WEIGHT_PER_POINT
        self.tk, self.ttk = tk, ttk
        self.bounds_for, self.rune_choices = equipment_bounds, RUNE_CHOICES
        self.root = root
        self.output_root = Path(output_root) if output_root else output_directory()
        self.catalogue = EquipmentCatalog()
        self.items = {self.label(item): item for item in self.catalogue.items
                      if equipment_bounds(item) and set(equipment_bounds(item)).issubset(WEIGHT_PER_POINT)}
        self.events = queue.Queue()
        self.stop_event = threading.Event()
        self.running = False
        self.closing = False
        self.last_report = None
        self.targets = {}
        root.title('Forgely — Entraînement')
        width = min(1020, max(640, root.winfo_screenwidth() - 60))
        height = min(700, max(500, root.winfo_screenheight() - 110))
        root.geometry(f'{width}x{height}')
        root.minsize(min(860, width), min(620, height))
        try: root.iconbitmap(str(Path(__file__).parent / 'assets' / 'forgely.ico'))
        except tk.TclError: pass
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('.', font=('Segoe UI', 10))
        style.configure('Title.TLabel', font=('Segoe UI', 19, 'bold'))
        style.configure('Accent.TButton', padding=9)
        outer = ttk.Frame(root, padding=18)
        outer.pack(fill='both', expand=True)
        ttk.Label(outer, text='Entraîner Forgely', style='Title.TLabel').pack(anchor='w')
        ttk.Label(outer, text='Sessions virtuelles ou apprentissage à partir de tes vidéos réelles.').pack(anchor='w', pady=(3, 8))
        self.notebook = ttk.Notebook(outer)
        self.notebook.pack(fill='both', expand=True)
        virtual = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(virtual, text='Sessions virtuelles')
        from forgely_video_ui import VideoPanel
        self.video_panel = VideoPanel(self.notebook, self.output_root)
        self.notebook.add(self.video_panel, text='Sessions vidéo')
        outer = virtual
        selector = ttk.Frame(outer)
        selector.pack(fill='x')
        ttk.Label(selector, text='Objet').pack(side='left', padx=(0, 12))
        self.item_value = tk.StringVar()
        self.item_box = ttk.Combobox(selector, textvariable=self.item_value, values=list(self.items), width=70)
        self.item_box.pack(side='left', fill='x', expand=True)
        self.item_box.bind('<KeyRelease>', self.filter_items)
        self.item_box.bind('<<ComboboxSelected>>', self.select_item)
        ttk.Button(selector, text='Afficher le jet', command=self.select_item).pack(side='left', padx=(8, 0))
        self.controls = [self.item_box]
        middle = ttk.Panedwindow(outer, orient='horizontal')
        middle.pack(fill='both', expand=True, pady=12)
        goals = ttk.Labelframe(middle, text='Jet voulu', padding=10)
        parameter_panel = ttk.Labelframe(middle, text='Sessions virtuelles', padding=4)
        parameter_canvas = tk.Canvas(parameter_panel, highlightthickness=0, width=330)
        parameter_scrollbar = ttk.Scrollbar(parameter_panel, orient='vertical', command=parameter_canvas.yview)
        parameter_canvas.configure(yscrollcommand=parameter_scrollbar.set)
        parameter_scrollbar.pack(side='right', fill='y')
        parameter_canvas.pack(side='left', fill='both', expand=True)
        parameters = ttk.Frame(parameter_canvas, padding=8)
        parameter_window = parameter_canvas.create_window((0, 0), window=parameters, anchor='nw')
        parameters.bind('<Configure>', lambda e: parameter_canvas.configure(scrollregion=parameter_canvas.bbox('all')))
        parameter_canvas.bind('<Configure>', lambda e: parameter_canvas.itemconfigure(parameter_window, width=e.width))
        middle.add(goals, weight=3)
        middle.add(parameter_panel, weight=2)
        ttk.Label(goals, text='Minimums préremplis au maximum naturel.\nToute valeur supérieure satisfait la cible. Vide = non ciblé.').pack(anchor='w', pady=(0, 8))
        target_outer = ttk.Frame(goals)
        target_outer.pack(fill='both', expand=True)
        self.canvas = tk.Canvas(target_outer, highlightthickness=0, background='#f3f3f3', width=420)
        scrollbar = ttk.Scrollbar(target_outer, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.target_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.target_frame, anchor='nw')
        self.target_frame.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        extra = ttk.Frame(goals)
        extra.pack(side='bottom', fill='x', pady=(8, 0), before=target_outer)
        self.extra_value = tk.StringVar(value='PA')
        self.extra_box = ttk.Combobox(extra, textvariable=self.extra_value, state='readonly', values=sorted(RUNE_CHOICES), width=22)
        self.extra_box.pack(side='left')
        self.extra_button = ttk.Button(extra, text='Ajouter une cible / exo', command=self.add_extra)
        self.extra_button.pack(side='left', padx=6)
        self.controls.extend([self.extra_box, self.extra_button])
        self.episodes = tk.StringVar(value='1000')
        self.max_steps = tk.StringVar(value='200')
        self.evaluations = tk.StringVar(value='200')
        self.preset = tk.StringVar(value='Moyen')
        self.pool = tk.StringVar(value='0')
        self.resume = tk.BooleanVar(value=True)
        self.generalization = tk.BooleanVar(value=False)
        self.preparatory = tk.BooleanVar(value=False)
        self.use_real = tk.BooleanVar(value=True)
        for row, (label, variable, values) in enumerate([
            ('Nombre de sessions', self.episodes, ('100', '1000', '10000', '100000')),
            ('Runes max. / session', self.max_steps, ('50', '100', '200', '500')),
            ('Sessions de vérification', self.evaluations, ('200', '500', '1000')),
            ('Jet de départ', self.preset, ('Minimum', 'Moyen', 'Maximum')),
            ('Puits de départ', self.pool, None),
        ]):
            ttk.Label(parameters, text=label).grid(row=row, column=0, sticky='w', pady=7)
            widget = ttk.Combobox(parameters, textvariable=variable, values=values, width=15,
                                 state='readonly' if variable is self.preset else 'normal') if values else ttk.Entry(parameters, textvariable=variable, width=17)
            widget.grid(row=row, column=1, sticky='ew', padx=(10, 0))
            self.controls.append(widget)
            if variable is self.preset: self.preset_box = widget
        experimental = ttk.Checkbutton(parameters, text='Essayer la stratégie généralisable (expérimental)',
                                       variable=self.generalization)
        experimental.grid(row=5,column=0,columnspan=2,sticky='w',pady=4)
        self.controls.append(experimental)
        check = ttk.Checkbutton(parameters, text='Reprendre un apprentissage compatible', variable=self.resume)
        check.grid(row=6, column=0, columnspan=2, sticky='w', pady=12)
        self.controls.append(check)
        ttk.Label(parameters, text='Objectif : atteindre toutes les cibles du jet souhaité.\n\nModèle FM partagé : résultats simulés.\nLa vérification compare la stratégie apprise\nà une stratégie de référence sur de nouveaux essais.', wraplength=320).grid(row=7, column=0, columnspan=2, sticky='w', pady=10)
        parameters.columnconfigure(1, weight=1)
        prep = ttk.Checkbutton(parameters,text='Comparer les actions préparatoires / overs temporaires',variable=self.preparatory)
        prep.grid(row=8,column=0,columnspan=2,sticky='w',pady=4)
        self.controls.append(prep)
        ttk.Label(parameters,text='Expérimental : compare le jet complet au témoin.\nAucun puits fictif ni activation automatique des conseils.',wraplength=320).grid(row=9,column=0,columnspan=2,sticky='w')
        real=ttk.Checkbutton(parameters,text='Utiliser les observations réelles fiables',variable=self.use_real)
        real.grid(row=10,column=0,columnspan=2,sticky='w',pady=6)
        self.controls.append(real)
        footer = ttk.Frame(outer)
        footer.pack(side='bottom', fill='x', before=middle)
        buttons = ttk.Frame(footer)
        buttons.pack(fill='x')
        self.start_button = ttk.Button(buttons, text='Lancer l’entraînement', style='Accent.TButton', command=self.start)
        self.start_button.pack(side='left')
        self.stop_button = ttk.Button(buttons, text='Arrêter et sauvegarder', command=self.stop, state='disabled')
        self.stop_button.pack(side='left', padx=8)
        self.report_button = ttk.Button(buttons, text='Voir le rapport', command=self.open_report, state='disabled')
        self.report_button.pack(side='right')
        ttk.Button(buttons, text='Ouvrir les résultats', command=self.open_directory).pack(side='right', padx=8)
        self.progress = ttk.Progressbar(footer, mode='determinate')
        self.progress.pack(fill='x', pady=(12, 8))
        self.status = tk.StringVar(value='Prêt. Conseils : 40 % simulations et 60 % statistiques réelles lorsque les deux sources sont disponibles et comparables.')
        self.status_label = ttk.Label(footer, textvariable=self.status, wraplength=960)
        self.status_label.pack(anchor='w')
        footer.bind('<Configure>', lambda e: self.status_label.configure(wraplength=max(200, e.width)))
        default = next(item for item in self.catalogue.items if item.item_id == 14092)
        self.item_value.set(self.label(default))
        self.select_item()
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.after(100, self.poll)

    @staticmethod
    def label(item):
        return f'{item.identity_name} — niv. {item.level} · {item.item_id}'

    def filter_items(self, event=None):
        if self.running: return
        query = self.item_value.get().casefold()
        self.item_box.configure(values=[name for name in self.items if query in name.casefold()][:150])

    def select_item(self, event=None):
        if self.running: return
        item = self.items.get(self.item_value.get())
        if item is None:
            self.status.set('Choisis un objet dans la liste, puis clique sur « Afficher le jet ».')
            return
        self.selected_id = item.item_id
        self.bounds = self.bounds_for(item)
        self.targets = {stat: self.tk.StringVar(value=str(hi) if hi >= 0 else '')
                        for stat, (lo, hi) in self.bounds.items()}
        self.render_targets()

    def render_targets(self):
        for widget in self.target_frame.winfo_children(): widget.destroy()
        for col, text in enumerate(('Caractéristique', 'Naturel', 'Cible')):
            self.ttk.Label(self.target_frame, text=text).grid(row=0, column=col, sticky='w', padx=7, pady=5)
        for row, (stat, variable) in enumerate(self.targets.items(), 1):
            self.ttk.Label(self.target_frame, text=stat).grid(row=row, column=0, sticky='w', padx=7, pady=4)
            pair = self.bounds.get(stat)
            natural = f'{pair[0]} à {pair[1]}' if pair else 'Exo'
            self.ttk.Label(self.target_frame, text=natural).grid(row=row, column=1, padx=7)
            self.ttk.Entry(self.target_frame, textvariable=variable, width=8).grid(row=row, column=2, padx=7)

    def add_extra(self):
        if self.running: return
        stat = self.extra_value.get()
        if stat not in self.targets:
            self.targets[stat] = self.tk.StringVar(value='1')
            self.render_targets()

    @staticmethod
    def number(text):
        import math
        try: value = float(text.strip().replace(',', '.'))
        except ValueError: raise ValueError('Indique un nombre valide.') from None
        if not math.isfinite(value): raise ValueError('Indique un nombre fini.')
        return value

    def start(self):
        from tkinter import messagebox
        from forgely_training import TrainingConfig
        if self.running: return
        try:
            item = self.items.get(self.item_value.get())
            if item is None or item.item_id != self.selected_id:
                raise ValueError('Sélectionne un objet puis affiche son jet avant de lancer.')
            targets = {s: self.number(v.get()) for s, v in self.targets.items() if v.get().strip()}
            config = TrainingConfig(item_id=item.item_id, targets=targets,
                episodes=int(self.episodes.get()), max_steps=int(self.max_steps.get()),
                evaluation_episodes=int(self.evaluations.get()),
                policy_search_episodes=256 if self.generalization.get() else 0,
                initial_preset={'Minimum':'min', 'Moyen':'moyen', 'Maximum':'max'}[self.preset.get()],
                initial_pool=self.number(self.pool.get()),
                resume=self.resume.get(),allow_preparatory=self.preparatory.get(),use_real_observations=self.use_real.get())
        except (ValueError, KeyError) as exc:
            messagebox.showerror('Configuration à corriger', str(exc), parent=self.root)
            return
        self.stop_event.clear()
        self.running = True
        self.start_button.configure(state='disabled')
        self.stop_button.configure(state='normal')
        for widget in self.controls: widget.configure(state='disabled')
        for widget in self.target_frame.winfo_children():
            if isinstance(widget, self.ttk.Entry): widget.configure(state='disabled')
        self.progress.configure(value=0, maximum=config.episodes)
        self.status.set('Préparation de l’entraînement…')
        def worker():
            from forgely_training import run_training
            last_progress = [0.]
            def progress(info):
                now = time.monotonic()
                if now - last_progress[0] >= .1 or info.get('phase') == 'done':
                    self.events.put(('progress', info))
                    last_progress[0] = now
            try:
                result = run_training(config, self.output_root, cancel=self.stop_event,
                                      progress=progress)
                self.events.put(('done', result))
            except Exception as exc:
                self.events.put(('error', (str(exc), traceback.format_exc())))
        threading.Thread(target=worker, name='Forgely-Entrainement', daemon=True).start()

    def stop(self):
        self.stop_event.set()
        self.stop_button.configure(state='disabled')
        self.status.set('Arrêt demandé. Sauvegarde de la progression en cours…')

    def poll(self):
        from tkinter import messagebox
        try:
            for _ in range(25):
                kind, payload = self.events.get_nowait()
                if kind == 'progress':
                    completed = payload.get('completed', 0)
                    total = payload.get('total', self.progress['maximum'])
                    self.progress.configure(value=completed, maximum=max(1, total))
                    phase = {'training':'Entraînement','policy_search':'Apprentissage généralisable'}.get(payload.get('phase'),'Vérification')
                    self.status.set(f'{phase} : {completed} / {total} sessions. Tu peux arrêter et sauvegarder à tout moment.')
                else:
                    self.running = False
                    self.start_button.configure(state='normal')
                    self.stop_button.configure(state='disabled')
                    for widget in self.controls: widget.configure(state='normal')
                    self.extra_box.configure(state='readonly')
                    self.preset_box.configure(state='readonly')
                    for widget in self.target_frame.winfo_children():
                        if isinstance(widget, self.ttk.Entry): widget.configure(state='normal')
                    if kind == 'error':
                        self.status.set('Entraînement non terminé : ' + payload[0])
                        if not self.closing: messagebox.showerror('Entraînement interrompu', payload[0], parent=self.root)
                    else:
                        self.last_report = self.output_root / payload['run_id'] / 'rapport.html'
                        self.report_button.configure(state='normal')
                        count = payload.get('episodes_completed', 0)
                        suffix = 'Arrêté et sauvegardé' if payload.get('cancelled') else 'Terminé et sauvegardé'
                        evaluation = payload.get('evaluation', {})
                        learned = evaluation.get('learned', {})
                        baseline = evaluation.get('baseline', {})
                        comparison = ''
                        if learned.get('episodes') and baseline.get('episodes'):
                            comparison = (f" Vérification : {learned['successes']}/{learned['episodes']} objectifs atteints "
                                          f"contre {baseline['successes']}/{baseline['episodes']} pour le témoin.")
                        use = (' Entraînement inactif dans les conseils : amélioration du jet complet non démontrée ou vérification insuffisante.'
                               if not payload.get('eligible_for_advice') else
                               ' Gain démontré dans le simulateur. Conseils compatibles : 40 % simulations, 60 % statistiques réelles lorsque les deux sources sont disponibles et comparables.')
                        extra=payload.get('policy_search',{}).get('episodes',0)
                        self.status.set(f'{suffix} : {count} sessions et {extra} trajectoires de recherche.{comparison}{use}')
                    if self.closing:
                        self.video_panel.request_close(self.root.destroy)
                        return
        except queue.Empty: pass
        self.root.after(100, self.poll)

    def open_report(self):
        if self.last_report and self.last_report.is_file(): webbrowser.open(self.last_report.resolve().as_uri())

    def open_directory(self):
        from tkinter import messagebox
        try:
            self.output_root.mkdir(parents=True, exist_ok=True)
            os.startfile(self.output_root)
        except OSError as exc: messagebox.showerror('Dossier inaccessible', str(exc), parent=self.root)

    def close(self):
        if self.running:
            self.closing = True
            self.stop()
        else: self.video_panel.request_close(self.root.destroy)


def main():
    parser = argparse.ArgumentParser(description='Entraînement local de Forgely')
    parser.add_argument('--self-test', type=Path, metavar='DOSSIER')
    parser.add_argument('--output-root', type=Path)
    args = parser.parse_args()
    if args.self_test: return self_test(args.self_test)
    import tkinter as tk
    root = tk.Tk()
    TrainingWindow(root, args.output_root)
    root.mainloop()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
