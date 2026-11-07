"""Small always-on-top draggable overlay. Tk mainloop owns all UI operations."""
from __future__ import annotations
import tkinter as tk
from pathlib import Path
import sys
from forgely_rune_icons import rune_icon_path
from forgely_typographie import families as font_families
from forgely_themes import THEMES, DEFAULT

ASSET = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent)) / 'assets' / 'forgely_64.png'


class FloatingBadge(tk.Toplevel):
    def __init__(self, root, on_open, on_toggle, on_quit, on_items=None, on_strategy=None, on_workbench=None):
        super().__init__(root)
        self.root = root
        self.palette = THEMES.get(getattr(root, 'theme_name', DEFAULT), THEMES[DEFAULT])
        self.ui_fonts = font_families(root)
        self.on_open = on_open
        self.on_toggle = on_toggle
        self.on_quit = on_quit
        self.overrideredirect(True)
        self.wm_attributes('-topmost', True)
        self.configure(bg=self.palette['PANEL'])
        self.geometry('270x86+25+110')
        # On Windows, transparent corners make the floating badge truly rounded.
        # Other systems retain the solid background if transparency is unavailable.
        self._rounded_overlay=False
        try:
            if sys.platform == 'win32':
                self.wm_attributes('-transparentcolor', '#FE00FE')
                self.configure(bg='#FE00FE')
                self._rounded_overlay=True
                from forgely_arrondi import RoundedButton
                self._background=tk.Canvas(self,bg='#FE00FE',bd=0,highlightthickness=0,width=270,height=86)
                self._background.place(x=0,y=0,width=270,height=86)
                self._background.create_polygon(12,0,258,0,270,12,270,74,258,86,12,86,0,74,0,12,
                    smooth=True,splinesteps=32,fill=self.palette['PANEL'],outline='')
        except tk.TclError:
            self._rounded_overlay=False
            self.configure(bg=self.palette['PANEL'])
        # Intentionally avoid fabricated game glyphs. Text remains readable at small size.
        self.photo = None
        self._rune_photo = None
        self.icon_label = tk.Label(self, text='FM', fg=self.palette['GREEN'], bg=self.palette['PANEL2'],
                                   font=(self.ui_fonts['display'], 12, 'bold'), padx=10, cursor='hand2',
                                   highlightthickness=0)
        self.icon_label.place(x=12,y=15,width=50,height=56)
        self.advice_label = tk.Label(self, text='Jet à lire', fg=self.palette['FG'], bg=self.palette['PANEL'],
                                    font=(self.ui_fonts['display'], 10, 'bold'), wraplength=174, anchor='w', justify='left')
        self.advice_label.place(x=75,y=10,width=180,height=41)
        self.status_dot = tk.Label(self, text='●', fg=self.palette['MUTED'], bg=self.palette['PANEL'],
                                   font=(self.ui_fonts['display'], 11, 'bold'))
        self.status_dot.place(x=246,y=54)
        self.status_text = tk.Label(self, text='Atelier en attente', fg=self.palette['MUTED'], bg=self.palette['PANEL'],
                                    font=(self.ui_fonts['display'], 7, 'bold'))
        self.status_text.place(x=75,y=56,anchor='nw')
        self._start = None
        for widget in (self.icon_label, self):
            widget.bind('<ButtonPress-1>', self._press)
            widget.bind('<B1-Motion>', self._drag)
            widget.bind('<ButtonRelease-1>', self._release)
            widget.bind('<Double-Button-1>', lambda e: self.on_open())
            widget.bind('<Button-3>', self._menu)
        self.menu = tk.Menu(self, tearoff=False)
        self.menu.add_command(label='Équipement actuel / choisir / créer', command=on_items or on_open)
        self.menu.add_command(label='Prochaine rune / stratégie', command=on_strategy or on_open)
        self.menu.add_command(label='Réussites, stratégies et sauvegarde', command=on_workbench or on_open)
        self.menu.add_command(label='Ouvrir Forgely', command=on_open)
        self.menu.add_command(label='Démarrer / arrêter l’observation', command=on_toggle)
        self.menu.add_separator()
        self.menu.add_command(label='Quitter Forgely', command=on_quit)
        self.tip = 'Clic droit : équipement · Double-clic : ouvrir · Glisser : déplacer'
        self.icon_label.configure(cursor='fleur')

    def _press(self, event):
        self._start = (event.x_root, event.y_root, self.winfo_x(), self.winfo_y())

    def _drag(self, event):
        if not self._start:
            return
        start_x, start_y, x, y = self._start
        self.geometry(f'+{max(0, x + event.x_root - start_x)}+{max(0, y + event.y_root - start_y)}')

    def _release(self, event):
        if self._start:
            moved = abs(event.x_root-self._start[0])+abs(event.y_root-self._start[1])
            if moved < 7:
                self.on_open()
        self._start = None

    def _menu(self, event):
        self.menu.tk_popup(event.x_root, event.y_root)

    def show_advice(self,rune,kind):
        try:
            path = rune_icon_path(rune or '')
            if path is not None:
                try:
                    from PIL import Image, ImageTk
                    with Image.open(path) as img:
                        self._rune_photo = ImageTk.PhotoImage(img.convert('RGBA').resize((40, 40), Image.Resampling.LANCZOS), master=self)
                    self.icon_label.configure(image=self._rune_photo, text='', padx=4)
                except (ImportError, OSError, tk.TclError):
                    self._rune_photo = None
                    self.icon_label.configure(image='', text='FM', padx=10)
            else:
                self._rune_photo = None
                self.icon_label.configure(image='', text='FM', padx=10)
            self.advice_label.configure(text=rune if rune else 'Jet à lire',
                fg=self.palette['GREEN'] if rune else self.palette['FG'])
        except tk.TclError:pass

    def set_theme(self,palette):
        """Update overlay surfaces when the appearance changes."""
        mapping={self.palette[key]:palette[key] for key in self.palette}
        self.palette=palette
        def visit(w):
            try:
                cfg=w.configure()
                updates={}
                for key in ('bg','background','fg','foreground'):
                    if key in cfg and str(w.cget(key)) in mapping:
                        updates[key]=mapping[str(w.cget(key))]
                if updates:w.configure(**updates)
            except (tk.TclError,ValueError):pass
            for c in w.winfo_children():visit(c)
        visit(self)
        if getattr(self,'_rounded_overlay',False):
            self._background.itemconfigure('all',fill=palette['PANEL'])

    def state_color(self, state):
        colors = {
            'active':'#22c55e',      # atelier détecté
            'paused':'#9ca3af',      # observateur arrêté
            'error':'#ef4444',       # atelier non détecté / erreur
            'candidate':'#E6C78B',   # lecture provisoire, à vérifier
            'waiting':'#ef4444',     # DOFUS ou atelier introuvable
            'unknown':'#f59e0b',     # analyse en attente
        }
        labels = {
            'active':'Atelier OK',
            'paused':'Arrêté',
            'error':'Atelier NON',
            'candidate':'À vérifier',
            'waiting':'Atelier NON',
            'unknown':'Analyse…',
        }
        self.status_dot.configure(fg=colors.get(state, '#9ca3af'))
        self.status_text.configure(text=labels.get(state, 'Atelier ?'), fg=colors.get(state, '#9ca3af'))
