from forgely_sqlite import database_connection
"""Audit local, en lecture seule, des tentatives de forgemagie enregistrées."""
import argparse
import csv
import json
import sqlite3
from collections import Counter
from pathlib import Path
from forgely_data import DB_FILE

FIELDS = ('id','captured_at','item','rune','outcome','source','evidence')

def audit(db_file=DB_FILE):
    path = Path(db_file)
    if not path.is_file():
        raise FileNotFoundError(f'Base de données introuvable : {path}')
    with database_connection(f'file:{path.resolve().as_posix()}?mode=ro', uri=True) as db:
        rows = [dict(zip(FIELDS,row)) for row in db.execute('SELECT '+','.join(FIELDS)+' FROM observations ORDER BY id')]
        has_unassigned = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='unassigned_actions'").fetchone()
        uncertain = db.execute('SELECT COUNT(*) FROM unassigned_actions').fetchone()[0] if has_unassigned else 0
    sources = Counter(row['source'] for row in rows)
    outcomes = Counter(row['outcome'] for row in rows)
    # OCR auto is NOT equivalent to ground-truth validation.
    return {'total':len(rows),'sources':dict(sources),'outcomes':dict(outcomes),
            'unassigned':uncertain,'auto_to_review':sources.get('ocr_auto',0), 'rows':rows}

def export(db_file, directory):
    result=audit(db_file)
    out=Path(directory); out.mkdir(parents=True,exist_ok=True)
    with (out/'tentatives_a_verifier.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS+('verification_humaine','correction','commentaire'))
        writer.writeheader()
        for row in result['rows']:
            writer.writerow({**row,'verification_humaine':'','correction':'','commentaire':''})
    report={k:v for k,v in result.items() if k!='rows'}
    (out/'bilan_collecte.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Exporter un audit local de Forgely, sans modifier les données')
    parser.add_argument('--db',default=str(DB_FILE))
    parser.add_argument('--output',default=str(Path.home()/'Documents'/'Forgely-Audit'))
    args=parser.parse_args()
    print(json.dumps(export(args.db,args.output),ensure_ascii=False,indent=2))
    print('Export :',args.output)
