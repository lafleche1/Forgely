from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from PIL import Image


@pytest.mark.parametrize('mode',['manual','automatic'])
def test_same_confirmed_item_uses_same_numeric_state(mode):
    from forgely_live_equipment import bind_confirmed_equipment
    from forgely_pipeline import VerifiedItemContext
    from forgely_workshop_readings import WorkshopReadings
    from forgely_vision_guidance import reference_for
    name="Talisman d'Elya Wood"
    jet={'Vitalité':133,'Intelligence':14,'Sagesse':40,'PA':1,'Soins':8,
         '% Résistance Eau':5,'% Résistance Air':6,'Résistance Terre':11,'Résistance Feu':13}
    readings=WorkshopReadings();readings.configure('same item',reference_for(name))
    for i in range(3):readings.observe(jet,0,sequence=i)
    app=SimpleNamespace(item=Mock(),workshop_readings=readings,pending_transition=None,
                        active_equipment_verified=False,mode=mode)
    context=(object(),1,'DOFUS');icon=Image.new('RGB',(32,32),'red')
    bind_confirmed_equipment(app,name,icon,(),context,4)
    assert app.active_equipment_verified
    assert app.live_jet==jet and app.live_pool==0
    assert app.live_after_fusion is False
    assert isinstance(app._verified_item_context,VerifiedItemContext)


def test_binding_never_turns_partial_numbers_into_a_complete_jet():
    from forgely_live_equipment import bind_confirmed_equipment
    from forgely_workshop_readings import WorkshopReadings
    readings=WorkshopReadings();readings.configure('item',{'Force','Vitalité'})
    for _ in range(3):readings.observe({'Force':38},0)
    app=SimpleNamespace(item=Mock(),workshop_readings=readings,pending_transition=None,
                        live_jet=None,live_pool=None,live_after_fusion=True)
    bind_confirmed_equipment(app,'item',Image.new('RGB',(32,32),'red'),(),None,3)
    assert app.live_jet is None and app.live_after_fusion


@pytest.mark.parametrize('mode',['manual','automatic'])
def test_complete_talisman_reading_clears_doubt_in_both_modes(mode):
    import queue
    from forgely import Forgely
    from forgely_context import FusionPairing
    from forgely_equipment_catalog import EquipmentCatalog
    from forgely_equipment_session import ManualEquipmentSession
    from forgely_workshop_readings import WorkshopReadings
    app=Mock();app.messages=queue.Queue();app.winfo_exists.return_value=False
    equipment=next(e for e in EquipmentCatalog().items if e.name=="Talisman d'Elya Wood")
    app.item.get.return_value=equipment.identity_name
    app.active_equipment_verified=True
    app.manual_equipment=ManualEquipmentSession(equipment) if mode=='manual' else None
    app.measured_goals=None;app.workshop_readings=WorkshopReadings()
    app.fusion_pairing=FusionPairing();app.pending_transition=None
    app.live_jet=None;app.live_pool=None;app.live_after_fusion=True;app._copilot_masked=True
    jet={'Vitalité':133,'Intelligence':14,'Sagesse':40,'PA':1,'Soins':8,
         '% Résistance Eau':5,'% Résistance Air':6,'Résistance Terre':11,'Résistance Feu':13}
    for _ in range(3):app.messages.put(('atelier_read',(jet,0)))
    Forgely.process_messages(app)
    assert app._copilot_masked is False
    assert app.live_jet==jet and app.live_pool==0
    assert app.workshop_readings.snapshot()==(jet,0)
