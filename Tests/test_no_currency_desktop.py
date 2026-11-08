"""Inspect actual widgets in isolated Tk processes without touching user data."""
import os
from pathlib import Path
import subprocess
import sys


def test_training_has_no_currency_controls_and_advice_stays_readable(tmp_path):
    script=r'''
import tkinter as tk
from tkinter import ttk
from unittest.mock import patch
from entrainer_forgely import TrainingWindow
from forgely import Forgely
from forgely_decision import Proposal

def texts(widget):
    result=[]
    for key in ('text',):
        try:result.append(str(widget.cget(key)))
        except tk.TclError:pass
    if isinstance(widget,ttk.Notebook):
        result.extend(widget.tab(tab,'text') for tab in widget.tabs())
    for child in widget.winfo_children():result.extend(texts(child))
    return result

root=tk.Tk();root.withdraw()
training=TrainingWindow(root)
assert not hasattr(training,'budget') and not hasattr(training,'price_button')
def check():
    for text in texts(root):
        assert not any(w in text.casefold() for w in ('prix','budget','kamas','coût')),text
check()
for child in root.winfo_children():child.destroy()
root.observation_only=False
root.rune=tk.StringVar(value='Fo');root.item=tk.StringVar(value='Anneau')
root.plan=None;root.live_jet={};root.live_pool=None
root.active_equipment_verified=False;root.live_after_fusion=False
root.ui_fonts={'body':'Segoe UI'}
root.label=lambda parent,text,size=10,**kwargs:tk.Label(parent,text=text)
root.button=lambda parent,text,command,*args,**kwargs:tk.Button(parent,text=text,command=command)
root.strategy_current=lambda:Proposal('Fo','fm_classique','Fo','Jet cible','aucune')
root.refresh_strategy=lambda:None
root.expert_detail=lambda proposal:Forgely.expert_detail(root,proposal)
Forgely.open_strategy(root)
with patch('forgely.list_successes',return_value=[]):Forgely.open_workbench(root)
root.update()
assert any("PUITS" in t for t in texts(root))
root.destroy()
'''
    env=dict(os.environ,PYTHONPATH=str(Path(__file__).resolve().parents[1]/'Application'),
             LOCALAPPDATA=str(tmp_path/'profile'))
    result=subprocess.run([sys.executable,'-c',script],env=env,capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stdout+result.stderr
