import queue
import pytest
from unittest.mock import Mock,patch
from forgely import Forgely
from forgely_detection import Observation
from forgely_workshop_readings import WorkshopReadings
from forgely_context import FusionPairing


@pytest.mark.parametrize('numeric_frame',[10,12])
def test_late_history_result_does_not_discard_newer_confirmed_jet(numeric_frame):
    app=Mock();app.messages=queue.Queue();app.winfo_exists.return_value=False
    app.last_full_event_frame_id=0;app.last_displayed_result_frame_id=0
    app.workshop_readings=WorkshopReadings()
    for _ in range(3):app.workshop_readings.observe({'Force':39},1)
    app._stable_numeric_frame=(None,numeric_frame,'objet')
    app.live_jet={'Force':39};app.live_pool=1;app.live_after_fusion=False
    app.fusion_pairing=FusionPairing();app.active_equipment_verified=True
    app.item.get.return_value='objet';app.saved_auto=0
    app.messages.put(('auto_event_frame',(10,Observation('Fo','SC','','confirmed'))))
    with patch('forgely.insert_observation'),patch('forgely.review_event'):
        Forgely.process_messages(app)
    assert app.live_jet=={'Force':39}
    assert app.live_pool==1
    assert app.workshop_readings.snapshot()==({'Force':39},1)
    app.refresh_strategy.assert_called()


def test_new_rune_still_suspends_pre_rune_snapshot():
    from forgely_copilot_continuity import numeric_snapshot_covers
    app=Mock();app._stable_numeric_frame=(None,9,'objet')
    app.item.get.return_value='objet';app.live_after_fusion=False
    assert not numeric_snapshot_covers(app,None,10)
    app._stable_numeric_frame=(('old account',),12,'objet')
    assert not numeric_snapshot_covers(app,None,10)


@pytest.mark.parametrize('mode',['manual','automatic'])
def test_each_of_three_changed_jets_recalculates_advice(mode):
    from forgely_equipment_catalog import EquipmentCatalog
    from forgely_equipment_session import ManualEquipmentSession
    app=Mock();app.messages=queue.Queue();app.winfo_exists.return_value=False
    equipment=EquipmentCatalog().search('Anneau','cycloide')[0]
    from forgely_vision_guidance import reference_for
    bounds=reference_for(equipment.identity_name)
    base={k:max(v) for k,v in bounds.items()}
    app.manual_equipment=ManualEquipmentSession(equipment) if mode=='manual' else None
    app.item.get.return_value=equipment.identity_name
    app.active_equipment_verified=True;app.observation_only=False;app.measured_goals=None
    app.workshop_readings=WorkshopReadings();app.fusion_pairing=FusionPairing()
    app.pending_transition=None;app.live_jet=None;app.live_pool=None
    app.live_after_fusion=True;app._copilot_masked=False
    app.plan={'item':equipment.identity_name,'stats':{'Force':{'target':40}}}
    app.live_laboratory.estimate.return_value=None
    calculated=[]
    def refresh():
        proposal=Forgely._strategy_current(app)
        if app.live_jet is not None:calculated.append((dict(app.live_jet),proposal))
    app.refresh_strategy.side_effect=refresh
    with patch('forgely_vision_guidance.reference_for',return_value=bounds), \
         patch('forgely.read_settings',return_value={}), \
         patch('forgely.held_advice',return_value=None), \
         patch('forgely.natural_bounds',return_value=bounds), \
         patch('forgely.complete_learning_profile',return_value=base), \
         patch('forgely.learning_sources',return_value=({},None)):
        for value in (38,39,40):
            jet={**base,'Force':value}
            for _ in range(3):app.messages.put(('atelier_read',(jet,1)))
            Forgely.process_messages(app)
            assert calculated[-1][0]==jet
    assert calculated[0][1].rune
    assert calculated[-1][1].rune is None
