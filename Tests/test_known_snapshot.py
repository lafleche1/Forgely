from types import SimpleNamespace
from PIL import Image,ImageDraw
from forgely import LatestFrameMailbox
from forgely_pipeline import VerifiedItemContext
from forgely_measured_goals import MeasuredGoals,current_snapshot
from forgely_workshop_readings import WorkshopReadings


def known_app():
    mailbox=LatestFrameMailbox();context=(mailbox,mailbox.generation(),'DOFUS')
    icon=Image.new('RGB',(32,32),'#38394e');ImageDraw.Draw(icon).ellipse((4,4,27,27),fill='red')
    goals=MeasuredGoals();goals.observe_slot(icon,(),(mailbox,'DOFUS'))
    readings=WorkshopReadings(required_frames=2);readings.configure((context,'Test'),{'Force'})
    for i in range(2):readings.observe({'Force':38},0,sequence=i)
    return SimpleNamespace(frame_mailbox=mailbox,last_capture_title='DOFUS',workshop_active=True,
        active_equipment_verified=True,item=SimpleNamespace(get=lambda:'Test'),
        _verified_item_context=VerifiedItemContext(*context,0,'Test',icon,()),
        measured_goals=goals,workshop_readings=readings,fast_slot_evidence=None)


def test_confirmed_object_and_complete_jet_do_not_wait_for_second_icon_validator():
    assert current_snapshot(known_app())==({'Force':38},0)


def test_confirmed_numbers_are_never_reused_for_other_item_or_account():
    app=known_app();app.item.get=lambda:'Other item'
    assert current_snapshot(app) is None
    app=known_app();app.frame_mailbox.invalidate('changed account')
    assert current_snapshot(app) is None
