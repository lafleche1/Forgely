"""Tk video workspace. Workers never call Tk; all processing stays on the PC."""
from copy import deepcopy
import json
import math
from pathlib import Path
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser

from forgely_video_analysis import DEFAULT_ZONES, analyze_video, frame_at, validate_zones, video_info
from forgely_video_store import VideoStore, atomic_json, now, qualify_event, transfer_session, catalogue, item_profile
from forgely_video_report import write_report

ZONE_NAMES={'item':'Objet', 'jet':'Caractéristiques', 'rune':'Rune utilisée', 'history':'Journal des tentatives', 'pool':'Puits / reliquat'}


def snapshot_from_fields(fields,pool):
    jet={}
    for stat,text in fields.items():
        if not str(text).strip():continue
        try:value=float(str(text).strip().replace(',','.'))
        except ValueError:raise ValueError('Valeur invalide pour '+stat) from None
        if not math.isfinite(value) or value!=int(value) or abs(value)>30000:
            raise ValueError('Indique un entier observé pour '+stat)
        jet[stat]=int(value)
    text=str(pool).strip()
    value=float(text.replace(',','.')) if text else None
    if value is not None and (not math.isfinite(value) or not 0<=value<=30000):
        raise ValueError('Puits invalide ; laisse vide s’il est inconnu.')
    return {'jet':jet,'pool':value}


