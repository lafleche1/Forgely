"""Remove archived recommendations while retaining actual and virtual measurements."""
from contextlib import closing
import json
from pathlib import Path
import sqlite3

MEASUREMENT_FIELDS=frozenset(('kind','real_observations','trials','counts','mean_target_loss',
    'mean_progress','mean_pool','mean_reward','reward_version','model_version','source'))


def measurements_only(results):
    return {rune:{key:value for key,value in row.items() if key in MEASUREMENT_FIELDS}
            for rune,row in results.items() if isinstance(row,dict)}


def without_forecasts(report):
    if not isinstance(report,dict):return report
    result=dict(report)
    if isinstance(report.get('prediction_log'),list):
        result['prediction_log']=[{k:v for k,v in row.items()
            if k not in ('forecast','forecast_state','forecast_frame')}
            if isinstance(row,dict) else row for row in report['prediction_log']]
    return result


def purge_history(observation_file,simulation_file=None,report_dir=None):
    """Only explicit recommendation fields/tables are removed. No backup copy."""
    result={'forecasts_removed':0,'virtual_advice_removed':0,'reports_cleaned':0}
    observation_file=Path(observation_file)
    if observation_file.is_file():
        with closing(sqlite3.connect(str(observation_file),timeout=15)) as db,db:
            tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if 'evaluation_trials' in tables:
                db.execute('UPDATE evaluation_trials SET forecast_id=NULL,matched=0 WHERE forecast_id IS NOT NULL')
            if 'evaluation_forecasts' in tables:
                result['forecasts_removed']=db.execute('SELECT count(*) FROM evaluation_forecasts').fetchone()[0]
                db.execute('DELETE FROM evaluation_forecasts')
            if 'evaluation_sessions' in tables:
                for sid,raw in db.execute('SELECT id,report FROM evaluation_sessions WHERE report IS NOT NULL').fetchall():
                    try:old=json.loads(raw)
                    except (ValueError,TypeError):continue
                    clean=without_forecasts(old)
                    if clean!=old:
                        db.execute('UPDATE evaluation_sessions SET report=? WHERE id=?',
                                   (json.dumps(clean,ensure_ascii=False),sid))
                        result['reports_cleaned']+=1
    if simulation_file is not None and Path(simulation_file).is_file():
        with closing(sqlite3.connect(str(simulation_file),timeout=15)) as db,db:
            exists=db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='virtual_runs'").fetchone()
            if exists:
                for ident,raw in db.execute('SELECT rowid,results_json FROM virtual_runs').fetchall():
                    old=json.loads(raw)
                    clean=measurements_only(old)
                    if clean!=old:
                        result['virtual_advice_removed']+=sum(len(set(row)-MEASUREMENT_FIELDS)
                            for row in old.values() if isinstance(row,dict))
                        db.execute('UPDATE virtual_runs SET results_json=? WHERE rowid=?',
                                   (json.dumps(clean,ensure_ascii=False),ident))
    if report_dir is not None and Path(report_dir).is_dir():
        root=Path(report_dir).resolve()
        for path in root.glob('bilan-*.json'):
            if path.is_symlink() or path.resolve().parent!=root:continue
            try:old=json.loads(path.read_text(encoding='utf8'))
            except (OSError,ValueError):continue
            clean=without_forecasts(old)
            if clean!=old:
                temporary=path.with_suffix('.json.tmp')
                temporary.write_text(json.dumps(clean,ensure_ascii=False),encoding='utf8')
                temporary.replace(path);result['reports_cleaned']+=1
    return result
