"""Three-step native equipment picker. Selection is committed only with targets."""
import math
import tkinter as tk
from tkinter import ttk,messagebox
from PIL import Image,ImageTk
from forgely_equipment_catalog import EquipmentCatalog,CATEGORIES,target_values,equipment_bounds
from forgely_plan import STATS
from forgely_tools import natural_bounds


class EquipmentPicker(tk.Toplevel):
    PAGE_SIZE=6

    def __init__(self,app,palette,on_commit,selected_id=None,goals_only=False,lock_equipment=False,floating=False):
        super().__init__(app)
        self.app=app;self.p=palette;self.on_commit=on_commit
        self.lock_equipment=lock_equipment
        self.catalog=EquipmentCatalog();self.photos={};self.page=0
        self.selected=self.catalog.get(selected_id) if selected_id else None
        self.category=tk.StringVar(value=self.selected.category if self.selected else '')
        self.query=tk.StringVar();self.fields={};self.pending_search=None
        self.title('Forgely — Mon équipement et mon jet souhaité')
        width=min(1080,self.winfo_screenwidth()-70);height=min(760,self.winfo_screenheight()-100)
        if floating:
            width=min(680,self.winfo_screenwidth()-40)
            height=min(640,self.winfo_screenheight()-70)
        self.geometry(f'{width}x{height}');self.minsize(min(780,width),min(580,height))
        self.configure(bg=self.p['BG']);self.transient(app)
        if floating:
            badge=app.overlay
            self.transient(badge)
            self.attributes('-topmost',True)
            x=badge.winfo_x()+badge.winfo_width()+10
            if x+width>self.winfo_screenwidth()-15:
                x=badge.winfo_x()-width-10
            x=max(15,min(x,self.winfo_screenwidth()-width-15))
            y=max(15,min(badge.winfo_y(),self.winfo_screenheight()-height-40))
            self.geometry(f'{width}x{height}+{x}+{y}')
        self.protocol('WM_DELETE_WINDOW',self.close)
        self.heading=self.label(self,'Quel objet veux-tu travailler ?',24,bold=True)
        self.heading.pack(anchor='w',padx=24,pady=(20,4))
        self.steps=self.label(self,'1  Type d’équipement   →   2  Choisir l’objet   →   3  Jet souhaité',10,color=self.p['GOLD'])
        self.steps.pack(anchor='w',padx=24,pady=(0,16))
        if self.lock_equipment:
            self.steps.configure(text='Objet détecté automatiquement · Définir le jet cible')
        self.body=tk.Frame(self,bg=self.p['BG'])
        self.footer=tk.Frame(self,bg=self.p['PANEL']);self.footer.pack(side='bottom',fill='x',padx=24,pady=(12,20))
        self.body.pack(fill='both',expand=True,padx=24)
        self.query.trace_add('write',self.schedule_search)
        if goals_only and self.selected:self.show_goals()
        else:self.show_catalogue()

    def label(self,parent,text,size=11,bold=False,color=None,**kw):
        return tk.Label(parent,text=text,font=(self.app.ui_fonts['body'],size,'bold' if bold else 'normal'),
            bg=parent.cget('bg'),fg=color or self.p['FG'],**kw)

    def button(self,parent,text,command,primary=False,**kw):
        return tk.Button(parent,text=text,command=command,font=(self.app.ui_fonts['body'],10),
            bg=self.p['ACCENT'] if primary else self.p['PANEL2'],fg=self.p['BUTTON_FG'] if primary else self.p['FG'],
            activebackground=self.p['HOVER'],activeforeground=self.p['BUTTON_FG'],relief='flat',bd=0,
            padx=12,pady=9,cursor='hand2',**kw)

    def clear(self):
        if self.pending_search is not None:
            self.after_cancel(self.pending_search);self.pending_search=None
        for parent in (self.body,self.footer):
            for child in parent.winfo_children():child.destroy()

    def photo(self,item,size=66):
        key=(item.icon_id,size)
        if key not in self.photos:
            path=self.catalog.icon_path(item)
            if not path:return None
            try:
                with Image.open(path) as im:
                    im=im.convert('RGBA');im.thumbnail((size,size),Image.Resampling.LANCZOS)
                    self.photos[key]=ImageTk.PhotoImage(im,master=self)
            except (OSError,ValueError):return None
        return self.photos.get(key)

    def show_catalogue(self):
        if self.lock_equipment:return
        self.clear();self.stage='catalogue';self.heading.configure(text='Quel objet veux-tu travailler ?')
        cats=tk.Frame(self.body,bg=self.p['BG']);cats.pack(fill='x',pady=(0,13))
        self.category_buttons={}
        for i,name in enumerate(CATEGORIES):
            cats.columnconfigure(i,weight=1,uniform='category')
            b=self.button(cats,name,lambda n=name:self.choose_category(n))
            b.grid(row=0,column=i,sticky='ew',padx=(0,5),pady=2);self.category_buttons[name]=b
        row=tk.Frame(self.body,bg=self.p['BG']);row.pack(fill='x',pady=(0,12))
        self.section=self.label(row,'Choisis un type d’équipement',15,bold=True);self.section.pack(side='left')
        self.search=tk.Entry(row,textvariable=self.query,bg=self.p['PANEL2'],fg=self.p['FG'],
            insertbackground=self.p['FG'],font=(self.app.ui_fonts['body'],11),relief='flat',width=27)
        self.search.pack(side='right',ipady=9)
        self.label(row,'Rechercher',10,color=self.p['MUTED']).pack(side='right',padx=8)
        self.grid_frame=tk.Frame(self.body,bg=self.p['BG']);self.grid_frame.pack(fill='both',expand=True)
        self.pagination=tk.Frame(self.body,bg=self.p['BG']);self.pagination.pack(fill='x',pady=(8,0))
        self.previous=self.button(self.pagination,'← Précédent',lambda:self.move_page(-1));self.previous.pack(side='left')
        self.page_label=self.label(self.pagination,'',10,color=self.p['MUTED']);self.page_label.pack(side='left',expand=True)
        self.next=self.button(self.pagination,'Suivant →',lambda:self.move_page(1));self.next.pack(side='right')
        self.selection_label=self.label(self.footer,'Aucun objet sélectionné',12,bold=True,anchor='w',wraplength=450)
        self.selection_label.pack(side='left',padx=15,pady=14)
        self.continue_button=self.button(self.footer,'Définir mon jet souhaité →',self.show_goals,True)
        self.continue_button.pack(side='right',padx=15,pady=12)
        self.render_items()

    def choose_category(self,name):
        self.category.set(name);self.page=0;self.query.set('');self.render_items()

    def schedule_search(self,*_):
        if getattr(self,'stage',None)!='catalogue':return
        if self.pending_search is not None:self.after_cancel(self.pending_search)
        self.pending_search=self.after(120,self.search_changed)

    def search_changed(self):
        self.pending_search=None;self.page=0;self.render_items()

    def move_page(self,delta):
        self.page+=delta;self.render_items()

    def choose(self,item):
        self.selected=item;self.render_items()

    def render_items(self):
        if self.stage!='catalogue':return
        category=self.category.get()
        for name,b in self.category_buttons.items():
            b.configure(bg=self.p['ACCENT'] if name==category else self.p['PANEL2'],
                        fg=self.p['BUTTON_FG'] if name==category else self.p['FG'])
        self.section.configure(text=category or 'Choisis un type d’équipement')
        for child in self.grid_frame.winfo_children():child.destroy()
        rows=self.catalog.search(category,self.query.get()) if category else []
        pages=max(1,math.ceil(len(rows)/self.PAGE_SIZE));self.page=max(0,min(self.page,pages-1))
        for col in range(3):self.grid_frame.columnconfigure(col,weight=1,uniform='items')
        for row in range(2):self.grid_frame.rowconfigure(row,weight=1,uniform='items')
        for i,item in enumerate(rows[self.page*self.PAGE_SIZE:(self.page+1)*self.PAGE_SIZE]):
            selected=self.selected==item;photo=self.photo(item)
            text=item.name+'\nNiv. '+str(item.level)+(f' · #{item.item_id}' if item.ambiguous_name else '')
            if not photo:text='Image indisponible\n'+text
            b=self.button(self.grid_frame,text,lambda x=item:self.choose(x),False,
                image=photo or '',compound='top',wraplength=230,
                highlightthickness=2,highlightbackground=self.p['ACCENT'] if selected else self.p['PANEL2'])
            b.configure(bg=self.p['PANEL2'] if selected else self.p['PANEL'])
            b.grid(row=i//3,column=i%3,sticky='nsew',padx=(0,8),pady=(0,8))
        if not rows:
            self.label(self.grid_frame,'Aucun objet ne correspond à ta recherche.' if category else
                'Sélectionne une catégorie pour afficher les équipements.',12,color=self.p['MUTED']).grid(row=0,column=0,columnspan=3)
        self.previous.configure(state='normal' if self.page else 'disabled')
        self.next.configure(state='normal' if self.page+1<pages else 'disabled')
        self.page_label.configure(text=f'{len(rows)} équipements · Page {self.page+1} / {pages}' if category else '')
        self.selection_label.configure(text=self.selected.name if self.selected else 'Aucun objet sélectionné')
        self.continue_button.configure(state='normal' if self.selected and self.selected.category==category else 'disabled')

    def show_goals(self):
        if not self.selected:return
        self.clear();self.stage='goals';self.fields={}
        self.heading.configure(text='Quel jet souhaites-tu obtenir ?')
        self.label(self.body,self.selected.name+'  ·  '+self.selected.category,15,bold=True,color=self.p['GOLD']).pack(anchor='w',pady=(0,5))
        self.label(self.body,'Renseigne les valeurs visées. Laisse une case vide pour ignorer cette caractéristique.',10,
                   color=self.p['MUTED'],wraplength=850,justify='left').pack(anchor='w',pady=(0,8))
        self.bounds=equipment_bounds(self.selected)
        self.bounds.update(natural_bounds(self.selected.identity_name))
        self.label(self.body,'Les jets actuels seront lus dans DOFUS.' if self.bounds else
                   'Bornes naturelles indisponibles : saisis tes objectifs ci-dessous. Les jets actuels seront lus dans DOFUS.',10,
                   color=self.p['MUTED'],wraplength=850,justify='left').pack(anchor='w',pady=(0,10))
        controls=tk.Frame(self.body,bg=self.p['BG']);controls.pack(fill='x',pady=(0,8))
        self.extra=tk.StringVar(value=next(iter(STATS)))
        ttk.Combobox(controls,textvariable=self.extra,values=list(STATS),state='readonly',width=24).pack(side='left')
        self.button(controls,'Ajouter une caractéristique',lambda:self.add_field(self.extra.get())).pack(side='left',padx=8)
        self.perfect=tk.BooleanVar(value=False)
        if self.bounds:
            tk.Checkbutton(controls,text='Jet parfait',variable=self.perfect,
                           command=lambda:self.fill_maximum() if self.perfect.get() else None,
                           bg=self.p['BG'],fg=self.p['FG'],selectcolor=self.p['PANEL']).pack(side='right')
        header=tk.Frame(self.body,bg=self.p['PANEL2']);header.pack(fill='x')
        for col,title in enumerate(('Caractéristique','Min naturel','Max naturel','Jet souhaité')):
            header.columnconfigure(col,weight=3 if col==0 else 2,uniform='goals')
            self.label(header,title,10,bold=True,width=1,anchor='w').grid(row=0,column=col,sticky='ew',padx=7,pady=9)
        holder=tk.Frame(self.body,bg=self.p['PANEL']);holder.pack(fill='both',expand=True)
        self.canvas=tk.Canvas(holder,bg=self.p['PANEL'],highlightthickness=0)
        scroll=ttk.Scrollbar(holder,orient='vertical',command=self.canvas.yview)
        self.inside=tk.Frame(self.canvas,bg=self.p['PANEL'])
        self.inner_id=self.canvas.create_window((0,0),window=self.inside,anchor='nw')
        self.inside.bind('<Configure>',lambda _:self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>',lambda e:self.canvas.itemconfigure(self.inner_id,width=e.width))
        self.canvas.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');self.canvas.pack(side='left',fill='both',expand=True)
        self.canvas.bind('<MouseWheel>',lambda e:self.canvas.yview_scroll(-int(e.delta/120),'units'))
        from forgely_items import key_for
        previous=(self.app.plan or {}).get('stats',{}) if key_for((self.app.plan or {}).get('item',''))==key_for(self.selected.identity_name) else {}
        stats=list(dict.fromkeys([*self.bounds,*previous])) or list(STATS)
        for stat in stats:
            if stat in STATS:self.add_field(stat,previous.get(stat,{}).get('target'))
        if not self.lock_equipment:
            self.button(self.footer,'← Changer d’objet',self.show_catalogue).pack(side='left',padx=12,pady=12)
        self.button(self.footer,'Enregistrer le jet souhaité',lambda:self.commit(False)).pack(side='right',padx=12,pady=12)
        self.button(self.footer,'Enregistrer et continuer' if self.lock_equipment else 'Démarrer la session',lambda:self.commit(True),True).pack(side='right',pady=12)

    def add_field(self,stat,value=None):
        if stat in self.fields:return
        row=tk.Frame(self.inside,bg=self.p['PANEL']);row.pack(fill='x',padx=7,pady=5)
        bounds=self.bounds.get(stat)
        texts=(stat,str(bounds[0]) if bounds else '—',str(bounds[1]) if bounds else '—')
        for col in range(4):row.columnconfigure(col,weight=3 if col==0 else 2,uniform='goals')
        for col,text in enumerate(texts):
            self.label(row,text,10,width=1,anchor='w').grid(row=0,column=col,sticky='ew',padx=7)
        var=tk.StringVar(value='' if value is None else str(value));self.fields[stat]=var
        entry=tk.Entry(row,textvariable=var,width=1,bg=self.p['PANEL2'],fg=self.p['FG'],insertbackground=self.p['FG'],
                       font=(self.app.ui_fonts['body'],11),relief='flat',justify='center')
        entry.grid(row=0,column=3,sticky='ew',padx=7,ipady=7)

    def fill_maximum(self):
        for value in self.fields.values():value.set('')
        for stat,bounds in self.bounds.items():
            maximum=max(bounds)
            if stat in STATS:
                self.add_field(stat);self.fields[stat].set(str(maximum))

    def commit(self,start):
        try:
            values=target_values({stat:var.get() for stat,var in self.fields.items()})
            self.on_commit(self.selected,values,start)
        except (ValueError,OSError) as exc:
            messagebox.showerror('Jet souhaité',str(exc),parent=self);return
        self.close()

    def close(self):
        if self.pending_search is not None:self.after_cancel(self.pending_search)
        self.destroy()
