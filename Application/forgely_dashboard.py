"""Native desktop presentation. This module never reads the game or stores attempts."""
import tkinter as tk
from tkinter import ttk
from forgely_session_ui import show_review


def stat_rows(observed, targets, *, verified=False):
    rows = []
    for stat in dict.fromkeys((*observed, *targets)):
        value, target = observed.get(stat), targets.get(stat)
        if value is None:
            state, tag = 'À lire', 'unknown'
        elif not verified:
            state, tag = 'À confirmer', 'pending'
        elif target is None:
            state, tag = 'Lu', 'normal'
        elif value >= target:
            state, tag = 'Atteint', 'success'
        else:
            state, tag = 'À compléter', 'pending'
        rows.append((stat, '—' if value is None else str(value),
                     '—' if target is None else str(target), state, tag))
    return rows


def advice_window_size(screen_width,screen_height):
    """Leave desktop margins and let the detail panel scroll on small screens."""
    return max(1,min(680,int(screen_width)-60)),max(1,min(700,int(screen_height)-80))


class ActivityLabel(tk.Label):
    """Keep a small UI-only session feed when existing callbacks update the label."""
    def __init__(self, parent, on_change, **kwargs):
        self._on_change = on_change
        self._last_text = kwargs.get('text', '')
        super().__init__(parent, **kwargs)

    def configure(self, cnf=None, **kwargs):
        text = kwargs.get('text', (cnf if isinstance(cnf, dict) else {}).get('text'))
        result = super().configure(cnf, **kwargs)
        if text is not None and text != self._last_text:
            self._last_text = text
            self._on_change(text)
        return result

    config = configure


