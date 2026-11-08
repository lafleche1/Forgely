"""Inline target editor for observed characteristics; no equipment selection."""
import tkinter as tk
from forgely_dofocus import normalise_jet
from forgely_rules import RUNE_CHOICES


class LiveTargets(tk.Frame):
    def __init__(self,parent,jet,targets,on_save,on_close,palette,on_perfect=None):
        super().__init__(parent,bg=palette['PANEL'])
        self.fields={};self.jet=normalise_jet(jet) or {}
        self.columnconfigure(0,weight=1);self.rowconfigure(2,weight=1)
        tk.Label(self,text='Quel jet souhaites-tu atteindre ?',bg=palette['PANEL'],
                 fg=palette['FG'],font=('Segoe UI',12,'bold')).grid(row=0,column=0,sticky='w',pady=(0,8))
        if on_perfect:
            tk.Checkbutton(self,text='Jet parfait',variable=parent.root.perfect_goal_checked,
                           command=on_perfect,bg=palette['PANEL'],fg=palette['FG'],
                           selectcolor=palette['PANEL']).grid(row=1,column=0,sticky='w',pady=(0,6))
        viewport=tk.Frame(self,bg=palette['PANEL'])
        viewport.grid(row=2,column=0,sticky='nsew')
        viewport.columnconfigure(0,weight=1);viewport.rowconfigure(0,weight=1)
        canvas=tk.Canvas(viewport,bg=palette['PANEL'],highlightthickness=0,height=180)
        scroll=tk.Scrollbar(viewport,orient='vertical',command=canvas.yview)
        scroll.grid(row=0,column=1,sticky='ns');canvas.grid(row=0,column=0,sticky='nsew')
        body=tk.Frame(canvas,bg=palette['PANEL']);canvas.create_window((0,0),window=body,anchor='nw')
        self.body=body;self.palette=palette
        body.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.configure(yscrollcommand=scroll.set)
        for i,stat in enumerate(dict.fromkeys((*self.jet,*targets))):
            current=self.jet.get(stat)
            if stat not in RUNE_CHOICES:continue
            tk.Label(body,text=f'{stat}  ({current if current is not None else "À lire"})',anchor='w',width=29,
                     bg=palette['PANEL'],fg=palette['FG']).grid(row=i,column=0,sticky='w',pady=3)
            value=tk.StringVar(value=str(targets.get(stat,current)) if targets.get(stat,current) is not None else '')
            tk.Entry(body,textvariable=value,width=9).grid(row=i,column=1,padx=8,pady=3)
            self.fields[stat]=value
        self.error=tk.Label(self,text='',bg=palette['PANEL'],fg=palette['GOLD'],wraplength=470)
        self.error.grid(row=3,column=0,sticky='ew')
        def save():
            try:
                values={k:int(v.get().strip()) for k,v in self.fields.items() if v.get().strip()}
                on_save(values)
            except ValueError as exc:self.error.configure(text=str(exc))
        actions=tk.Frame(self,bg=palette['PANEL']);actions.grid(row=4,column=0,sticky='ew',pady=6)
        self.save_button=tk.Button(actions,text='Enregistrer et conseiller',command=save)
        self.save_button.pack(side='left')
        tk.Button(actions,text='Plus tard',command=on_close).pack(side='right')

    def fill_targets(self,targets):
        for child in self.body.winfo_children():child.destroy()
        self.fields={}
        for i,stat in enumerate(dict.fromkeys((*self.jet,*targets))):
            if stat not in RUNE_CHOICES:continue
            current=self.jet.get(stat)
            tk.Label(self.body,text=f'{stat}  ({current if current is not None else "À lire"})',
                     anchor='w',width=29,bg=self.palette['PANEL'],fg=self.palette['FG']).grid(row=i,column=0,sticky='w',pady=3)
            value=tk.StringVar(value=str(targets[stat]) if stat in targets else '')
            tk.Entry(self.body,textvariable=value,width=9).grid(row=i,column=1,padx=8,pady=3)
            self.fields[stat]=value
        self.error.configure(text='')
