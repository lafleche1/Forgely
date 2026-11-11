import queue,threading
from types import SimpleNamespace
from unittest.mock import Mock,patch
from PIL import Image,ImageDraw
from forgely import Forgely,LatestFrameMailbox
from forgely_pipeline import VerifiedItemContext
import pytest


@pytest.mark.parametrize('identity_matches',[True,False])
def test_numeric_reading_is_published_before_identity_and_history_work(identity_matches):
    mailbox=LatestFrameMailbox();image=Image.new('RGB',(1648,928),'#38394e')
    mailbox.publish(image,'DOFUS',1,0)
    app=Mock();app.frame_mailbox=mailbox;app.stop_event=threading.Event()
    app.capture=Mock(last_handle=123,manual_handle=None)
    app.messages=queue.Queue();app.capture_debug_requested=threading.Event()
    app._confirmed_atelier_read=None
    icon=image.resize((32,32))
    ImageDraw.Draw(icon).ellipse((4,4,27,27),fill='red')
    app.active_equipment_verified=True;app.item.get.return_value='known item'
    reference=icon if identity_matches else Image.new('RGB',(32,32),'white')
    app._verified_item_context=VerifiedItemContext(mailbox,0,'DOFUS',0,'known item',reference,())
    app.manual_equipment=None;app.latest_observation_id=0;app.completed_ocr_attempts=0
    app._ocr_stale_frames=0;app.occluded_observations=0
    app.skipped_frames=0
    app.rune_center=None
    atelier=SimpleNamespace(active=True,readable=True,effects='38 Force',reliquat='reliquat : 4,7',
        history='',runes='',title='Joaillomager',reason='',timings={},recovery_pending=False)
    def stop_before_secondary_work(*args,**kwargs):
        app.stop_event.set()
        raise RuntimeError('secondary work deliberately stopped')
    with patch('forgely.read_atelier',return_value=atelier), \
         patch('forgely.current_icon',return_value=icon), \
         patch('forgely.slot_equipment_decision',return_value=SimpleNamespace(name=None)), \
         patch('forgely_history_summary.summarize_history',side_effect=stop_before_secondary_work):
        Forgely.observer_worker(app)
    numeric=[]
    while not app.messages.empty():
        kind,payload=app.messages.get()
        if kind=='worker_message':
            _,_,_,kind,payload=payload
        if kind=='observation' and payload[2]=='atelier_read':numeric.append(payload[3][:2])
    assert numeric==([({'Force':38},4.7)] if identity_matches else [])
