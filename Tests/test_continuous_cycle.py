from types import SimpleNamespace
from unittest.mock import Mock,patch
from forgely import Forgely
from forgely_workshop_readings import WorkshopReadings
from forgely_copilote import player_signal


def test_known_workshop_moves_through_calculation_without_stop_state():
    r=WorkshopReadings(required_frames=2);r.configure('item',{'Force'})
    app=SimpleNamespace(observation_only=False,running=True,workshop_active=True,
        active_equipment_verified=True,workshop_readings=r,_copilot_masked=True)
    proposal=Forgely._strategy_current(app)
    assert proposal.kind=='calcul' and proposal.summary=='Calcul…'
    signal=player_signal(proposal,{}, {'Force':40},None,True,True)
    assert signal.title=='Lecture à confirmer' and not signal.stop
    assert not r.observe({'Force':38},4.4,sequence=1)
    assert r.observe({'Force':38},4.4,sequence=2)


def test_actual_closed_workshop_still_has_a_real_reason():
    app=SimpleNamespace(observation_only=False,running=True,workshop_active=False)
    p=Forgely._strategy_current(app)
    assert p.kind=='suspendu' and p.summary=='Lecture du jeu en attente'


def test_two_fresh_reads_produce_next_rune_after_each_calculation():
    import queue
    from forgely_equipment_catalog import EquipmentCatalog
    from forgely_vision_guidance import reference_for
    from forgely_context import FusionPairing
    equipment=EquipmentCatalog().search('Anneau','cycloide')[0]
    bounds=reference_for(equipment.identity_name);base={k:max(v) for k,v in bounds.items()}
    a=Mock();a.messages=queue.Queue();a.winfo_exists.return_value=False
    a.item.get.return_value=equipment.identity_name
    a.running=a.workshop_active=a.active_equipment_verified=True
    a.observation_only=False;a.manual_equipment=None;a.measured_goals=None;a._copilot_masked=False
    a.workshop_readings=WorkshopReadings(required_frames=2)
    a.fusion_pairing=FusionPairing();a.pending_transition=None
    a.live_jet=None;a.live_pool=None;a.live_after_fusion=True
    a.plan={'item':equipment.identity_name,'stats':{'Force':{'target':40}}}
    a.live_laboratory.estimate.return_value=None
    with patch('forgely.read_settings',return_value={}), \
         patch('forgely.learning_sources',return_value=({},None)), \
         patch('forgely.natural_bounds',return_value=bounds), \
         patch('forgely.complete_learning_profile',return_value=base):
        for value in (38,39):
            assert Forgely._strategy_current(a).kind=='calcul'
            jet={**base,'Force':value}
            a.messages.put(('atelier_read',(jet,4.4)));Forgely.process_messages(a)
            assert Forgely._strategy_current(a).kind=='calcul'
            a.messages.put(('atelier_read',(jet,4.4)));Forgely.process_messages(a)
            assert Forgely._strategy_current(a).rune is not None
            a.workshop_readings.invalidate();a.live_jet=None;a.live_pool=None;a.live_after_fusion=True
