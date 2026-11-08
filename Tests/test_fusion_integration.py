from types import SimpleNamespace
from unittest.mock import patch
import pytest


def test_unchanged_sn_is_emitted_by_real_worker_tracker_with_its_event_frame():
    from forgely_learning import FusionContextTracker
    from forgely_detection import Observation
    tracker=FusionContextTracker()
    old='item\nEchec\n-1 Force\nEchec'
    new='item\nReussite\nEchec\n-1 Force\nEchec'
    for frame in (1,2):tracker.observe('Test',old,{'Force':1},0,None)
    event=Observation('Fo','SN','','confirmed')
    tracker.observe('Test',new,{'Force':1},0,event,event_frame_id=11)
    transition=tracker.observe('Test',new,{'Force':1},0,None)
    assert transition is not None
    assert transition['before']==transition['after']
    assert transition['event_frame_id']==11
    assert tracker.pending_event is None


@pytest.mark.parametrize(('event_frame','expected'),[(11,1),(12,0)])
def test_deferred_real_accepted_event_keeps_observation_link_for_session_review(tmp_path,event_frame,expected):
    import queue
    from unittest.mock import Mock
    from forgely import Forgely
    from forgely_pipeline import AcceptedRuneEvent
    from forgely_detection import Observation
    from forgely_session_review import SessionRecorder
    from forgely_session_ui import capture_scope
    from forgely_workshop_readings import WorkshopReadings
    from forgely_labo_live import LiveLaboratory
    from forgely_context import save_transition
    from forgely_data import insert_observation
    db=tmp_path/'events.db';rec=SessionRecorder(db,tmp_path/'reports')
    mailbox=SimpleNamespace(generation=lambda:0,snapshot=lambda:(0,(12,None,'A',0,0)))
    readings=WorkshopReadings(required_frames=2)
    readings.observe({'Force':0},5);readings.observe({'Force':0},5)
    app=SimpleNamespace(frame_mailbox=mailbox,messages=queue.Queue(),session_recorder=rec,
        workshop_readings=readings,active_equipment_verified=True,item=SimpleNamespace(get=lambda:'Test'),
        live_jet={'Force':0},live_pool=5,live_after_fusion=False,latest_observation_id=12,
        last_full_event_frame_id=0,last_displayed_result_frame_id=0,pending_transition=None,
        context_saved=0,context_rejected=0,saved_auto=0,live_laboratory=LiveLaboratory(db),
        status=Mock(),overlay=Mock(),detect_label=Mock(),detect_help=Mock(),learning_summary=Mock(),
        refresh_strategy=Mock(),refresh_stats_now=Mock(),dashboard=None,winfo_exists=lambda:False)
    app.record_learning=lambda *a,**kw:Forgely.record_learning(app,*a,**kw)
    rec.ensure_session(item='Test',targets={'Force':2},jets={'Force':0},pool=5,
                       prices={'Fo':36},scope=capture_scope(app))
    rec.forecast('Fo',{'SC':50,'SN':50,'EC':0},frame=10,scope=capture_scope(app))
    event=Observation('Fo','SC','','confirmed')
    app.messages.put(('accepted_event',AcceptedRuneEvent(11,event,'Test',mailbox,0,'A')))
    transition={'rune':'Fo','outcome':'SC','before':{'jet':{'Force':0},'pool':5},
                'after':{'jet':{'Force':1},'pool':5},'event_frame_id':event_frame}
    app.messages.put(('worker_message',(mailbox,0,'A','learning_transition',('Test',transition))))
    with patch('forgely.insert_observation',side_effect=lambda *a,**kw:insert_observation(*a,db_file=db,**kw)), \
         patch('forgely.save_transition',side_effect=lambda *a,**kw:save_transition(*a,db_file=db,**kw)), \
         patch('forgely.complete_learning_profile',return_value={'Force':100}):
        while not app.messages.empty():Forgely.process_messages(app)
    result=rec.finish(jets={'Force':1},pool=5,confirmed=True)
    assert app.context_saved==expected
    assert result['prediction_evaluation']['n']==expected
    assert result['learning']['qualified_transitions']==expected


