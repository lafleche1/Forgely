from types import SimpleNamespace
from unittest.mock import Mock,patch
import threading,queue
from PIL import Image,ImageDraw


def test_old_confirmation_cannot_disable_refresh_of_a_new_partial_frame():
    from forgely import Forgely,LatestFrameMailbox,workshop_change_signature
    from forgely_copilot_continuity import ConfirmedAtelierRead
    old=Image.new('RGB',(1648,928),'#333333');new=old.copy()
    ImageDraw.Draw(new).rectangle((710,400,760,420),fill='white')
    stop=threading.Event();mailbox=LatestFrameMailbox()
    capture=Mock(last_handle=123);capture.capture.return_value=(new,'DOFUS')
    app=SimpleNamespace(stop_event=stop,confirmation_requested=threading.Event(),
        capture=capture,frame_mailbox=mailbox,messages=queue.Queue(),_capture_interval=0,
        _capture_gate_reference=workshop_change_signature(new),_capture_gate_last_sent_ns=100,
        _capture_gate_force_ns=12_000_000_000,_visual_changes_seen=0,
        _capture_gate_changes=0,_unchanged_frames_skipped=0,
        _capture_gate_identity=('DOFUS',123,new.size),
        _confirmed_atelier_read=ConfirmedAtelierRead((mailbox,'DOFUS',123,old.size),
            workshop_change_signature(old),object(),({'Force':38},4.7)))
    with patch('forgely.forgely_perf_ns',return_value=100_000_000_000), \
         patch.object(stop,'wait',side_effect=lambda *_:stop.set()):
        Forgely.capture_worker(app)
    assert mailbox.snapshot()[1] is not None


def test_stable_partial_jet_still_requests_the_missing_lines():
    from forgely import Forgely
    from forgely_workshop_readings import WorkshopReadings
    r=WorkshopReadings();r.configure('item',{'Force','Vitalité'})
    for _ in range(3):r.observe({'Force':38},4.4)
    app=Mock();app.messages=queue.Queue();app.winfo_exists.return_value=False
    app.workshop_readings=r;app.active_equipment_verified=False;app.manual_equipment=None
    app.measured_goals=None;app._copilot_masked=False;app.live_jet=None
    app.confirmation_requested=threading.Event()
    app.messages.put(('atelier_read',({'Force':38},4.4)))
    Forgely.process_messages(app)
    assert app.confirmation_requested.is_set()


def test_incomplete_zone_retry_is_bounded_and_does_not_touch_other_zones():
    from forgely_zone_cache import ZoneCache
    c=ZoneCache();im=Image.new('RGB',(30,30),'white')
    with patch('forgely_zone_cache.monotonic',return_value=0):
        c.remember('current_jet',im,'38 Force')
        c.remember('reliquat',im,'4,4')
    with patch('forgely_zone_cache.monotonic',return_value=.5):
        assert not c.retry_unresolved('current_jet')
    with patch('forgely_zone_cache.monotonic',return_value=1.1):
        assert c.retry_unresolved('current_jet')
        assert not c.retry_unresolved('current_jet')
    assert c.get('reliquat')=='4,4'