class AtelierDashboard:
    def __init__(self, app, palette):
        self.app = app
        self.palette = palette
        self._table_key = None
        self.activity = []
        self.style = ttk.Style(app)
        self.style.theme_use('clam')
        self.apply_palette(palette)
        bg, panel, muted = palette['BG'], palette['PANEL'], palette['MUTED']
        app.geometry(f'{min(1180, app.winfo_screenwidth()-60)}x{min(780, app.winfo_screenheight()-100)}')
        app.minsize(min(960, app.winfo_screenwidth()-60), min(660, app.winfo_screenheight()-100))

        shell = tk.Frame(app, bg=bg)
        shell.pack(fill='both', expand=True)
        sidebar = tk.Frame(shell, bg=panel, width=190)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        app.label(sidebar, 'FORGELY', 22, bold=True, color=palette['FG']).pack(anchor='w', padx=23, pady=(31, 0))
        app.label(sidebar, 'VOTRE ATELIER, EN CLAIR.', 8, color=muted).pack(anchor='w', padx=24, pady=(4, 34))
        app.label(sidebar, 'ESPACE DE TRAVAIL', 8, bold=True, color=muted).pack(anchor='w', padx=24, pady=(0, 12))
        self.navigation = []
        for title, action in (
                ('Atelier', lambda: app.focus_set()),
                ('Jet cible', app.open_plan_editor),
                ('Historique', app.show_history),
                ('Bilan de session', lambda: show_review(app)),
                ('Outils', app.open_more_menu)):
            button = tk.Button(sidebar, text=title, command=action, anchor='w',
                font=(app.ui_fonts['body'], 11), relief='flat', bd=0, padx=15,
                pady=11, cursor='hand2', takefocus=True,
                highlightthickness=0,
                bg=palette['PANEL2'] if title == 'Atelier' else panel,
                fg=palette['GREEN'] if title == 'Atelier' else palette['FG'],
                activebackground=palette['PANEL2'], activeforeground=palette['FG'])
            button.pack(fill='x', padx=12, pady=3)
            self.navigation.append(button)
        support = tk.Frame(sidebar, bg=panel)
        support.pack(side='bottom', fill='x', padx=16, pady=23)
        for text, command in (('Apparence', app.show_appearance), ('Diagnostic OCR', app.show_ocr_diagnostic), ('Paramètres', app.show_settings)):
            app.button(support, text, command).pack(fill='x', pady=4)
        app.label(support, 'LOCAL · DONNÉES SUR VOTRE PC', 7, color=muted).pack(anchor='w', pady=(16, 0))

        main = tk.Frame(shell, bg=bg)
        main.pack(side='left', fill='both', expand=True, padx=25, pady=23)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(2, weight=1)
        heading = tk.Frame(main, bg=bg)
        heading.grid(row=0, column=0, sticky='ew', pady=(0, 17))
        title = tk.Frame(heading, bg=bg)
        title.pack(side='left')
        app.label(title, 'L’atelier', 27, bold=True).pack(anchor='w')
        app.label(title, 'Votre équipement. Vos objectifs. La prochaine décision.', 10, color=muted).pack(anchor='w', pady=(4, 0))
        app.button(heading, 'Mode discret', app.minimize_to_badge).pack(side='right', padx=(8, 0))
        app.mode_button = app.button(heading, '', app.toggle_observation_mode)
        app.mode_button.pack(side='right')
        app.update_mode_button()

        connection = app.card(main)
        connection.grid(row=1, column=0, sticky='ew', pady=(0, 17))
        connection_row = tk.Frame(connection, bg=panel)
        connection_row.pack(fill='x', padx=17, pady=(12, 3))
        app.game_state_label = app.label(connection_row, '● Atelier en attente', 11, bold=True, color=palette['GOLD'])
        app.game_state_label.pack(side='left')
        app.observe_button = app.button(connection_row, 'Démarrer l’observation', app.toggle_observer, primary=True)
        app.observe_button.pack(side='right')
        app.game_title_label = app.label(connection, 'Ouvrez l’atelier dans DOFUS, puis démarrez la lecture.', 9, color=muted, wraplength=780, justify='left')
        app.game_title_label.pack(anchor='w', padx=17, pady=(0, 5))
        tk.Checkbutton(support, text='Mode flottant automatique',
            variable=app.auto_floating, command=app.save_floating_preference,
            bg=panel, fg=muted, activebackground=panel, activeforeground=palette['FG'],
            selectcolor=palette['PANEL2'], highlightthickness=0,
            font=(app.ui_fonts['body'], 7)).pack(anchor='w', pady=(9, 0))

        workspace = tk.Frame(main, bg=bg)
        workspace.grid(row=2, column=0, sticky='nsew')
        workspace.columnconfigure(0, weight=3, minsize=375, uniform='work')
        workspace.columnconfigure(1, weight=2, minsize=250, uniform='work')
        workspace.rowconfigure(0, weight=1)
        equipment = app.card(workspace)
        equipment.grid(row=0, column=0, sticky='nsew', padx=(0, 14))
        app.label(equipment, 'ÉQUIPEMENT ACTUEL', 8, bold=True, color=muted).pack(anchor='w', padx=18, pady=(16, 6))
        item_heading = tk.Frame(equipment, bg=panel)
        item_heading.pack(fill='x', padx=18, pady=(0, 5))
        app.button(item_heading, 'Identifier', app.open_equipment_quick).pack(side='right', padx=(8, 0))
        app.plan_item_lbl = app.label(item_heading, 'Objet à identifier', 15, bold=True, wraplength=300, justify='left', anchor='w')
        app.plan_item_lbl.pack(side='left', fill='x', expand=True)
        self.reading_label = app.label(equipment, 'Aucune lecture disponible', 9, color=muted)
        self.reading_label.pack(anchor='w', padx=18, pady=(0, 12))
        table_area = tk.Frame(equipment, bg=panel)
        table_area.pack(fill='both', expand=True, padx=12)
        self.table = ttk.Treeview(table_area, columns=('stat', 'value', 'target', 'state'),
                                  show='headings', height=8, style='Forgely.Treeview', selectmode='browse')
        for key, text, width, anchor in (
                ('stat', 'Caractéristique', 160, 'w'), ('value', 'Actuel', 60, 'center'),
                ('target', 'Cible', 60, 'center'), ('state', 'Lecture', 105, 'w')):
            self.table.heading(key, text=text, anchor=anchor)
            self.table.column(key, width=width, minwidth=50, stretch=key in ('stat', 'state'), anchor=anchor)
        scroll = ttk.Scrollbar(table_area, orient='vertical', command=self.table.yview, style='Forgely.Vertical.TScrollbar')
        self.table.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.table.pack(side='left', fill='both', expand=True)
        self.empty_label = app.label(table_area, 'Le jet apparaîtra ici\naprès lecture de l’atelier.', 11, color=muted, justify='center')
        self.empty_label.place(relx=.5, rely=.52, anchor='center')
        self.pool_label = app.label(equipment, 'Puits —  ·  en attente de lecture', 10, bold=True, color=palette['GOLD'])
        self.pool_label.pack(side='bottom', before=table_area, anchor='w', padx=18, pady=(13, 12))

        advice = app.card(workspace)
        advice.grid(row=0, column=1, sticky='nsew')
        app.advice_heading = app.label(advice, 'PROCHAINE DÉCISION', 8, bold=True, color=muted, wraplength=260, justify='left')
        app.advice_heading.pack(anchor='w', padx=18, pady=(17, 14))
        app.main_rune_icon = tk.Label(advice, text='FM', fg=palette['GREEN'], bg=palette['PANEL2'],
            font=(app.ui_fonts['display'], 14, 'bold'), width=5, height=3)
        app.main_rune_icon.pack(anchor='w', padx=18, pady=(0, 13))
        app.home_advice_label = app.label(advice, 'En attente de DOFUS', 20, bold=True, wraplength=280, justify='left', anchor='w')
        app.home_advice_label.pack(anchor='w', fill='x', padx=18, pady=(0, 10))
        app.home_advice_detail = app.label(advice, 'Activez la lecture pour retrouver votre jet.', 10, color=muted, wraplength=280, justify='left')
        app.home_advice_detail.pack(anchor='w', padx=18, pady=(0, 14))
        app.plan_action_lbl = app.label(advice, '', 10, color=palette['GREEN'], wraplength=280, justify='left')
        app.plan_explain_lbl = app.label(advice, '', 9, color=muted, wraplength=280, justify='left')
        app.player_risk_label = app.label(advice, 'Risque : inconnu', 9, color=muted, wraplength=280, justify='left')
        app.player_risk_label.pack(anchor='w', padx=18, pady=(0, 10))
        modes = ttk.Combobox(advice, textvariable=app.goal_mode,
                            values=__import__('forgely_copilote').MODES, state='readonly', width=18)
        modes.pack(anchor='w', padx=18, pady=(0, 15))
        modes.bind('<<ComboboxSelected>>', lambda _: app.refresh_strategy())
        app.button(advice, 'Voir le détail', app.open_strategy).pack(anchor='w', padx=18, pady=(0, 12))
        advice.bind('<Configure>', self._resize_advice)

        bottom = tk.Frame(main, bg=bg)
        bottom.grid(row=3, column=0, sticky='ew', pady=(15, 0))
        bottom.columnconfigure(0, weight=3)
        bottom.columnconfigure(1, weight=2)
        last = app.card(bottom)
        last.grid(row=0, column=0, sticky='nsew', padx=(0, 14))
        app.label(last, 'FIL DE LECTURE', 8, bold=True, color=muted).pack(anchor='w', padx=17, pady=(13, 7))
        app.detect_label = ActivityLabel(last, self.add_activity, text='Aucune tentative détectée',
            bg=panel, fg=palette['FG'], font=(app.ui_fonts['display'], 11, 'bold'),
            wraplength=430, justify='left', anchor='w')
        app.detect_label.pack(anchor='w', padx=17)
        app.detect_help = app.label(last, 'Les lectures provisoires restent à vérifier.', 8, color=muted, wraplength=430, justify='left')
        app.detect_help.pack(anchor='w', padx=17, pady=(5, 0))
        self.activity_label = app.label(last, 'Votre session commence ici.', 8, color=muted, wraplength=430, justify='left')
        self.activity_label.configure(height=1)
        self.activity_label.pack(anchor='w', padx=17, pady=(7, 12))
        counts = app.card(bottom)
        counts.grid(row=0, column=1, sticky='nsew')
        app.label(counts, 'OBSERVATIONS LOCALES', 8, bold=True, color=muted).pack(anchor='w', padx=17, pady=(13, 7))
        app.total_lbl = app.label(counts, '0 tentative', 20, bold=True)
        app.total_lbl.pack(anchor='w', padx=17)
        rates = tk.Frame(counts, bg=panel)
        rates.pack(fill='x', padx=17, pady=(8, 12))
        app.stats_labels = {}
        for kind, color in (('SC', palette['GREEN']), ('SN', palette['GOLD']), ('EC', palette['RED'])):
            cell = tk.Frame(rates, bg=panel)
            cell.pack(side='left', padx=(0, 18))
            app.label(cell, kind, 8, color=muted).pack(side='left', padx=(0, 4))
            label = app.label(cell, '—', 10, bold=True, color=color)
            label.pack(side='left')
            app.stats_labels[kind] = label
        hidden = tk.Frame(main, bg=bg)
        for name in ('scan_label', 'ignored_label', 'atelier_info_label', 'reason_label', 'visual_label', 'rune_prob_lbl'):
            setattr(app, name, app.label(hidden, '', 9))
        tk.Label(main, textvariable=app.status, bg=bg, fg=muted,
            font=(app.ui_fonts['body'], 8), anchor='w', justify='left', wraplength=840).grid(row=4, column=0, sticky='ew', pady=(13, 0))
        self.apply_palette(palette)

    def _resize_advice(self, event):
        for name in ('advice_heading', 'home_advice_label', 'home_advice_detail',
                     'plan_action_lbl', 'plan_explain_lbl', 'player_risk_label'):
            getattr(self.app, name).configure(wraplength=max(190, event.width-38))
        if event.height < 350:
            self.app.main_rune_icon.pack_forget()
        elif not self.app.main_rune_icon.winfo_manager():
            self.app.main_rune_icon.pack(anchor='w', padx=18, pady=(0, 13), before=self.app.home_advice_label)

    def fit_advice(self):
        text = self.app.home_advice_detail.cget('text')
        if len(text) > 210:
            self.app.home_advice_detail.configure(text=text[:207].rstrip() + '…')

    def add_activity(self, text):
        self.activity.insert(0, text)
        del self.activity[8:]
        previous = self.activity[1:2]
        self.activity_label.configure(text=previous[0][:75] if previous else 'Lecture de la session en cours.')

    def apply_palette(self, palette):
        self.palette = palette
        font = self.app.ui_fonts
        self.style.configure('Forgely.Treeview', background=palette['PANEL'],
            fieldbackground=palette['PANEL'], foreground=palette['FG'], borderwidth=0,
            bordercolor=palette['PANEL'], lightcolor=palette['PANEL'], darkcolor=palette['PANEL'],
            font=(font['body'], 10), rowheight=30, relief='flat')
        self.style.configure('Forgely.Treeview.Heading', background=palette['PANEL2'],
            foreground=palette['MUTED'], font=(font['display'], 9, 'bold'), borderwidth=0, relief='flat')
        self.style.map('Forgely.Treeview', background=[('selected', palette['PANEL2'])], foreground=[('selected', palette['FG'])])
        self.style.configure('Forgely.Vertical.TScrollbar', background=palette['PANEL2'],
            troughcolor=palette['PANEL'], bordercolor=palette['PANEL'], arrowcolor=palette['MUTED'])
        self.style.configure('TCombobox', fieldbackground=palette['PANEL2'], background=palette['PANEL2'], foreground=palette['FG'])
        self.style.map('TCombobox', fieldbackground=[('readonly', palette['PANEL2'])], foreground=[('readonly', palette['FG'])])
        if hasattr(self, 'table'):
            for tag, color in (('success', palette['GREEN']), ('pending', palette['GOLD']), ('unknown', palette['MUTED']), ('normal', palette['FG'])):
                self.table.tag_configure(tag, foreground=color)

    def sync(self):
        app = self.app
        verified = bool(app.active_equipment_verified and app.live_jet is not None and not app.live_after_fusion)
        observed = app.live_jet if verified else (app.workshop_readings.partial_jet or app.workshop_readings.jet or {})
        if not app.workshop_active:
            observed = {}
        targets = {k: v['target'] for k, v in (app.plan or {}).get('stats', {}).items()
                   if v.get('target') is not None}
        if app.plan and app.active_equipment_verified and app.item.get() != app.plan.get('item'):
            targets = {}
        rows = stat_rows(observed, targets, verified=verified)
        key = tuple(rows)
        if key != self._table_key:
            self._table_key = key
            self.table.delete(*self.table.get_children())
            for stat, value, target, state, tag in rows:
                self.table.insert('', 'end', values=(stat, value, target, state), tags=(tag,))
        if rows:
            self.empty_label.place_forget()
        else:
            self.empty_label.place(relx=.5, rely=.52, anchor='center')
        caption = 'Lecture confirmée de l’équipement' if verified else 'Lecture provisoire · à confirmer' if observed else 'Aucune lecture disponible'
        self.reading_label.configure(text=caption)
        pool = app.live_pool if verified else app.workshop_readings.partial_pool
        if not app.workshop_active:
            pool = None
        amount = '—' if pool is None else f'{pool:g}'.replace('.', ',')
        self.pool_label.configure(text='Puits ' + amount + ('  ·  confirmé' if verified and pool is not None else '  ·  provisoire' if pool is not None else '  ·  en attente de lecture'))

