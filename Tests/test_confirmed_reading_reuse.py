from types import SimpleNamespace
from unittest.mock import Mock,patch
import queue
import threading
from PIL import Image,ImageDraw


def test_identical_confirmed_pixels_reuse_reading_without_ocr():
    from forgely_copilot_continuity import ConfirmedAtelierRead,read_current_atelier
    from forgely import workshop_change_signature
    im=Image.new('RGB',(1648,928),'#333333')
    context=(object(),'DOFUS',123,im.size)
    reading=object();ocr=Mock(return_value=object())
    cached=ConfirmedAtelierRead(context,workshop_change_signature(im),reading,({'Force':38},4.9))
    result,reused=read_current_atelier(cached,context,workshop_change_signature(im.copy()),ocr)
    assert result is reading and reused
    ocr.assert_not_called()
    # Changed jet, pool, history, rune selection or artwork must not reuse it.
    for box in ((490,223,510,240),(880,280,940,320),(620,190,640,200),
                (300,350,320,380),(650,185,670,205)):
        changed=im.copy();ImageDraw.Draw(changed).rectangle(box,fill='white')
        result,reused=read_current_atelier(cached,context,workshop_change_signature(changed),ocr)
        assert not reused and result is ocr.return_value
    _,reused=read_current_atelier(cached,(context[0],'OTHER',123,im.size),cached.signature,ocr)
    assert not reused


def test_confirmed_unchanged_workshop_does_not_restart_ocr_every_twelve_seconds():
    from forgely import Forgely,LatestFrameMailbox,workshop_change_signature
    from forgely_copilot_continuity import ConfirmedAtelierRead
    im=Image.new('RGB',(1648,928),'#333333')
    signature=workshop_change_signature(im)
    stop=threading.Event();mailbox=LatestFrameMailbox()
    capture=Mock(last_handle=123);capture.capture.return_value=(im,'DOFUS')
    app=SimpleNamespace(stop_event=stop,confirmation_requested=threading.Event(),
        capture=capture,frame_mailbox=mailbox,messages=queue.Queue(),_capture_interval=0,
        _capture_gate_reference=signature,_capture_gate_last_sent_ns=100,
        _capture_gate_force_ns=12_000_000_000,_visual_changes_seen=0,
        _capture_gate_changes=0,_unchanged_frames_skipped=0,
        _capture_gate_identity=('DOFUS',123,im.size),
        _confirmed_atelier_read=ConfirmedAtelierRead((mailbox,'DOFUS',123,im.size),signature,object(),({'Force':38},4.9)))
    with patch('forgely.forgely_perf_ns',return_value=100_000_000_000), \
         patch.object(stop,'wait',side_effect=lambda *_:stop.set()):
        Forgely.capture_worker(app)
    assert mailbox.snapshot()[1] is None
    assert app._unchanged_frames_skipped==1


def test_observer_reuses_confirmed_capture_after_mask_without_calling_ocr():
    from forgely import Forgely,LatestFrameMailbox,workshop_change_signature
    from forgely_copilot_continuity import ConfirmedAtelierRead,read_current_atelier
    im=Image.new('RGB',(1648,928),'#333333')
    mailbox=LatestFrameMailbox();mailbox.publish(im,'DOFUS',1,0)
    stop=threading.Event();capture=Mock(last_handle=123)
    app=SimpleNamespace(stop_event=stop,frame_mailbox=mailbox,capture=capture,
        messages=queue.Queue(),last_capture_title='',latest_observation_id=0,
        history_delta_monitor=Mock(),
        _confirmed_atelier_read=ConfirmedAtelierRead((mailbox,'DOFUS',123,im.size),
            workshop_change_signature(im),object(),({'Force':38},4.9)))
    def reuse_then_stop(*args):
        result=read_current_atelier(*args)
        assert result[1]
        stop.set()
        return result
    with patch('forgely.read_current_atelier',side_effect=reuse_then_stop) as reuse, \
         patch('forgely.read_atelier') as ocr:
        Forgely.observer_worker(app)
    reuse.assert_called_once()
    ocr.assert_not_called()


def test_only_confirmed_unchanged_numeric_zones_survive_expiry():
    from forgely_zone_cache import ZoneCache
    image=Image.new('RGB',(32,32),'white')
    cache=ZoneCache(refresh_seconds=0)
    cache.remember('effects',image,'38 Force')
    cache.remember('reliquat',image,'4,9')
    cache.remember('history',image,'previous history')
    confirmed=tuple(cache.entries.items())
    cache.clear()
    cache.confirm_numeric(confirmed)
    ocr=Mock(return_value='new text')
    assert cache.read('effects',image,ocr)=='38 Force'
    assert cache.read('reliquat',image,ocr)=='4,9'
    ocr.assert_not_called()
    # Rune selection/history may change without requiring numeric-zone OCR.
    assert cache.read('history',image,ocr)=='new text'
    changed=image.copy();changed.putpixel((5,5),(0,0,0))
    assert cache.read('effects',changed,ocr)=='new text'
    assert ocr.call_count==2


def test_known_unchanged_logo_does_not_reidentify_after_rune_selection():
    from forgely import Forgely,LatestFrameMailbox
    from forgely_continuous_identity import CurrentSlotTracker
    from forgely_pipeline import VerifiedItemContext
    im=Image.new('RGB',(1648,928),'#333333')
    icon=Image.new('RGB',(32,32),'#38394e')
    ImageDraw.Draw(icon).ellipse((4,4,27,27),fill='red')
    tracker=CurrentSlotTracker()
    for i in range(3):tracker.observe(icon)
    stop=threading.Event();mailbox=LatestFrameMailbox();mailbox.publish(im,'DOFUS',1,0)
    app=SimpleNamespace(stop_event=stop,frame_mailbox=mailbox,messages=queue.Queue(),
                        active_equipment_verified=True,current_slot_tracker=tracker,
                        _verified_item_context=VerifiedItemContext(mailbox,0,'DOFUS',1,'known',icon,()))
    def same_icon(_):stop.set();return icon
    with patch('forgely.current_icon',side_effect=same_icon), \
         patch('forgely_item_identity.ItemIdentityReader') as reader:
        Forgely.item_identity_worker(app)
    reader.return_value.read.assert_not_called()
