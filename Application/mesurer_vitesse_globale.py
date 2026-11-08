"""Reproducible offline latency benchmark. Fictitious data, no game observations."""
import argparse
from contextlib import ExitStack
from functools import partial
import json
from pathlib import Path
import sqlite3
import statistics
from tempfile import TemporaryDirectory
from time import perf_counter_ns
from types import SimpleNamespace
from unittest.mock import patch


def measure(fn,count):
    fn()
    values=[]
    for _ in range(count):
        start=perf_counter_ns();fn();values.append((perf_counter_ns()-start)/1e6)
    values.sort()
    return {'p50_ms':round(statistics.median(values),4),'p95_ms':round(values[int(.95*(len(values)-1))],4),'calls':count}


def benchmark():
    from forgely_item_vision import identify_known
    from forgely_data import connect,stats
    import forgely
    from forgely_tools import natural_bounds,observation_cursor,cost_since
    registered=[(i,f'Amulette fictive numero {i:04d}') for i in range(2000)]+[(99999,'Anneau du Cycloïde')]
    result={'note':'Linux/Python offline; données fictives. Ne mesure pas la capture Windows ni la latence OCR réelle en jeu.',
            'registered_names':len(registered),'observations':30000}
    result['name_lookup']=measure(lambda:identify_known('ANNEAU DU CYCLOÏDE',registered),15)
    with TemporaryDirectory() as directory:
        root=Path(directory);db=root/'bench.sqlite3';csv=root/'bounds.csv'
        with connect(db) as connection:
            connection.executemany('INSERT INTO observations(captured_at,item,rune,outcome,source,evidence) VALUES(?,?,?,?,?,?)',
                [('2026-11-08T00:00:00','Objet benchmark',('Fo','Pa Fo','Ra Fo','Vi','Pa Vi','Ra Vi','Sa','Pa Sa','Ra Sa')[i%9],('SC','SN','EC')[i%3],'manual','SYNTHETIC BENCHMARK') for i in range(30000)])
        cursor=observation_cursor(db)
        csv.write_text('equipement,statistique,min,max\n'+''.join(f'Objet fictif {i},Force,0,100\n' for i in range(10000)),encoding='utf8')
        result['natural_bounds']=measure(lambda:natural_bounds('Objet fictif 9999',csv),15)
        cfg={'strategy':'Budget optimisé','budget_kamas':0,'prices':{'Fo':36,'Pa Fo':132,'Ra Fo':382,'Vi':248,'Pa Vi':830,'Ra Vi':2368,'Sa':316,'Pa Sa':1051,'Ra Sa':3131}}
        app=SimpleNamespace(observation_only=False,plan={'item':'Objet benchmark','stats':{'Force':{'target':50},'Vitalité':{'target':300},'Sagesse':{'target':30}}},
            active_equipment_verified=True,item=SimpleNamespace(get=lambda:'Objet benchmark'),
            live_jet={'Force':20,'Vitalité':200,'Sagesse':15},live_pool=30,live_after_fusion=False,
            budget_start_cursor=cursor,last_transition_audit=None,
            live_laboratory=SimpleNamespace(estimate=lambda *a:None,calibration=lambda *a:None,revision=0))
        with ExitStack() as patches:
            patches.enter_context(patch('forgely.read_settings',return_value=cfg))
            patches.enter_context(patch('forgely.natural_bounds',return_value={'Force':(0,100),'Vitalité':(0,350),'Sagesse':(0,50)}))
            patches.enter_context(patch('forgely.DB_FILE',db))
            patches.enter_context(patch('forgely.stats',side_effect=partial(stats,db_file=db)))
            patches.enter_context(patch('forgely.cost_since',side_effect=partial(cost_since,db_file=db)))
            if hasattr(forgely,'stats_by_rune'):
                from forgely_data import stats_by_rune
                patches.enter_context(patch('forgely.stats_by_rune',side_effect=partial(stats_by_rune,db_file=db)))
            result['stable_advice']=measure(lambda:forgely.Forgely.strategy_current(app),30)
            def changed():
                app.live_pool=29 if app.live_pool==30 else 30
                return forgely.Forgely.strategy_current(app)
            result['changed_state_advice']=measure(changed,30)
            result['selected_rune']=forgely.Forgely.strategy_current(app).rune
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();result=benchmark();args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(result,ensure_ascii=False))