def test_budget_alert_keeps_advice_by_default_and_stop_is_explicit():
    from forgely_pricing import budget_proposal
    from forgely_decision import Proposal
    proposal=Proposal('Fo','fm_classique','Fo','Conseil confirmé','test',{'prediction':{'SC':50}})
    cost={'known_cost':120,'complete':True,'unpriced_attempts':0}
    alerted=budget_proposal(proposal,{'budget_kamas':100},cost)
    assert alerted.rune=='Fo' and 'budget' in alerted.explanation.lower()
    assert alerted.estimates['prediction']==proposal.estimates['prediction']
    stopped=budget_proposal(proposal,{'budget_kamas':100,'stop_at_budget':True},cost)
    assert stopped.rune is None and stopped.kind=='bloqué'
    partial=budget_proposal(proposal,{'budget_kamas':100},dict(cost,complete=False,unpriced_attempts=2))
    assert partial.rune=='Fo' and 'incomplet' in partial.explanation.lower()


def test_budget_stop_option_survives_settings_without_changing_legacy_defaults(tmp_path):
    from forgely_tools import read_settings,save_settings
    path=tmp_path/'preferences.json'
    assert 'stop_at_budget' not in read_settings(path)
    save_settings({'strategy':'Chances maximales','prices':{},'budget_kamas':100,'stop_at_budget':True},path)
    assert read_settings(path)['stop_at_budget'] is True
    save_settings({'stop_at_budget':False},path)
    assert read_settings(path)['stop_at_budget'] is False


def test_dynamic_simulator_uses_current_pc_goals_instead_of_stale_plan():
    from forgely_measured_goals import MeasuredGoals
    from forgely_simulation_ui import confirmed_context
    goals=MeasuredGoals();goals.targets={'Force':50}
    app=SimpleNamespace(active_equipment_verified=True,item=SimpleNamespace(get=lambda:'Test'),
        measured_goals=goals,plan={'item':'Autre','stats':{'Vitalité':{'target':300}}},
        live_after_fusion=True,live_jet=None,live_pool=None)
    with patch('forgely_measured_goals.current_snapshot',return_value=({'Force':10},20)), \
         patch('forgely_simulation_ui.natural_profile',return_value={'Force':100}), \
         patch('forgely_simulation_ui.read_settings',return_value={'prices':{'Fo':36},'strategy':'Chances maximales','budget_kamas':0}):
        context=confirmed_context(app)
    assert context['targets']=={'Force':50}
    assert context['jets']=={'Force':10} and context['pool']==20
    assert app.plan['item']=='Autre'


def test_video_calibration_receives_the_real_confirmed_pc_goals():
    from forgely_session_ui import review_tick
    from forgely_session_review import SessionRecorder
    from forgely_measured_goals import MeasuredGoals
    from unittest.mock import Mock
    goals=MeasuredGoals();goals.targets={'Force':50}
    app=SimpleNamespace(session_recorder=Mock(spec=SessionRecorder),measured_goals=goals,
        active_equipment_verified=True,item=SimpleNamespace(get=lambda:'Test'),
        plan={'item':'Autre','stats':{'Vitalité':{'target':300}}},
        live_after_fusion=True,live_jet=None,live_pool=None,latest_observation_id=12)
    app.session_recorder.active=None
    with patch('forgely_measured_goals.current_snapshot',return_value=({'Force':10},20)), \
         patch('forgely_session_ui.SessionRecorder',SessionRecorder), \
         patch('forgely_tools.read_settings',return_value={'prices':{'Fo':36}}):
        review_tick(app)
    assert app.session_recorder.ensure_session.call_args.kwargs['targets']=={'Force':50}
    assert app.session_recorder.ensure_session.call_args.kwargs['jets']=={'Force':10}
