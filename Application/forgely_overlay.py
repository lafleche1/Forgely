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
    def __init__(self, root, on_open, on_toggle, on_quit, on_items=None, on_strategy=None, on_workbench=None, on_goals=None,
                 on_reviews=None,on_perfect=None):
        super().__init__(root)
        self.title('Forgely · Copilote')
        self.root = root
        self.palette = THEMES.get(getattr(root, 'theme_name', DEFAULT), THEMES[DEFAULT])
        self.ui_fonts = font_families(root)
        self.on_open = on_open
        self.on_toggle = on_toggle
        self.manual_reviews_enabled=on_reviews is not None
        self.on_quit = on_quit
        self.review_count=0
        self.review_panel=None
        self.review_editing=False
        self.goal_editing=False
        self.goal_panel=None
        self.overrideredirect(True)
        self.wm_attributes('-topmost', True)
        self.configure(bg=self.palette['PANEL'], highlightthickness=1,
                       highlightbackground=self.palette['PANEL2'])
        self.dock_right(370,528)
        self._rounded_overlay=False
        panel=self.palette['PANEL']
        def label(text, size=10, color=None, **kw):
            return tk.Label(self, text=text, bg=panel, fg=color or self.palette['FG'],
                            font=(self.ui_fonts['body'],size), **kw)
        self.header=label('FORGELY  /  COPILOTE',10,self.palette['MUTED'],anchor='w')
        self.header.place(x=18,y=12,width=290,height=24)
        tk.Button(self,text='↗',command=on_open,bg=panel,fg=self.palette['FG'],
                  relief='flat',bd=0,cursor='hand2').place(x=327,y=10,width=28,height=28)
        self.item_label=label('Choisir un équipement',15,anchor='w',wraplength=330,justify='left')
        self.item_label.place(x=18,y=44,width=334,height=52)
        self.status_dot=label('●',11,self.palette['MUTED'])
        self.status_dot.place(x=16,y=98,width=18,height=22)
        self.status_text=label('Atelier en attente',9,self.palette['MUTED'],anchor='w')
        self.status_text.place(x=40,y=98,width=300,height=22)
        self.photo=None
        self._rune_photo=None
        self.icon_label=label('FM',14,self.palette['GREEN'])
        self.icon_label.configure(bg=self.palette['PANEL2'])
        self.icon_label.place(x=18,y=136,width=52,height=60)
        self.advice_label=label('Jet à lire',17,self.palette['GREEN'],anchor='w',justify='left',wraplength=205)
        self.advice_label.place(x=84,y=133,width=208,height=66)
        self.pool_label=label('Puits\n—',11,self.palette['MUTED'],justify='center')
        self.pool_label.place(x=298,y=139,width=54,height=54)
        self.review_button=tk.Button(self,text='Lecture à vérifier',command=on_reviews or on_open,
            bg=self.palette['PANEL2'],fg=self.palette['GOLD'],relief='flat',bd=0,cursor='hand2',
            font=(self.ui_fonts['body'],10))
        from tkinter import ttk
        self.stats_table=ttk.Treeview(self,columns=('stat','value','target','state'),show='headings',
                                    height=5,style='Forgely.Treeview',selectmode='none')
        for key,title,width in (('stat','Caractéristique',135),('value','Actuel',50),('target','Cible',50),('state','Lecture',90)):
            self.stats_table.heading(key,text=title)
            self.stats_table.column(key,width=width,minwidth=35,stretch=True,anchor='w' if key in ('stat','state') else 'center')
        self.stats_table.place(x=18,y=213,width=316,height=160)
        scroll=ttk.Scrollbar(self,orient='vertical',command=self.stats_table.yview,style='Forgely.Vertical.TScrollbar')
        scroll.place(x=334,y=213,width=18,height=160)
        self.stats_scroll=scroll
        self.stats_table.configure(yscrollcommand=scroll.set)
        self.feed_label=label('Les dernières lectures apparaîtront ici.',9,self.palette['MUTED'],
                              anchor='nw',justify='left',wraplength=330)
        self.feed_label.place(x=18,y=386,width=334,height=72)
        self.learning_label=label('Mémoire : en attente',8,self.palette['MUTED'],anchor='w')
        self.learning_label.place(x=18,y=498,width=334,height=20)
        self.action_buttons=[]
        for x,text,command in ((18,'Atelier',on_open),(132,'Observer',on_toggle),(246,'Détails',on_strategy or on_open)):
            action=tk.Button(self,text=text,command=command,bg=self.palette['PANEL2'],fg=self.palette['FG'],
                      activebackground=self.palette['BUTTON_HOVER'],activeforeground=self.palette['FG'],
                      relief='flat',bd=0,cursor='hand2',font=(self.ui_fonts['body'],10))
            action.place(x=x,y=462,width=106,height=30)
            self.action_buttons.append(action)
        self._equipment_key=None
        self._start = None
        for widget in (self.header, self.item_label, self.icon_label):
            widget.bind('<ButtonPress-1>', self._press)
            widget.bind('<B1-Motion>', self._drag)
            widget.bind('<ButtonRelease-1>', self._release)
            widget.bind('<Double-Button-1>', lambda e: self.on_open())
            widget.bind('<Button-3>', self._menu)
        self.menu = tk.Menu(self, tearoff=False)
        self.menu.add_command(label='Jet cible / jet souhaité', command=on_goals or on_open)
        if on_perfect:self.menu.add_checkbutton(label='Jet parfait',variable=root.perfect_goal_checked,command=on_perfect)
        self.menu.add_command(label='Équipement actuel / choisir / créer', command=on_items or on_open)
        self.menu.add_command(label='Prochaine rune / stratégie', command=on_strategy or on_open)
        if self.manual_reviews_enabled:
            self.menu.add_command(label='Lectures à vérifier', command=on_reviews)
        self.menu.add_command(label='Réussites, stratégies et sauvegarde', command=on_workbench or on_open)
        self.menu.add_command(label='Ouvrir Forgely', command=on_open)
        self.menu.add_command(label='Démarrer / arrêter l’observation', command=on_toggle)
        self.menu.add_separator()
        self.menu.add_command(label='Quitter Forgely', command=on_quit)
        self.tip = 'Clic droit : équipement · Double-clic : ouvrir · Glisser : déplacer'
        self.icon_label.configure(cursor='fleur')

    def sync_review(self,count):
        """Review request is conditional and always below the advice."""
        if self.goal_editing:return
        if not self.manual_reviews_enabled:
            count=0
            if self.review_editing:
                self.review_editing=False
                if self.review_panel is not None:self.review_panel.place_forget()
        previous=bool(self.review_count)
        self.review_count=max(0,int(count))
        self.review_button.configure(text=f'Lecture à vérifier · {self.review_count}')
        if (previous and not self.review_count and self.review_editing and
                not self.review_panel.show_confirmed.get()):
            self.close_review()
        if self.review_editing:
            return
        offset=34 if self.review_count else 0
        if self.review_count:self.review_button.place(x=18,y=204,width=334,height=28)
        else:self.review_button.place_forget()
        self.stats_table.place(x=18,y=213+offset,width=316,height=160)
        self.stats_scroll.place(x=334,y=213+offset,width=18,height=160)
        self.feed_label.place(x=18,y=386+offset,width=334,height=72)
        for button in self.action_buttons:button.place_configure(y=462+offset)
        self.learning_label.place_configure(y=498+offset)
        if previous!=bool(self.review_count) or self.winfo_width()>400:
            self.geometry(f'370x{528+offset}')

    def open_review(self,store,on_done):
        if not self.manual_reviews_enabled:
            self.sync_review(0)
            return
        from forgely_review_panel import ReviewPanel
        if self.review_panel is not None:self.review_panel.destroy()
        self.review_editing=True
        self.review_button.place_forget()
        self.stats_table.place_forget();self.stats_scroll.place_forget();self.feed_label.place_forget()
        self.review_panel=ReviewPanel(self,store,on_done,self.close_review,self.palette)
        self.review_panel.place(x=18,y=210,width=534,height=350)
        for button in self.action_buttons:button.place_configure(y=574)
        self.learning_label.place_configure(y=614)
        self.geometry('570x640')

    def close_review(self):
        self.review_editing=False
        if self.review_panel is not None:self.review_panel.place_forget()
        self.geometry(f'370x{544 if self.review_count else 510}')
        self.sync_review(self.review_count)

    def sync_equipment(self, item, rows, amount, activity):
        """Display only the main dashboard's current, qualified readings."""
        self.item_label.configure(text=item or 'Choisir un équipement')
        self.pool_label.configure(text='Puits\n'+amount)
        key=tuple(rows)
        if key != self._equipment_key:
            self._equipment_key=key
            self.stats_table.delete(*self.stats_table.get_children())
            for stat,value,target,state,tag in rows:
                self.stats_table.insert('', 'end', values=(stat,value,target,state), tags=(tag,))
            for tag,color in (('success',self.palette['GREEN']),('pending',self.palette['GOLD']),('unknown',self.palette['MUTED'])):
                self.stats_table.tag_configure(tag,foreground=color)
        self.feed_label.configure(text=getattr(self,'_prediction','') or '\n'.join(entry[:65] for entry in activity[:3]) or 'Les dernières lectures apparaîtront ici.')

    def show_prediction(self,text):
        self._prediction=text
        self.feed_label.configure(text=text)

    def open_targets(self,jet,targets,on_save,on_perfect=None):
        from forgely_live_targets import LiveTargets
        if self.goal_panel is not None:self.goal_panel.destroy()
        self.close_review()
        self.goal_editing=True
        self.stats_table.place_forget();self.stats_scroll.place_forget();self.feed_label.place_forget()
        self.goal_panel=LiveTargets(self,jet,targets,on_save,self.close_targets,self.palette,on_perfect=on_perfect)
        self.goal_panel.place(x=18,y=210,width=494,height=350)
        for button in self.action_buttons:button.place_configure(y=574)
        self.learning_label.place_configure(y=614)
        self.dock_right(530,640)

    def close_targets(self):
        self.goal_editing=False
        if self.goal_panel is not None:self.goal_panel.place_forget()
        self.dock_right(370,528)
        self.sync_review(0)

    def dock_right(self,width,height):
        x=max(0,self.winfo_screenwidth()-width-20)
        y=max(0,min(110,self.winfo_screenheight()-height-40))
        self.geometry(f'{width}x{height}+{x}+{y}')

    def show_learning(self,text):
        self.learning_label.configure(text=text,fg=self.palette['GREEN'])

    def _press(self, event):
        self._start = (event.x_root, event.y_root, self.winfo_x(), self.winfo_y())

    def _drag(self, event):
        if not self._start:
            return
        start_x, start_y, x, y = self._start
        self.geometry(f'+{max(0, x + event.x_root - start_x)}+{max(0, y + event.y_root - start_y)}')

    def _release(self, event):
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
        if state in ('waiting','paused','error'):
            self._prediction=''
            self.feed_label.configure(text='Lecture suspendue · aucun scénario actuel')
            self.advice_label.configure(text='Lecture suspendue')
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
