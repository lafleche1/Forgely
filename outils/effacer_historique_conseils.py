"""Purge recommendations only; verify that all observation/trial measurements survive."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
from contextlib import closing

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Application'))
from forgely_advice_history import purge_history,measurements_only


def measurements(root):
    result={}
    for name,tables in (('observations_locales.sqlite3',('observations','fusion_contexts','evaluation_trials')),
                        ('simulations.sqlite3',('virtual_runs',))):
        path=root/name
        if not path.exists():continue
        with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
            present={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            for table in tables:
                if table not in present:continue
                columns='state_hash,item_id,state_json,trials,sc,sn,ec,source' if table=='virtual_runs' else '*'
                if table=='evaluation_trials':
                    available={r[1] for r in db.execute('PRAGMA table_info(evaluation_trials)')}
                    columns=','.join(c for c in ('observation_id','session','qualified','before_state','after_state','event_frame','in_scope') if c in available)
                    if not columns:continue
                digest=hashlib.sha256();count=0
                for row in db.execute(f'SELECT {columns} FROM {table} ORDER BY rowid'):
                    digest.update(repr(row).encode('utf8'));count+=1
                result[table]={'rows':count,'sha256':digest.hexdigest()}
                if table=='virtual_runs':
                    detail=hashlib.sha256()
                    for (raw,) in db.execute('SELECT results_json FROM virtual_runs ORDER BY rowid'):
                        detail.update(json.dumps(measurements_only(json.loads(raw)),sort_keys=True,
                            ensure_ascii=False,separators=(',',':')).encode('utf8'))
                    result['virtual_measurement_details']={'rows':count,'sha256':detail.hexdigest()}
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();root=args.data_dir.resolve(strict=True)
    if not root.is_dir():raise ValueError('Dossier de données requis')
    before=measurements(root)
    removed=purge_history(root/'observations_locales.sqlite3',root/'simulations.sqlite3',root/'bilans_sessions')
    after=measurements(root)
    if before!=after:raise RuntimeError('Les mesures ont changé pendant la purge : vérifier les écritures concurrentes')
    result={'data_directory':str(root),'removed':removed,'preserved_measurements':after,
            'measurements_unchanged':True,'archived_recommendations_enabled':False}
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(result,ensure_ascii=True))


if __name__=='__main__':main()
