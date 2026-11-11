import json
from pathlib import Path
import pytest
from forgely_data import insert_observation, insert_unassigned
from forgely_session_review import SessionRecorder


def recorder(tmp_path):
    return SessionRecorder(tmp_path/'real.db',tmp_path/'reports')


def begin(rec,**kw):
    args=dict(item='Test',targets={'Force':2},jets={'Force':0},pool=5,
              prices={'Fo':36},scope='capture-1',level=169)
    args.update(kw)
    return rec.ensure_session(**args)


def test_report_scoped_to_item_and_boundary_with_unknown_costs(tmp_path):
    rec=recorder(tmp_path)
    insert_observation('Test','Fo','EC','manual',db_file=rec.db_file)
    sid=begin(rec)
    insert_observation('Test','Fo','SC','ocr_auto',db_file=rec.db_file)
    insert_observation('Other','Fo','EC','manual',db_file=rec.db_file)
    insert_observation('Test','Pa Fo','SN','manual',db_file=rec.db_file)
    insert_unassigned('EC',db_file=rec.db_file)
    result=rec.finish(jets={'Force':2},pool=5,confirmed=True)
    assert result['session_id']==sid and result['goal']['status']=='atteint'
    assert result['attempts']==2 and result['known_cost']==36
    assert result['unpriced_attempts']==1 and result['unassigned_actions']==1
    assert result['cost_complete'] is False
    assert json.loads(Path(result['json_path']).read_text())['attempts']==2
    assert rec.finish(jets={'Force':2},pool=5,confirmed=True)['session_id']==sid
    assert len(list(rec.report_dir.glob('*.json')))==1


def test_finish_unconfirmed_never_claims_goal(tmp_path):
    rec=recorder(tmp_path);begin(rec)
    result=rec.finish(jets={'Force':2},pool=5,confirmed=False)
    assert result['goal']['status']=='inconnu'


def test_change_target_closes_old_session_without_reusing_forecast(tmp_path):
    rec=recorder(tmp_path);first=begin(rec)
    rec.forecast('Fo',{'SC':50,'SN':50,'EC':0,'version':'test'},frame=1,scope='capture-1')
    second=begin(rec,targets={'Force':3})
    assert second!=first
    obs=insert_observation('Test','Fo','SC','ocr_auto',db_file=rec.db_file)
    rec.event(obs,'Test','Fo','SC',frame=2,scope='capture-1')
    rec.transition(obs,{'jet':{'Force':0},'pool':5},{'jet':{'Force':1},'pool':5},qualified=True)
    report=rec.finish(jets={'Force':1},pool=5,confirmed=True)
    assert report['prediction_evaluation']['n']==0


def test_only_prospective_same_scope_rune_and_context_scores(tmp_path):
    rec=recorder(tmp_path);begin(rec)
    rec.forecast('Fo',{'SC':50,'SN':50,'EC':0,'version':'test'},frame=10,scope='capture-1')
    obs=insert_observation('Test','Fo','SC','ocr_auto',db_file=rec.db_file)
    rec.event(obs,'Test','Fo','SC',frame=11,scope='capture-1')
    rec.transition(obs,{'jet':{'Force':0},'pool':5},{'jet':{'Force':1},'pool':5},qualified=True)
    result=rec.finish(jets={'Force':1},pool=5,confirmed=True)
    assert result['prediction_evaluation']['n']==1
    assert result['prediction_evaluation']['brier']==pytest.approx(.5)
    assert result['learning']['qualified_transitions']==1


@pytest.mark.parametrize('frame,scope,rune,before,qualified',[
    (10,'capture-1','Fo',{'jet':{'Force':0},'pool':5},True),
    (11,'capture-2','Fo',{'jet':{'Force':0},'pool':5},True),
    (11,'capture-1','Pa Fo',{'jet':{'Force':0},'pool':5},True),
    (11,'capture-1','Fo',{'jet':{'Force':1},'pool':5},True),
    (11,'capture-1','Fo',{'jet':{'Force':0},'pool':5},False)])
