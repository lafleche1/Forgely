"""Offline benchmark; fictitious scaled items never enter the shipped reference."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import argparse
import json
import statistics
import time
import tracemalloc
import forgely_dofocus as d
from forgely_dofocus_store import build_database,ReferenceStore
from forgely_decision import advise


def timings(fn,count):
    values=[]
    for index in range(count):
        start=time.perf_counter_ns();fn(index);values.append((time.perf_counter_ns()-start)/1e6)
    values.sort()
    return {'p50_ms':statistics.median(values),'p95_ms':values[min(len(values)-1,int(.95*len(values)))]}


def benchmark(contexts=3000):
    if type(contexts) is not int or contexts<200:raise ValueError('Au moins 200 contextes pour ce test de croissance')
    data=d.catalogue()
    sample=next(s for s in data['snapshots'] if s['item_id']==14092 and s['pool']==0)
    jet={r['stat']:r['value'] for r in sample['rows']}
    result={'note':'Mesures locales Python ; fixture de croissance fictive, aucune nouvelle observation DOFUS.',
            'real_states':len(data['snapshots']),'real_database_bytes':d.STORE_PATH.stat().st_size,
            'synthetic_contexts':contexts,'synthetic_is_game_evidence':False}
    result['current_lookup']=timings(lambda _:d.lookup(sample['item'],jet,0,'Fo'),300)
    result['current_advice']=timings(lambda _:advise(jet,{'Force':40},pool=0,item=sample['item']),100)
    fixture={**data,'snapshots':[],'coverage':'SYNTHETIC BENCHMARK FIXTURE — NOT DOFOCUS EVIDENCE'}
    for index in range(contexts):
        s=deepcopy(sample);s['item']=f'Benchmark fictif {index:04}'
        s['item_id']=900000+index;s['url']=d.SOURCE_URL+str(s['item_id'])
        fixture['snapshots'].append(s)
    with TemporaryDirectory() as directory:
        source=Path(directory)/'fixture.json';db=Path(directory)/'fixture.sqlite3'
        source.write_text(json.dumps(fixture,ensure_ascii=False),encoding='utf-8')
        built=build_database(source,db);result['synthetic_database_bytes']=built['bytes']
        with patch.object(d,'STORE_PATH',db):
            item=f'Benchmark fictif {contexts-1:04}'
            result['synthetic_lookup_last']=timings(lambda _:d.lookup(item,jet,0,'Fo'),100)
            result['synthetic_advice_last']=timings(lambda _:advise(jet,{'Force':40},pool=0,item=item),100)
            result['synthetic_advice_uncached_items']=timings(lambda i:advise(jet,{'Force':40},pool=0,item=f'Benchmark fictif {i:04}'),200)
        store=ReferenceStore(db)
        result['synthetic_lookup_uncached_items']=timings(lambda i:store.rune(f'Benchmark fictif {i:04}',jet,0,'Fo'),200)
        tracemalloc.start()
        memory_store=ReferenceStore(db)
        for i in range(200):memory_store.rune(f'Benchmark fictif {i:04}',jet,0,'Fo')
        current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        result['reader_python_memory_after_200_distinct_states']={'current_bytes':current,'peak_bytes':peak,
            'note':'Allocations Python du lecteur uniquement ; exclut le processus, SQLite natif et la fixture de préparation.'}
        result['bounded_cache']={k:v._asdict() for k,v in memory_store.cache_info().items()}
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--contexts',type=int,default=3000)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    data=benchmark(args.contexts)
    args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(data,ensure_ascii=False))


if __name__=='__main__':main()
