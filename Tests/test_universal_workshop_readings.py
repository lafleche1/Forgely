from pathlib import Path
import pytest

from forgely_workshop_readings import WorkshopReadings


def test_catalogue_profiles_stabilize_without_minimum_or_sign_restrictions():
    from forgely_equipment_catalog import EquipmentCatalog, equipment_bounds
    from forgely_dofocus import canonical_stat
    tested=0
    for item in EquipmentCatalog().items:
        bounds=equipment_bounds(item)
        if not bounds:continue
        for scenario in ('minimum','maximum','zero','below_minimum'):
            jet={canonical_stat(stat):(min(pair) if scenario=='minimum' else max(pair)
                  if scenario=='maximum' else 0 if scenario=='zero' else min(pair)-1)
                 for stat,pair in bounds.items()}
            readings=WorkshopReadings()
            readings.configure(item.identity_name,bounds)
            for frame in range(3):
                stable=readings.observe(jet,0.0,sequence=frame)
            assert stable, (item.name,scenario,readings.waiting_reason)
            assert readings.snapshot()==(jet,0.0), (item.name,scenario)
        tested+=1
    assert tested>2500


def test_tetriste_diagnostic_uses_the_same_complete_reference_as_the_reader():
    from forgely_profile_guidance import compare
    jet={'Portée':1,'Force':-15,'Intelligence':-15,'Chance':-15,'Agilité':-15}
    report=compare('Amulette Tétriste',jet)
    assert 'Portée' in report['expected']
    assert report['extra']==[]
    assert report['missing']==[]


def test_waiting_for_pixels_is_not_displayed_as_a_running_calculation():
    from forgely_copilote import player_signal
    from forgely_decision import Proposal
    proposal=Proposal(None,'calcul','Calcul…','Reliquat à confirmer','lecture en cours')
    signal=player_signal(proposal,{}, {'Force':0}, None,True,True)
    assert signal.title=='Lecture à confirmer'
    assert signal.detail=='Reliquat à confirmer'
    from forgely_predictive import report_text
    compact=report_text(proposal,{}, {'Force':0},None,None,compact=True)
    assert 'Reliquat à confirmer' in compact
    assert 'Calcul…' not in compact


def test_real_tetriste_screenshot_reads_negative_lines_and_zero_pool():
    from PIL import Image
    from forgely_atelier import read_atelier,choose_reliquat
    from forgely_jet import parse_jet
    from forgely_ocr_backend import extract_text
    image=Image.open(Path(__file__).parent/'fixtures/workshop_tetriste_20261110.png')
    reading=read_atelier(image,extract_text,title_cache={},five_zones=True)
    assert reading.active
    jet=parse_jet(reading.effects)
    assert jet=={'Portée':1,'Force':-15,'Intelligence':-15,'Chance':-15,'Agilité':-15}
    assert choose_reliquat(reading.effects,reading.reliquat)==0.0


@pytest.mark.parametrize('color', [(220,65,65),(190,190,190)])
def test_workshop_detection_does_not_require_a_positive_green_stat(color):
    from PIL import Image
    import numpy as np
    from forgely_atelier import workshop_visual_fallback
    image=Image.open(Path(__file__).parent/'fixtures/workshop_tetriste_20261110.png').convert('RGB')
    pixels=np.array(image)
    r,g,b=pixels.astype(int).transpose(2,0,1)
    green=(g>=74)&(g*100>r*117)&(g*100>b*106)
    pixels[green]=color
    assert workshop_visual_fallback(Image.fromarray(pixels))


def test_actual_tetriste_jet_reaches_the_ui_through_three_noisy_capture_messages():
    import queue
    import threading
    from unittest.mock import Mock
    from PIL import Image
    from forgely import Forgely, LatestFrameMailbox, workshop_change_signature
    from forgely_copilot_continuity import ConfirmedAtelierRead,numeric_frame_signature
    image=Image.open(Path(__file__).parent/'fixtures/workshop_tetriste_20261110.png').convert('RGB')
    jet={'Portée':1,'Force':-15,'Intelligence':-15,'Chance':-15,'Agilité':-15}
    mailbox=LatestFrameMailbox()
    app=Mock();app.frame_mailbox=mailbox;app.capture.last_handle=123
    app.item.get.return_value='Amulette Tétriste';app.active_equipment_verified=True
    app.messages=queue.Queue();app.workshop_readings=WorkshopReadings()
    app.manual_equipment=None;app.measured_goals=None;app.fusion_pairing=None
    app.pending_transition=None;app.live_jet=app.live_pool=None
    app.latest_observation_id=0;app.dashboard=None
    app.winfo_exists.return_value=False
    app.confirmation_requested=threading.Event()
    context=(mailbox,'DOFUS',123,image.size)
    for frame in range(1,4):
        delivery=ConfirmedAtelierRead(context,workshop_change_signature(image),None,
            (dict(jet),0.0),numeric_signature=numeric_frame_signature(image))
        latest=image.convert('RGBA' if frame%2 else 'RGB')
        rgb=image.getpixel((710,800))
        latest.putpixel((710,800),tuple(min(255,c+1) for c in rgb)+( (255,) if latest.mode=='RGBA' else ()))
        mailbox.publish(latest,'DOFUS',frame,0)
        app.messages.put(('worker_message',(mailbox,mailbox.generation(),'DOFUS',
            'observation',(frame,1,'atelier_read',(dict(jet),0.0,delivery)))))
        Forgely.process_messages(app)
    assert app.workshop_readings.snapshot()==(jet,0.0)
    assert app.live_jet==jet and app.live_pool==0.0
    assert app._copilot_masked is False
