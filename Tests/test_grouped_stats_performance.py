import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Application'))
import forgely_data as data

def test_grouped_matches_individual_and_external_updates(tmp_path):
    path=tmp_path/'observations.sqlite3'
    data.insert_observation('Item','Vi','SC','manual',db_file=path)
    data.insert_observation('Item','Fo','EC','ocr_auto',db_file=path)
    grouped=data.stats_by_rune(' Item ',db_file=path)
    assert grouped['Vi']==data.stats('Item','Vi',db_file=path)[1]
    assert grouped['Fo']==data.stats('Item','Fo',db_file=path)[1]
    data.insert_observation('Item','Vi','SN','manual',db_file=path)
    assert data.stats_by_rune('Item',db_file=path)['Vi']=={'SC':1,'SN':1,'EC':0}

def test_refresh_keeps_one_scheduled_timer():
    import ast
    source=Path('Application/forgely.py').read_text(encoding='utf8')
    tree=ast.parse(source)
    method=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='refresh_stats')
    module=ast.Module(body=[method],type_ignores=[])
    scope={}
    exec(compile(module,'refresh_stats','exec'),scope)
    class Fake:
        def __init__(self): self.pending={};self.serial=0;self.calls=0
        def after(self,delay,callback):
            self.serial+=1;self.pending[self.serial]=callback;return self.serial
        def after_cancel(self,timer): self.pending.pop(timer,None)
        def refresh_stats_now(self): self.calls+=1
        refresh_stats=scope['refresh_stats']
    ui=Fake()
    for _ in range(10): ui.refresh_stats()
    assert len(ui.pending)==1
    assert ui.calls==10
