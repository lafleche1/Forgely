"""Inline review editor, embedded in Forgely's existing floating window."""
import json
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from forgely_reading_review import decode
from forgely_jet import STATS, parse_jet
from forgely_atelier import parse_reliquat


class ReviewPanel(tk.Frame):
    def __init__(self,parent,store,on_done,on_later,palette):
        super().__init__(parent,bg=palette['PANEL'])
        self.store,self.on_done,self.on_later=store,on_done,on_later
        self.palette=palette;self.rows=[];self.ident=None;self.boxes={};self.mode='number'
        self.number=tk.StringVar();self.label=tk.StringVar();self.message=tk.StringVar()
        self.selection=tk.StringVar();self.show_confirmed=tk.BooleanVar(value=False)
        top=tk.Frame(self,bg=palette['PANEL']);top.pack(fill='x')
        self.combo=ttk.Combobox(top,textvariable=self.selection,state='readonly')
        self.combo.pack(side='left',fill='x',expand=True)
        self.combo.bind('<<ComboboxSelected>>',lambda e:self.load(self.combo.current()))
        tk.Checkbutton(top,text='Références',variable=self.show_confirmed,command=self.reload,
                       bg=palette['PANEL'],fg=palette['FG'],selectcolor=palette['PANEL2']).pack(side='right')
        canvas_area=tk.Frame(self,bg=palette['PANEL']);canvas_area.pack(fill='x',pady=(8,0))
        self.canvas=tk.Canvas(canvas_area,height=100,bg='#11151c',highlightthickness=0)
        vertical=ttk.Scrollbar(canvas_area,orient='vertical',command=self.canvas.yview)
        vertical.pack(side='right',fill='y');self.canvas.configure(yscrollcommand=vertical.set)
        self.canvas.pack(side='left',fill='both',expand=True)
        scroll=ttk.Scrollbar(self,orient='horizontal',command=self.canvas.xview)
        scroll.pack(fill='x');self.canvas.configure(xscrollcommand=scroll.set)
        self.canvas.bind('<ButtonPress-1>',self.start_box)
        self.canvas.bind('<B1-Motion>',self.drag_box)
        self.canvas.bind('<ButtonRelease-1>',self.end_box)
        tools=tk.Frame(self,bg=palette['PANEL']);tools.pack(fill='x',pady=5)
        self.number_select=ttk.Button(tools,text='1 · Encadrer le nombre',command=lambda:self.set_mode('number'))
        self.number_select.pack(side='left',padx=(0,5))
        ttk.Button(tools,text='2 · Encadrer le libellé',command=lambda:self.set_mode('label')).pack(side='left')
        fields=tk.Frame(self,bg=palette['PANEL']);fields.pack(fill='x')
        ttk.Entry(fields,textvariable=self.number,width=10).pack(side='left',padx=(0,8))
        self.label_input=ttk.Combobox(fields,textvariable=self.label,values=STATS,state='readonly')
        self.label_input.pack(side='left',fill='x',expand=True)
        tk.Label(self,textvariable=self.message,bg=palette['PANEL'],fg=palette['GOLD'],
                 anchor='w',justify='left',wraplength=500).pack(fill='x',pady=5)
        actions=tk.Frame(self,bg=palette['PANEL']);actions.pack(fill='x')
        self.confirm_button=ttk.Button(actions,text='Confirmer / corriger',command=self.confirm)
        self.confirm_button.pack(side='left',padx=(0,6))
        self.reject_button=ttk.Button(actions,text='Illisible',command=self.reject)
        self.reject_button.pack(side='left',padx=(0,6))
        ttk.Button(actions,text='Plus tard',command=on_later).pack(side='right')
        self.disable_button=ttk.Button(actions,text='Désactiver',command=self.disable)
        self.reload()

    def reload(self):
        self.rows=self.store.confirmed() if self.show_confirmed.get() else self.store.pending()
        values=[f"{i+1}. {r.get('label') or r.get('suggestion') or 'Lecture inconnue'}"[:95] for i,r in enumerate(self.rows)]
        self.combo.configure(values=values)
        if self.rows:
            self.combo.current(0);self.load(0)
        else:
            self.ident=None;self.selection.set('Aucune lecture en attente')
            self.canvas.delete('all');self.message.set('Aucune demande à traiter.')
            self.confirm_button.configure(state='disabled');self.reject_button.configure(state='disabled')

    def load(self,index):
        if not 0<=index<len(self.rows):return
        row=self.store.get(self.rows[index]['id']);self.ident=row['id'];self.boxes={}
        bgr=decode(row['image']);self.image=Image.fromarray(bgr[:,:,::-1])
        self.zoom=min(2,500/self.image.width)
        display=self.image.resize((round(self.image.width*self.zoom),round(self.image.height*self.zoom)),Image.Resampling.NEAREST)
        self.photo=ImageTk.PhotoImage(display,master=self)
        self.canvas.delete('all');self.canvas.create_image(0,0,image=self.photo,anchor='nw')
        self.canvas.configure(scrollregion=(0,0,display.width,display.height));self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        self.canvas.configure(height=min(120,max(55,display.height)))
        self.number.set(row['number'] or '');self.label.set(row['label'] or '')
        if row['kind']=='pool':
            self.label_input.configure(values=('Puits',));self.label.set('Puits')
            suggestion=parse_reliquat(row['suggestion'] or '')
            if row['state'] in ('pending','needs_review') and suggestion is not None:self.number.set(str(suggestion).replace('.',','))
        else:
            self.label_input.configure(values=STATS)
            proposed=parse_jet(row['suggestion'] or '')
            if row['state'] in ('pending','needs_review') and len(proposed)==1:
                name,value=next(iter(proposed.items()));self.number.set(str(value));self.label.set(name)
        if row['state']=='confirmed':
            self.boxes={'number':tuple(json.loads(row['number_box'])),'label':tuple(json.loads(row['label_box']))}
            self.draw_boxes();self.confirm_button.configure(state='disabled');self.reject_button.configure(state='disabled')
            self.disable_button.pack(side='left',padx=6)
            self.message.set('Référence confirmée. Désactiver la retire du catalogue utilisé par la V1.')
        else:
            self.confirm_button.configure(state='normal');self.reject_button.configure(state='normal');self.disable_button.pack_forget()
            self.set_mode('number')

    def set_mode(self,mode):
        self.mode=mode
        self.message.set(('Encadre le nombre complet, signe et virgule compris.' if mode=='number'
                          else 'Encadre seulement le libellé, sans nombre ni icône.')+
                         ' La correction concerne cette image enregistrée.')

    def point(self,event):
        return (max(0,min(self.image.width,round(self.canvas.canvasx(event.x)/self.zoom))),
                max(0,min(self.image.height,round(self.canvas.canvasy(event.y)/self.zoom))))

    def start_box(self,event):
        if self.ident:self.start=self.point(event)

    def drag_box(self,event):
        if not hasattr(self,'start'):return
        x,y=self.point(event);a,b=self.start
        self.canvas.delete('draft')
        self.canvas.create_rectangle(a*self.zoom,b*self.zoom,x*self.zoom,y*self.zoom,outline='#f5c879',width=2,tags='draft')

    def end_box(self,event):
        if not hasattr(self,'start'):return
        x,y=self.point(event);a,b=self.start;del self.start
        self.canvas.delete('draft')
        if x!=a and y!=b:
            self.boxes[self.mode]=(min(x,a),min(y,b),abs(x-a),abs(y-b))
            self.draw_boxes()
            if self.mode=='number':self.set_mode('label')

    def draw_boxes(self):
        self.canvas.delete('boxes')
        for name,(x,y,w,h) in self.boxes.items():
            self.canvas.create_rectangle(x*self.zoom,y*self.zoom,(x+w)*self.zoom,(y+h)*self.zoom,
                outline='#77ddab' if name=='number' else '#7eb7ff',width=2,tags='boxes')

    def confirm(self):
        try:
            if not self.ident or set(self.boxes)!={'number','label'}:
                raise ValueError('Encadre le nombre et son libellé avant de confirmer.')
            self.store.confirm(self.ident,self.number.get().strip(),self.label.get().strip(),
                               self.boxes['number'],self.boxes['label'])
        except (ValueError,OSError) as exc:
            self.message.set(str(exc));return
        self.on_done()

    def reject(self):
        if self.ident:self.store.reject(self.ident);self.on_done()

    def disable(self):
        if self.ident:self.store.disable(self.ident);self.on_done()