def test_unmatched_observations_never_validate_forecast(tmp_path,frame,scope,rune,before,qualified):
    rec=recorder(tmp_path);begin(rec)
    rec.forecast('Fo',{'SC':50,'SN':50,'EC':0,'version':'test'},frame=10,scope='capture-1')
    obs=insert_observation('Test',rune,'SC','ocr_auto',db_file=rec.db_file)
    rec.event(obs,'Test',rune,'SC',frame=frame,scope=scope)
    rec.transition(obs,before,{'jet':{'Force':3},'pool':5},qualified=qualified)
    assert rec.finish(jets={'Force':3},pool=5,confirmed=True)['prediction_evaluation']['n']==0


def test_export_escapes_item_and_preserves_real_data(tmp_path):
    from forgely_session_review import export_review
    import zipfile
    rec=recorder(tmp_path)
    item='<script>alert(1)</script>'
    begin(rec,item=item)
    insert_observation(item,'Fo','SC','ocr_auto',db_file=rec.db_file)
    result=rec.finish(jets={'Force':1},pool=5,confirmed=True)
    html=Path(result['html_path']).read_text()
    assert '<script>' not in html and '&lt;script&gt;' in html
    original=rec.db_file.read_bytes()
    out=export_review(result,tmp_path/'bilan.zip')
    with zipfile.ZipFile(out) as z:
        assert len(z.namelist())==2
        assert all(name.endswith(('.json','.html')) for name in z.namelist())
    assert rec.db_file.read_bytes()==original
    with pytest.raises(ValueError):export_review(result,result['json_path'])


def test_ui_hooks_record_prospective_trial_and_calibration_progress(tmp_path):
    from types import SimpleNamespace
    from unittest.mock import patch
    from forgely_session_ui import review_tick,review_event,review_transition,capture_scope
    from forgely_decision import advise
    rec=recorder(tmp_path)
    mailbox=SimpleNamespace(generation=lambda:0)
    app=SimpleNamespace(session_recorder=rec,plan={'item':'Test','stats':{'Force':{'target':2}}},
        active_equipment_verified=True,live_after_fusion=False,live_jet={'Force':0},live_pool=5,
        item=SimpleNamespace(get=lambda:'Test'),frame_mailbox=mailbox,latest_observation_id=10)
    p=advise({'Force':0},{'Force':2},natural_max={'Force':100},pool=5,prices={'Fo':36})
    # Legacy prices do not select the rune; record the actual advised action.
    p=advise({'Force':0},{'Force':2},natural_max={'Force':100},pool=5,
             prices={'Fo':36,'Pa Fo':1000,'Ra Fo':10000},remaining_budget=100,mode='Budget optimisé')
    with patch('forgely_tools.read_settings',return_value={'prices':{'Fo':36}}):
        review_tick(app,p)
    from forgely_dofocus import reference
    rune=p.rune
    gain=reference(rune).gain
    obs=insert_observation('Test',rune,'SC','ocr_auto',db_file=rec.db_file)
    review_event(app,obs,'Test',rune,'SC',11,capture_scope(app))
    review_transition(app,obs,{'jet':{'Force':0},'pool':5},{'jet':{'Force':gain},'pool':5},True)
    result=rec.finish(jets={'Force':gain},pool=5,confirmed=True)
    assert result['prediction_evaluation']['n']==1
    assert result['learning']['qualified_transitions']==1


