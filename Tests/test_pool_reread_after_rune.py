import threading,queue
from types import SimpleNamespace
from unittest.mock import Mock,patch
from PIL import Image
from forgely import Forgely,LatestFrameMailbox,workshop_change_signature
from forgely_copilot_continuity import ConfirmedAtelierRead,read_current_atelier
from forgely_zone_cache import ZoneCache


def test_rune_forces_pool_reader_even_when_pixels_and_previous_value_match():
    image=Image.new('RGB',(1648,928),'#333333');pool=Image.new('RGB',(80,30),'white')
    mailbox=LatestFrameMailbox();mailbox.publish(image,'DOFUS',1,0)
    cache=ZoneCache();cache.remember('reliquat',pool,'4,7')
    stop=threading.Event();request=threading.Event();request.set()
    confirmed=ConfirmedAtelierRead((mailbox,'DOFUS',123,image.size),
        workshop_change_signature(image),object(),({'Force':38},4.7),tuple(cache.entries.items()))
    app=SimpleNamespace(stop_event=stop,frame_mailbox=mailbox,capture=Mock(last_handle=123),
        messages=queue.Queue(),last_capture_title='',latest_observation_id=0,
        pool_refresh_requested=request,_confirmed_atelier_read=confirmed)
    reader=Mock(return_value='4,7')
    def read_numeric(im,ocr,zones,titles,**kwargs):
        assert kwargs['pool_ocr_token'] is not None
        zones.read('reliquat',pool,reader)
        return object()
    def done(*args):
        result=read_current_atelier(*args);stop.set();return result
    with patch('forgely.read_atelier',side_effect=read_numeric), \
         patch('forgely.read_current_atelier',side_effect=done):
        Forgely.observer_worker(app)
    reader.assert_called_once()
    assert not request.is_set()


def test_new_pool_token_bypasses_shared_ocr_cache_for_identical_digits():
    from forgely_ocr_backend import extract_text
    from time import monotonic_ns
    patch_image=Image.new('RGB',(80,30),'white')
    command='pool-reread-test-'+str(monotonic_ns())
    with patch('forgely_ocr_backend._recognize',return_value='4,7') as engine:
        patch_image.info['forgely_pool_ocr_token']=1
        assert extract_text(patch_image,command)=='4,7'
        patch_image.info['forgely_pool_ocr_token']=2
        assert extract_text(patch_image,command)=='4,7'
    assert engine.call_count==2


def test_corrected_pool_is_not_replaced_by_old_confirmation_on_next_frame():
    from forgely_pipeline import VerifiedItemContext
    from PIL import ImageDraw
    image=Image.new('RGB',(1648,928),'#333333');pool=Image.new('RGB',(80,30),'white')
    icon=Image.new('RGB',(32,32),'#38394e');ImageDraw.Draw(icon).ellipse((4,4,27,27),fill='red')
    mailbox=LatestFrameMailbox();mailbox.publish(image,'DOFUS',1,0)
    cache=ZoneCache();cache.remember('reliquat',pool,'4,7')
    old=SimpleNamespace(active=True,readable=True,effects='38 Force',reliquat='reliquat : 4,7',
        history='',runes='',title='Joaillomager',reason='',timings={},recovery_pending=False)
    fresh=SimpleNamespace(**{**vars(old),'reliquat':'reliquat : 4,4'})
    stop=threading.Event();request=threading.Event();request.set()
    confirmed=ConfirmedAtelierRead((mailbox,'DOFUS',123,image.size),
        workshop_change_signature(image),old,({'Force':38},4.7),tuple(cache.entries.items()))
    app=Mock();app.frame_mailbox=mailbox;app.stop_event=stop;app.messages=queue.Queue()
    app.capture=Mock(last_handle=123,manual_handle=None);app.capture_debug_requested=threading.Event()
    app.pool_refresh_requested=request;app._confirmed_atelier_read=confirmed
    app._verified_item_context=VerifiedItemContext(mailbox,0,'DOFUS',0,'Test',icon,())
    app.active_equipment_verified=True;app.item.get.return_value='Test';app.manual_equipment=None
    app.rune_center=None;app._ocr_stale_frames=app.completed_ocr_attempts=app.skipped_frames=0
    frames=[(0,(i,image,'DOFUS',1,0)) for i in (1,2)]
    def next_frame(*args):
        if frames:return frames.pop(0)
        stop.set();return 0,None
    def read_numeric(im,ocr,zones,titles,**kwargs):
        zones.read('reliquat',pool,lambda _: '4,4')
        return fresh
    with patch.object(mailbox,'wait_snapshot',side_effect=next_frame), \
         patch('forgely.read_atelier',side_effect=read_numeric), \
         patch('forgely.current_icon',return_value=icon), \
         patch('forgely_history_summary.summarize_history',side_effect=RuntimeError('skip secondary work')):
        Forgely.observer_worker(app)
    values=[]
    while not app.messages.empty():
        kind,payload=app.messages.get()
        if kind=='worker_message':_,_,_,kind,payload=payload
        if kind=='observation' and payload[2]=='atelier_read':values.append(payload[3][1])
    assert values==[4.4,4.4]