class VideoPanel(ttk.Frame):
    def __init__(self, parent, output_root):
        super().__init__(parent, padding=8)
        self.output_root=Path(output_root)/'Videos'
        self.store=VideoStore(self.output_root)
        self.zones=deepcopy(DEFAULT_ZONES)
        try:
            saved=json.loads((self.output_root/'disposition.json').read_text(encoding='utf-8'))
            validate_zones(saved); self.zones=saved
        except (OSError,ValueError,TypeError): pass
        self.entries=[{'path':s['path'],'session':s} for s in self.store.sessions()]
        self.session=None; self.current=None; self.image=None; self.photo=None
        self.item_override=None
        self.busy=False; self.cancel=threading.Event(); self.messages=queue.Queue()
        self.close_callback=None; self.closed=False; self.worker=None
        self.status=tk.StringVar(value='Importe tes MP4. Analyse des images uniquement, sans audio.')
        self.file_value=tk.StringVar(); self.zone_value=tk.StringVar(value=ZONE_NAMES['item'])
        self.position=tk.DoubleVar(value=0)
        self.side=tk.StringVar(value='after'); self.selected_event=None
        self._build()
        self.refresh_files()
        self.poll_id=self.after(100,self.poll)

    def _build(self):
        ttk.Label(self,text='Apprendre de sessions réelles',font=('Segoe UI',14,'bold')).pack(anchor='w')
        ttk.Label(self,text='Images uniquement · résultats par objet · les lectures ambiguës restent à vérifier.').pack(anchor='w',pady=(2,6))
        top=ttk.Frame(self); top.pack(fill='x')
        self.file_box=ttk.Combobox(top,textvariable=self.file_value,state='readonly')
        self.file_box.pack(side='left',fill='x',expand=True)
        self.file_box.bind('<<ComboboxSelected>>',self.select_file)
        self.add_button=ttk.Button(top,text='Ajouter des MP4',command=self.add_files)
        self.add_button.pack(side='left',padx=(6,0))
        tools=ttk.Frame(self);tools.pack(fill='x',pady=6)
        self.start_button=ttk.Button(tools,text='Analyser / reprendre',command=self.start)
        self.start_button.pack(side='left')
        self.stop_button=ttk.Button(tools,text='Arrêter et sauvegarder',command=self.stop,state='disabled')
        self.stop_button.pack(side='left',padx=6)
        self.report_button=ttk.Button(tools,text='Rapport',command=self.open_report)
        self.report_button.pack(side='left')
        self.transfer_button=ttk.Button(tools,text='Transmettre à Forgely',command=self.transfer)
        self.transfer_button.pack(side='right')
        identity=ttk.Frame(self);identity.pack(fill='x',pady=(0,4))
        self.identity_label=ttk.Label(identity,text='Objet : détection automatique')
        self.identity_label.pack(side='left')
        self.identity_button=ttk.Button(identity,text='Confirmer un objet illisible',command=self.choose_identity)
        self.identity_button.pack(side='right')
        main=ttk.Panedwindow(self,orient='horizontal');main.pack(fill='both',expand=True)
        preview=ttk.Frame(main);events=ttk.Frame(main)
        main.add(preview,weight=3);main.add(events,weight=2)
        zones=ttk.Frame(preview);zones.pack(fill='x')
        ttk.Label(zones,text='Zone à tracer :').pack(side='left')
        self.zone_box=ttk.Combobox(zones,textvariable=self.zone_value,values=list(ZONE_NAMES.values()),state='readonly',width=20)
        self.zone_box.pack(side='left',padx=4)
        self.zone_box.bind('<<ComboboxSelected>>',lambda e:self.render())
        ttk.Button(zones,text='Mémoriser',command=self.save_layout).pack(side='left')
        self.preview=tk.Canvas(preview,background='#202331',highlightthickness=0,width=500,height=280)
        self.preview.pack(fill='both',expand=True,pady=4)
        self.preview.bind('<Configure>',lambda e:self.render())
        self.preview.bind('<ButtonPress-1>',self.drag_start)
        self.preview.bind('<B1-Motion>',self.drag_move)
        self.preview.bind('<ButtonRelease-1>',self.drag_end)
        self.seek=ttk.Scale(preview,from_=0,to=1,variable=self.position)
        self.seek.pack(fill='x');self.seek.bind('<ButtonRelease-1>',lambda e:self.show_position())
        self.time_label=ttk.Label(preview,text='0:00');self.time_label.pack(anchor='w')
        before_after=ttk.Frame(preview);before_after.pack(fill='x')
        for value,label in [('before','Avant la tentative'),('after','Après la tentative')]:
            ttk.Radiobutton(before_after,text=label,variable=self.side,value=value,command=self.show_evidence).pack(side='left')
        ttk.Label(preview,text='Trace les 5 zones sur l’aperçu si la disposition diffère.\nLe journal doit montrer les nouvelles lignes et leur décalage.',wraplength=470).pack(anchor='w',pady=4)
        ttk.Label(events,text='Tentatives repérées').pack(anchor='w')
        table=ttk.Frame(events);table.pack(fill='both',expand=True)
        self.tree=ttk.Treeview(table,columns=('time','rune','result','quality'),show='headings',height=10,selectmode='browse')
        for key,label,width in [('time','Temps',52),('rune','Rune',65),('result','Résultat',55),('quality','Lecture',100)]:
            self.tree.heading(key,text=label);self.tree.column(key,width=width,minwidth=40)
        scroll=ttk.Scrollbar(table,orient='vertical',command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');self.tree.pack(fill='both',expand=True)
        self.tree.bind('<<TreeviewSelect>>',self.select_event)
        self.detail=tk.Text(events,height=5,wrap='word',font=('Segoe UI',9),state='disabled')
        self.detail.pack(fill='x',pady=4)
        edits=ttk.Frame(events);edits.pack(fill='x')
        self.review_button=ttk.Button(edits,text='Vérifier / corriger',command=self.review)
        self.review_button.pack(side='left')
        self.reject_button=ttk.Button(edits,text='Rejeter',command=self.reject)
        self.reject_button.pack(side='left',padx=6)
        self.progress=ttk.Progressbar(self,mode='determinate');self.progress.pack(fill='x',pady=(6,3))
        ttk.Label(self,textvariable=self.status,wraplength=920).pack(anchor='w')

    def refresh_files(self):
        labels=[f'{i+1}. {Path(e["path"]).name} — {e.get("session",{}).get("status","à analyser")}' for i,e in enumerate(self.entries)]
        self.file_box.configure(values=labels)
        if self.current is not None and self.current<len(labels):self.file_value.set(labels[self.current])
        self.update_controls()

    def add_files(self):
        if self.busy:return
        paths=filedialog.askopenfilenames(parent=self,
                 title='Sessions réelles de forgemagie',filetypes=[('Vidéos MP4','*.mp4')])
        self.add_paths(paths)

    def add_paths(self,paths):
        for path in paths:
            path=str(Path(path).resolve())
            if not any(e['path']==path for e in self.entries):self.entries.append({'path':path})
        self.refresh_files()
        if paths:
            self.current=len(self.entries)-1
            self.file_box.current(self.current);self.select_file()

    def select_file(self,event=None):
        if self.busy:return
        index=self.file_box.current()
        if index<0:return
        self.current=index;entry=self.entries[index];self.session=entry.get('session')
        self.item_override=(self.session or {}).get('config',{}).get('item_override')
        self.update_identity_label()
        if self.session:self.zones=deepcopy(self.session.get('config',{}).get('zones',self.zones))
        self.position.set(0);self.selected_event=None
        try:
            info=video_info(entry['path']);self.seek.configure(to=max(0,info['duration']-.1))
            self.status.set(f'{info["duration"]:.1f} s · {info["width"]} × {info["height"]} · règle les zones puis lance l’analyse.')
            self.show_position()
        except (OSError,ValueError) as exc:self.status.set(str(exc));self.image=None;self.render()
        self.populate_events();self.update_controls()

    def show_position(self):
        if self.current is None:return
        try:
            self.image=frame_at(self.entries[self.current]['path'],self.position.get());self.render()
            value=self.position.get();self.time_label.configure(text=f'{int(value)//60}:{value%60:04.1f}')
        except (ValueError,OSError) as exc:self.status.set(str(exc))

    def render(self):
        from PIL import ImageTk,ImageOps
        self.preview.delete('all')
        if self.image is None:return
        width=max(2,self.preview.winfo_width());height=max(2,self.preview.winfo_height())
        image=ImageOps.contain(self.image,(width,height))
        x=(width-image.width)//2;y=(height-image.height)//2
        self.display_box=(x,y,image.width,image.height)
        self.photo=ImageTk.PhotoImage(image,master=self.preview)
        self.preview.create_image(x,y,anchor='nw',image=self.photo)
        selected=next(k for k,v in ZONE_NAMES.items() if v==self.zone_value.get())
        for name,box in self.zones.items():
            a,b,c,d=box;active=name==selected
            self.preview.create_rectangle(x+a*image.width,y+b*image.height,x+c*image.width,y+d*image.height,
                                          outline='#ffe080' if active else '#8cddff',width=2 if active else 1)
            if active:self.preview.create_text(x+a*image.width+3,y+b*image.height+2,anchor='nw',text=ZONE_NAMES[name],fill='#ffe080')

    @staticmethod
    def relative_box(start,end,display_box):
        x,y,w,h=display_box
        x1,x2=sorted((min(1,max(0,(start[0]-x)/w)),min(1,max(0,(end[0]-x)/w))))
        y1,y2=sorted((min(1,max(0,(start[1]-y)/h)),min(1,max(0,(end[1]-y)/h))))
        return (x1,y1,x2,y2)

    def drag_start(self,event):
        if not self.busy and self.image is not None:self.drag_origin=(event.x,event.y)

    def drag_move(self,event):
        if not hasattr(self,'drag_origin'):return
        self.preview.delete('drag')
        self.preview.create_rectangle(*self.drag_origin,event.x,event.y,outline='white',width=2,tags='drag')

    def drag_end(self,event):
        if not hasattr(self,'drag_origin'):return
        box=self.relative_box(self.drag_origin,(event.x,event.y),self.display_box);del self.drag_origin
        if box[2]-box[0]>.005 and box[3]-box[1]>.005:
            name=next(k for k,v in ZONE_NAMES.items() if v==self.zone_value.get())
            self.zones[name]=box
            self.status.set(f'Zone « {ZONE_NAMES[name]} » réglée. Mémoriser pour les prochaines vidéos.')
        self.render()

    def save_layout(self):
        validate_zones(self.zones);atomic_json(self.output_root/'disposition.json',self.zones)
        self.status.set('Disposition mémorisée pour les prochaines vidéos.')

    def update_identity_label(self):
        item,_=item_profile(self.item_override)
        self.identity_label.configure(text='Objet : '+(item.identity_name+' (confirmé)' if item else 'détection automatique'))

    def choose_identity(self):
        if self.busy:return
        dialog=tk.Toplevel(self);dialog.title('Confirmer l’objet de la vidéo');dialog.transient(self.winfo_toplevel())
        frame=ttk.Frame(dialog,padding=14);frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='À utiliser seulement si les passages au nom illisible concernent tous cet objet.\nLes caractéristiques manquantes ne seront pas complétées.',wraplength=600).pack(anchor='w')
        labels={'Détection automatique':None,**{f'{i.identity_name} · {i.item_id}':i.item_id for i in catalogue().items}}
        value=tk.StringVar(value=next(k for k,v in labels.items() if v==self.item_override))
        ttk.Combobox(frame,textvariable=value,values=list(labels),width=65).pack(fill='x',pady=8)
        def save():
            if value.get() not in labels:return
            self.item_override=labels[value.get()];self.update_identity_label();dialog.destroy()
        ttk.Button(frame,text='Confirmer pour cette vidéo',command=save).pack(anchor='e')

    def update_controls(self):
        for widget in (self.add_button,self.file_box,self.zone_box,self.start_button,self.report_button,
                       self.transfer_button,self.review_button,self.reject_button,self.identity_button):
            widget.configure(state='disabled' if self.busy else ('readonly' if widget in (self.file_box,self.zone_box) else 'normal'))
        self.stop_button.configure(state='normal' if self.busy else 'disabled')
        if not self.busy:
            if self.current is None:self.start_button.configure(state='disabled')
            if not self.session:
                for w in (self.report_button,self.transfer_button,self.review_button,self.reject_button):w.configure(state='disabled')

    def start(self):
        if self.busy or self.current is None:return
        path=self.entries[self.current]['path'];zones=deepcopy(self.zones);item_override=self.item_override
        try:validate_zones(zones)
        except ValueError as exc:messagebox.showerror('Zones à corriger',str(exc),parent=self);return
        self.busy=True;self.cancel.clear();self.update_controls()
        self.status.set('Préparation du MP4… aucune analyse audio.');self.progress.configure(value=0)
        def work():
            last=[0.]
            def progress(info):
                value=time.monotonic()
                if value-last[0]>.15:self.messages.put(('progress',info));last[0]=value
            try:
                session=analyze_video(path,self.store,zones,self.cancel,progress,item_override=item_override)
                if session.get('id'):write_report(session,self.store.folder(session['id']))
                self.messages.put(('done',session))
            except Exception as exc:self.messages.put(('error',str(exc)))
        self.worker=threading.Thread(target=work,name='Forgely-Video',daemon=True);self.worker.start()

    def stop(self):
        self.cancel.set();self.status.set('Arrêt demandé. Sauvegarde des observations et de la reprise…')

    def poll(self):
        if self.closed:return
        try:
            for _ in range(30):
                kind,data=self.messages.get_nowait()
                if kind=='progress':
                    self.progress.configure(maximum=max(1,data['duration']),value=data['time'])
                    self.status.set(('Identification du fichier…' if data['phase']=='hash' else
                                     f'Analyse visuelle : {data["time"]:.1f} / {data["duration"]:.1f} s · {data.get("events",0)} tentatives candidates'))
                else:
                    self.busy=False
                    if kind=='done' and data.get('id'):
                        self.session=data;self.entries[self.current]['session']=data
                        count=sum(qualify_event(e)['eligible'] for e in data['events'])
                        self.status.set(f'{"Analyse sauvegardée, reprise possible" if data["status"]=="paused" else "Analyse terminée"} : {len(data["events"])} candidats, {count} admissibles. Consulte le rapport et les lectures ambiguës.')
                        self.populate_events();self.refresh_files()
                    elif kind=='error':
                        self.status.set('Analyse interrompue : '+data)
                        if not self.close_callback:messagebox.showerror('Analyse vidéo',data,parent=self)
                    else:self.status.set('Arrêt avant le début de l’analyse. Tu peux relancer.')
                    self.update_controls()
                    if self.close_callback:
                        callback=self.close_callback;self.shutdown();callback();return
        except queue.Empty:pass
        self.poll_id=self.after(100,self.poll)

    def populate_events(self):
        self.tree.delete(*self.tree.get_children())
        for event in (self.session or {}).get('events',[]):
            q=qualify_event(event)
            label='Rejeté' if event.get('status')=='rejected' else ('Confirmé' if q['eligible'] and event.get('status')=='confirmed' else 'Cohérent' if q['eligible'] else 'À vérifier')
            self.tree.insert('', 'end',iid=event['id'],values=(f'{event.get("time",0):.1f}s',event.get('rune') or '?',event.get('outcome') or '?',label))

    def current_event(self):
        ids=self.tree.selection()
        return next((e for e in (self.session or {}).get('events',[]) if ids and e['id']==ids[0]),None)

    def select_event(self,event=None):
        selected=self.current_event()
        if selected is None:return
        self.selected_event=selected['id'];q=qualify_event(selected)
        text=f'{q["item"] or "Objet inconnu"}\n'+ ('Comptabilité cohérente. ' if q['eligible'] else '\n'.join(q['reasons']))
        self.detail.configure(state='normal');self.detail.delete('1.0','end');self.detail.insert('1.0',text);self.detail.configure(state='disabled')
        self.show_evidence()

    def show_evidence(self):
        event=self.current_event()
        if not event:return
        from PIL import Image
        relative=event.get('evidence',{}).get(self.side.get())
        folder=self.store.folder(self.session['id']).resolve()
        if relative:
            path=(folder/relative).resolve()
            if path.is_relative_to(folder) and path.is_file():
                with Image.open(path) as im:self.image=im.copy()
                self.position.set(event.get(self.side.get()+'_time') or event.get('time',0))
                self.time_label.configure(text=f'{self.position.get():.2f} s · {"avant" if self.side.get()=="before" else "après"}')
                self.render();return
        self.position.set(event.get('time',0));self.show_position()

    def apply_review(self,event_id,changes):
        if self.busy:raise ValueError('Attends la fin ou l’arrêt de l’analyse.')
        event=next(e for e in self.session['events'] if e['id']==event_id)
        event.update(deepcopy(changes),reviewed_at=now())
        if changes.get('status')=='confirmed' and changes.get('rune'):
            event['issues']=[issue for issue in event.get('issues',[]) if issue!='ambiguous_rune']
        self.store.save_session(self.session);self.populate_events()
        self.status.set('Correction sauvegardée. Transmets à nouveau pour actualiser les observations de Forgely.')

    def reject(self):
        event=self.current_event()
        if event:self.apply_review(event['id'],{'status':'rejected','review_note':'Rejet manuel'})

    def review(self):
        event=self.current_event()
        if not event:return
        dialog=tk.Toplevel(self);dialog.title('Vérifier une tentative réelle');dialog.geometry('780x620')
        dialog.transient(self.winfo_toplevel())
        outer=ttk.Frame(dialog,padding=12);outer.pack(fill='both',expand=True)
        labels={f'{i.identity_name} · {i.item_id}':i.item_id for i in catalogue().items}
        item=tk.StringVar(value=next((label for label,ident in labels.items() if ident==event.get('item_id')),''))
        from forgely_dofocus import RUNE_REFERENCES
        rune=tk.StringVar(value=event.get('rune') or '');outcome=tk.StringVar(value=event.get('outcome') or '')
        for label,var,values in [('Objet',item,list(labels)),('Rune',rune,sorted(RUNE_REFERENCES)),('Résultat',outcome,['SC','SN','EC'])]:
            ttk.Label(outer,text=label).pack(anchor='w')
            ttk.Combobox(outer,textvariable=var,values=values).pack(fill='x')
        ttk.Label(outer,text='Corrige les valeurs visibles. Une case vide signifie inconnue ; zéro doit être réellement lu.').pack(anchor='w',pady=8)
        columns=ttk.Frame(outer);columns.pack(fill='both',expand=True)
        canvas=tk.Canvas(columns,highlightthickness=0,height=200)
        scrollbar=ttk.Scrollbar(columns,orient='vertical',command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set);scrollbar.pack(side='right',fill='y');canvas.pack(fill='both',expand=True)
        table=ttk.Frame(canvas);canvas.create_window((0,0),window=table,anchor='nw')
        table.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
        for col,label in enumerate(('Caractéristique','Avant','Après')):ttk.Label(table,text=label).grid(row=0,column=col,padx=8)
        fields={'before':{},'after':{}}
        _,profile=item_profile(event.get('item_id'))
        stats=set(profile)
        for side in fields:stats.update((event.get(side) or {}).get('jet',{}))
        def add_stat(stat):
            if not stat or stat in fields['before']:return
            row=len(fields['before'])+1
            ttk.Label(table,text=stat).grid(row=row,column=0,sticky='w',padx=8,pady=2)
            for col,side in enumerate(fields,1):
                value=(event.get(side) or {}).get('jet',{}).get(stat)
                variable=tk.StringVar(value='' if value is None else str(value))
                fields[side][stat]=variable
                ttk.Entry(table,textvariable=variable,width=12).grid(row=row,column=col,padx=8,pady=2)
        for stat in sorted(stats):add_stat(stat)
        from forgely_dofocus import WEIGHT_PER_POINT
        extra=ttk.Frame(outer);extra.pack(fill='x',pady=4);extra_stat=tk.StringVar()
        ttk.Combobox(extra,textvariable=extra_stat,values=sorted(WEIGHT_PER_POINT),state='readonly',width=27).pack(side='left')
        ttk.Button(extra,text='Ajouter une ligne visible',command=lambda:add_stat(extra_stat.get())).pack(side='left',padx=6)
        pools={};pool_frame=ttk.Frame(outer);pool_frame.pack(fill='x',pady=4)
        for side,label in [('before','Puits avant'),('after','Puits après')]:
            value=(event.get(side) or {}).get('pool')
            pools[side]=tk.StringVar(value='' if value is None else str(value))
            ttk.Label(pool_frame,text=label).pack(side='left',padx=4)
            ttk.Entry(pool_frame,textvariable=pools[side],width=10).pack(side='left')
        note=tk.StringVar(value=event.get('review_note',''))
        ttk.Label(outer,text='Note de vérification').pack(anchor='w');ttk.Entry(outer,textvariable=note).pack(fill='x')
        ttk.Label(outer,text='Les séquences contenant plusieurs tentatives ou une coupe restent exclues, même après correction.',wraplength=730).pack(anchor='w',pady=6)
        confirm=tk.BooleanVar(value=False)
        ttk.Checkbutton(outer,text='J’ai comparé les images avant/après et vérifié cette tentative unique.',variable=confirm).pack(anchor='w')
        def save():
            try:
                if not confirm.get():raise ValueError('Vérifie les images puis coche la confirmation.')
                if item.get() not in labels or rune.get() not in RUNE_REFERENCES or outcome.get() not in ('SC','SN','EC'):
                    raise ValueError('Choisis un objet, une rune et un résultat connus.')
                ident=labels[item.get()];_,profile=item_profile(ident)
                changes={'item_id':ident,'natural_max':profile,'rune':rune.get(),'outcome':outcome.get(),
                         **{side:snapshot_from_fields({s:v.get() for s,v in values.items()},pools[side].get()) for side,values in fields.items()},
                         'status':'confirmed','review_note':note.get()}
                if not all(isinstance(changes[k],dict) and isinstance(changes[k].get('jet'),dict) for k in ('before','after')):
                    raise ValueError('Chaque état doit contenir jet et pool.')
                json.dumps(changes,allow_nan=False)
                self.apply_review(event['id'],changes);dialog.destroy()
            except (ValueError,TypeError) as exc:messagebox.showerror('Lecture à corriger',str(exc),parent=dialog)
        ttk.Button(outer,text='Enregistrer la vérification',command=save).pack(anchor='e',pady=8)

    def open_report(self):
        if not self.session or self.busy:return
        path=write_report(self.session,self.store.folder(self.session['id']))
        webbrowser.open(path.resolve().as_uri())

    def transfer(self):
        if not self.session or self.busy:return
        from forgely_data import DB_FILE
        try:
            result=transfer_session(self.session,DB_FILE)
            self.status.set(f'{result["accepted"]} observations transmises à Forgely ; {result["excluded"]} exclues. Les fréquences servent à calibrer les conseils, sans activer une stratégie non évaluée.')
        except (OSError,ValueError) as exc:messagebox.showerror('Transmission interrompue',str(exc),parent=self)

    def request_close(self,callback):
        if self.busy:
            self.close_callback=callback;self.stop()
        else:self.shutdown();callback()

    def shutdown(self):
        self.cancel.set();self.closed=True
        try:self.after_cancel(self.poll_id)
        except tk.TclError:pass