def test_old_capture_does_not_consume_current_forecast_or_count_in_report(tmp_path):
    rec=recorder(tmp_path);begin(rec,scope='new')
    rec.forecast('Fo',{'SC':50,'SN':50,'EC':0},frame=10,scope='new')
    old=insert_observation('Test','Fo','SC','ocr_auto',db_file=rec.db_file)
    rec.event(old,'Test','Fo','SC',frame=11,scope='old')
    now=insert_observation('Test','Fo','SC','ocr_auto',db_file=rec.db_file)
    rec.event(now,'Test','Fo','SC',frame=12,scope='new')
    rec.transition(now,{'jet':{'Force':0},'pool':5},{'jet':{'Force':1},'pool':5},qualified=True)
    result=rec.finish(jets={'Force':1},pool=5,confirmed=True)
    assert result['prediction_evaluation']['n']==1
    assert result['attempts']==1 and result['ignored_scope_attempts']==1


def test_ui_closes_goal_change_even_while_waiting_for_post_rune_reading(tmp_path):
    from types import SimpleNamespace
    from forgely_session_ui import review_tick
    rec=recorder(tmp_path)
    box=SimpleNamespace(generation=lambda:0)
    scope=str(id(box))+':0'
    begin(rec,scope=scope)
    app=SimpleNamespace(session_recorder=rec,plan={'item':'Test','stats':{'Force':{'target':3}}},
        active_equipment_verified=True,live_after_fusion=True,live_jet=None,live_pool=None,
        item=SimpleNamespace(get=lambda:'Test'),frame_mailbox=box)
    review_tick(app)
    assert rec.active is None and rec.last_report['goal']['status']=='inconnu'


def test_actual_message_pipeline_links_observation_and_full_transition(tmp_path):
    import queue
    from types import SimpleNamespace
    from unittest.mock import Mock,patch
    from forgely import Forgely
    from forgely_context import FusionPairing,save_transition
    from forgely_workshop_readings import WorkshopReadings
    from forgely_labo_live import LiveLaboratory
    from forgely_session_ui import capture_scope
    rec=recorder(tmp_path);readings=WorkshopReadings(required_frames=2)
    readings.observe({'Force':0},5);readings.observe({'Force':0},5)
    app=SimpleNamespace(messages=queue.Queue(),workshop_readings=readings,session_recorder=rec,
        active_equipment_verified=True,item=SimpleNamespace(get=lambda:'Test'),
        live_jet={'Force':0},live_pool=5,live_after_fusion=False,
        pending_transition=None,pre_fusion_sample=None,fusion_pairing=FusionPairing(),
        latest_observation_id=10,last_full_event_frame_id=0,last_displayed_result_frame_id=0,
        live_laboratory=LiveLaboratory(rec.db_file),context_saved=0,context_rejected=0,saved_auto=0,
        status=Mock(),overlay=Mock(),atelier_info_label=Mock(),detect_label=Mock(),detect_help=Mock(),
        refresh_strategy=Mock(),render_plan=Mock(),refresh_stats_now=Mock(),
        dashboard=None,winfo_exists=lambda:False,process_messages=lambda:None)
    begin(rec,scope=capture_scope(app))
    rec.forecast('Fo',{'SC':50,'SN':50,'EC':0},frame=1,scope=capture_scope(app))
    def persist(*args,**kw):return save_transition(*args,**kw,db_file=rec.db_file)
    def observe(*args,**kw):return insert_observation(*args,**kw,db_file=rec.db_file)
    with patch('forgely.save_transition',side_effect=persist),patch('forgely.insert_observation',side_effect=observe), \
         patch('forgely_dofocus.natural_profile',return_value={'Force':100}):
        app.messages.put(('atelier_read',({'Force':1},5)))
        app.messages.put(('auto_event_frame',(10,SimpleNamespace(rune='Fo',outcome='SC',evidence='test'))))
        app.messages.put(('atelier_read',({'Force':1},5)))
        app.messages.put(('atelier_read',({'Force':1},5)))
        while not app.messages.empty():Forgely.process_messages(app)
    result=rec.finish(jets={'Force':1},pool=5,confirmed=True)
    assert result['attempts']==1
    assert result['prediction_evaluation']['n']==1
    assert result['prediction_log'][0]['event_frame']==10
