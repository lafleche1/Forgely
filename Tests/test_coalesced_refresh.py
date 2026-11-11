import queue
from unittest.mock import Mock,patch
from types import SimpleNamespace
from forgely import Forgely
from forgely_workshop_readings import WorkshopReadings


def test_three_queued_measurements_render_one_final_advice():
    app=Mock();app.messages=queue.Queue();app.winfo_exists.return_value=False
    app.workshop_readings=WorkshopReadings();app.active_equipment_verified=False
    app.manual_equipment=None;app.measured_goals=None;app._copilot_masked=False
    app.observation_only=False;app.plan=None;app.item.get.return_value=''
    app.equipment_mode.get.return_value='automatic'
    from forgely_decision import Proposal
    app.current_proposal=Proposal(None,'suspendu','Lecture','Lecture','')
    app.live_jet=None;app.live_pool=None;app.live_after_fusion=True
    app.strategy_current.return_value=app.current_proposal
    app.refresh_strategy=lambda:Forgely.refresh_strategy(app)
    app.render_plan=lambda *args,**kwargs:Forgely.render_plan(app,*args,**kwargs)
    for _ in range(3):app.messages.put(('atelier_read',({'Force':38},0)))
    with patch.object(Forgely,'_refresh_strategy_now',create=True) as calculate, \
         patch.object(Forgely,'strategy_current',return_value=None):
        Forgely.process_messages(app)
    calculate.assert_called_once()
    assert app.workshop_readings.snapshot()==({'Force':38},0)


def test_idle_message_pump_does_not_redraw_the_dashboard():
    app=Mock();app.messages=queue.Queue();app.winfo_exists.return_value=False
    Forgely.process_messages(app)
    app.dashboard.sync.assert_not_called()


def test_session_recording_sees_stable_read_before_rune_in_same_batch():
    from forgely_context import FusionPairing
    from forgely_detection import Observation
    app=Mock();app.messages=queue.Queue();app.winfo_exists.return_value=False
    app.workshop_readings=WorkshopReadings();app.active_equipment_verified=True
    app.manual_equipment=None;app.measured_goals=None;app._copilot_masked=False
    app.item.get.return_value='Test';app.live_jet=None;app.live_pool=None
    app.live_after_fusion=True;app.pending_transition=None;app.fusion_pairing=FusionPairing()
    app.last_full_event_frame_id=app.last_displayed_result_frame_id=app.latest_observation_id=0
    app.saved_auto=0;app.refresh_strategy=lambda:Forgely.refresh_strategy(app)
    opened=False;events=[]
    def record_boundary(*args):
        nonlocal opened
        if app.live_jet is not None:opened=True
    def record_event(*args):
        if opened:events.append(args[1])
    for _ in range(3):app.messages.put(('atelier_read',({'Force':38},0)))
    app.messages.put(('auto_event_frame',(10,Observation('Fo','SC','','confirmed'))))
    with patch('forgely_vision_guidance.reference_for',return_value={'Force':(0,40)}), \
         patch('forgely.review_tick',side_effect=record_boundary), \
         patch('forgely.review_event',side_effect=record_event), \
         patch('forgely.insert_observation',return_value=1), \
         patch.object(Forgely,'_refresh_strategy_now'):
        Forgely.process_messages(app)
    assert events==[1]
