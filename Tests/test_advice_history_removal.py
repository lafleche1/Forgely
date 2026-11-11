import json
import sqlite3
from forgely_session_review import SessionRecorder
from forgely_simulation_journal import SimulationJournal


def test_current_session_forecast_is_not_persisted_in_database_or_report(tmp_path):
    rec=SessionRecorder(tmp_path/'observations_locales.sqlite3')
    rec.ensure_session(item='Test',targets={'Force':1},jets={'Force':0},pool=5,prices={},scope='scope')
    rec.forecast('Fo',{'SC':50,'SN':50,'EC':0},frame=1,scope='scope')
    with sqlite3.connect(rec.db_file) as db:
        assert db.execute('SELECT count(*) FROM evaluation_forecasts').fetchone()[0]==0
    from forgely_data import insert_observation
    obs=insert_observation('Test','Fo','SC','manual',db_file=rec.db_file)
    rec.event(obs,'Test','Fo','SC',frame=2,scope='scope')
    rec.transition(obs,{'jet':{'Force':0},'pool':5},{'jet':{'Force':1},'pool':5},qualified=True)
    report=rec.finish(jets={'Force':1},pool=5,confirmed=True)
    assert report['prediction_evaluation']['n']==1
    assert report['attempts']==1
    for row in json.loads(open(report['json_path'],encoding='utf8').read())['prediction_log']:
        assert not {'forecast','forecast_state','forecast_frame'} & row.keys()


def test_virtual_journal_keeps_trial_statistics_without_advice_or_policy(tmp_path):
    journal=SimulationJournal(tmp_path/'simulations.sqlite3')
    result={'Fo':dict(kind='virtual_trials',real_observations=0,trials=16,
        counts={'SC':4,'SN':4,'EC':8},mean_target_loss=1,
        sequence={'validation':{'selected':'Fo'}},trained_policy={'factor':1.2})}
    journal.record(('model',77,'state'),result)
    with sqlite3.connect(journal.path) as db:
        saved=json.loads(db.execute('SELECT results_json FROM virtual_runs').fetchone()[0])
    assert 'sequence' not in saved['Fo'] and 'trained_policy' not in saved['Fo']
    assert journal.totals()=={'virtual':16,'SC':4,'SN':4,'EC':8}
    assert 'sequence' in result['Fo']  # Live caller's current advice is intact.


def test_purge_removes_old_advice_and_preserves_real_and_training_measurements(tmp_path):
    from forgely_advice_history import purge_history
    real=tmp_path/'observations_locales.sqlite3';virtual=tmp_path/'simulations.sqlite3'
    with sqlite3.connect(real) as db:
        db.executescript('CREATE TABLE observations(id INTEGER,outcome TEXT);'
            "INSERT INTO observations VALUES(1,'SC');"
            'CREATE TABLE evaluation_forecasts(id INTEGER,prediction TEXT);'
            "INSERT INTO evaluation_forecasts VALUES(1,'old advice');"
            'CREATE TABLE evaluation_trials(forecast_id INTEGER,matched INTEGER,reason TEXT);'
            "INSERT INTO evaluation_trials VALUES(1,1,'matched');")
    with sqlite3.connect(virtual) as db:
        db.execute('CREATE TABLE virtual_runs(results_json TEXT,trials INTEGER,sc INTEGER,sn INTEGER,ec INTEGER)')
        db.execute('INSERT INTO virtual_runs VALUES(?,16,4,4,8)',(json.dumps({'Fo':{
            'trials':16,'counts':{'SC':4,'SN':4,'EC':8},'sequence':{'selected':'Fo'},'trained_policy':{'factor':1.2}}}),))
    result=purge_history(real,virtual)
    assert result['forecasts_removed']==1 and result['virtual_advice_removed']==2
    with sqlite3.connect(real) as db:
        assert db.execute('SELECT * FROM observations').fetchall()==[(1,'SC')]
        assert db.execute('SELECT count(*) FROM evaluation_forecasts').fetchone()[0]==0
        assert db.execute('SELECT forecast_id FROM evaluation_trials').fetchone()[0] is None
    with sqlite3.connect(virtual) as db:
        assert db.execute('SELECT trials,sc,sn,ec FROM virtual_runs').fetchone()==(16,4,4,8)
    assert purge_history(real,virtual)['virtual_advice_removed']==0


def test_archived_advice_never_becomes_visual_evidence_or_learning(tmp_path):
    from forgely_empirical_model import load_empirical_model
    from forgely_labo_live import compute_snapshot
    rec=SessionRecorder(tmp_path/'observations_locales.sqlite3')
    with sqlite3.connect(rec.db_file) as db:
        db.execute('INSERT INTO evaluation_forecasts(session,rune,prediction,state,frame,scope) VALUES(?,?,?,?,?,?)',
            ('old','Fo',json.dumps({'SC':100,'SN':0,'EC':0}),json.dumps({'jet':{'Force':40},'pool':100}),1,'old'))
    assert load_empirical_model(rec.db_file).sample_count==0
    snapshot=compute_snapshot(rec.db_file)
    assert snapshot['observations']==0
    assert not snapshot.get('calibration')


def test_cleanup_verification_detects_per_rune_measurement_changes(tmp_path):
    import runpy
    from pathlib import Path
    tool=runpy.run_path(str(Path(__file__).resolve().parents[1]/'outils/effacer_historique_conseils.py'))
    journal=SimulationJournal(tmp_path/'simulations.sqlite3')
    journal.record(('model',77,'state'),{'Fo':dict(kind='virtual_trials',real_observations=0,
        trials=16,counts={'SC':4,'SN':4,'EC':8},mean_target_loss=1)})
    before=tool['measurements'](tmp_path)
    with sqlite3.connect(journal.path) as db:
        data=json.loads(db.execute('SELECT results_json FROM virtual_runs').fetchone()[0])
        data['Fo']['mean_target_loss']=2
        db.execute('UPDATE virtual_runs SET results_json=?',(json.dumps(data),))
    assert tool['measurements'](tmp_path)!=before
