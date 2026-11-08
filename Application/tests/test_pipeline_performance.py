from forgely_context import FusionPairing
import queue
import threading
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PIL import Image, ImageDraw
from forgely import (Forgely, LatestFrameMailbox, workshop_change_signature,
                     workshop_significantly_changed)
from forgely_pipeline import FrameMessageSink


def test_rune_panel_only_change_wakes_capture():
    old = Image.new('RGB', (1648, 928), '#333333')
    new = old.copy()
    ImageDraw.Draw(new).rectangle((880, 280, 940, 320), fill='white')
    assert workshop_significantly_changed(workshop_change_signature(old), workshop_change_signature(new))


def test_upper_effect_row_only_change_wakes_capture():
    old = Image.new('RGB', (1648, 928), '#333333')
    new = old.copy()
    ImageDraw.Draw(new).rectangle((490, 223, 580, 245), fill='white')
    assert workshop_significantly_changed(workshop_change_signature(old), workshop_change_signature(new))


def test_mailbox_title_switch_invalidates_generation():
    m = LatestFrameMailbox()
    m.publish('pixels', 'Account A', 1, 1)
    generation = m.generation()
    m.publish('pixels', 'Account B', 2, 1)
    assert m.generation() > generation


def test_message_pump_schedules_faster_and_drains_bursts():
    obj = Mock()
    obj.messages = queue.Queue()
    obj.winfo_exists.return_value = True
    for _ in range(30):
        obj.messages.put(('error', 'test'))
    Forgely.process_messages(obj)
    assert obj.messages.qsize() < 20
    assert obj.after.call_args.args[0] <= 40
    assert obj.messages.qsize() == 0 or obj.after.call_args.args[0] <= 5


def test_old_worker_messages_are_ignored_after_context_invalidation():
    m = LatestFrameMailbox()
    m.publish('pixels', 'A', 1, 1)
    obj = Mock()
    obj.frame_mailbox = m
    obj.messages = queue.Queue()
    obj.winfo_exists.return_value = False
    obj.messages.put(('worker_message', (m, m.generation(), 'A', 'error', 'old error')))
    m.invalidate('closed')
    Forgely.process_messages(obj)
    obj.status.set.assert_not_called()


def test_current_worker_envelope_is_delivered():
    m = LatestFrameMailbox()
    m.publish('pixels', 'A', 1, 1)
    obj = Mock()
    obj.frame_mailbox = m
    obj.messages = queue.Queue()
    obj.winfo_exists.return_value = False
    obj.messages.put(('worker_message', (m, m.generation(), 'A', 'error', 'current')))
    Forgely.process_messages(obj)
    obj.status.set.assert_called_once_with('Capture : current')


def test_capture_context_change_publishes_identical_pixels():
    stop = threading.Event()
    mailbox = LatestFrameMailbox()
    mailbox.publish('same', 'A', 1, 0)
    capture = Mock(last_handle=20)
    capture.capture.return_value = ('same', 'B')
    obj = SimpleNamespace(stop_event=stop, confirmation_requested=threading.Event(),
        capture=capture, frame_mailbox=mailbox, messages=queue.Queue(), _capture_interval=0,
        _capture_gate_reference='same', _capture_gate_last_sent_ns=100,
        _capture_gate_force_ns=12_000_000_000, _visual_changes_seen=0,
        _capture_gate_changes=0, _unchanged_frames_skipped=0,
        _capture_gate_identity=('A', 10))
    with patch('forgely.workshop_change_signature', return_value='same'), \
         patch('forgely.workshop_significantly_changed', return_value=False), \
         patch('forgely.forgely_perf_ns', return_value=200), \
         patch.object(stop, 'wait', side_effect=lambda *_: stop.set()):
        Forgely.capture_worker(obj)
    assert mailbox.snapshot()[1][2] == 'B'


def test_sink_discards_invalidated_or_stopped_results():
    mailbox=LatestFrameMailbox()
    mailbox.publish('same','A',1,0)
    messages=queue.Queue()
    stop=threading.Event()
    sink=FrameMessageSink(messages,mailbox,mailbox.generation(),'A',stop)
    mailbox.invalidate('other account')
    sink.put(('auto_event_frame',(1,'old event')))
    assert messages.empty()
    sink=FrameMessageSink(messages,mailbox,mailbox.generation(),'A',stop)
    stop.set()
    sink.put(('auto_event_frame',(1,'old event')))
    assert messages.empty()


def test_wait_snapshot_binds_frame_and_context_and_wakes_on_invalidation():
    mailbox=LatestFrameMailbox()
    mailbox.publish('first','A',1,0)
    generation,frame=mailbox.wait_snapshot(0,threading.Event(),0)
    assert frame[1]=='first'
    assert generation==0
    mailbox.invalidate('closed')
    changed,frame=mailbox.wait_snapshot(1,threading.Event(),generation)
    assert changed>generation
    assert frame is None


def test_capture_reuses_thread_local_mss_and_closes_it():
    import forgely
    capture=forgely.GameCapture()
    shot=SimpleNamespace(size=(2,1),bgra=bytes([0,0,255,255,0,255,0,255]))
    session=Mock()
    session.grab.return_value=shot
    window=SimpleNamespace(left=0,top=0,width=2,height=1)
    with patch('mss.mss',return_value=session) as factory:
        first=capture._foreground_image(window)
        second=capture._foreground_image(window)
        assert first.tobytes()==second.tobytes()==bytes([255,0,0,0,255,0])
        assert factory.call_count==1
        capture.close()
        session.close.assert_called_once()
        capture._foreground_image(window)
        assert factory.call_count==2
        capture.close()


def test_full_ocr_invalidated_during_read_never_publishes_results():
    mailbox=LatestFrameMailbox()
    mailbox.publish('pixels','A',1,0)
    stop=threading.Event()
    obj=SimpleNamespace(stop_event=stop,frame_mailbox=mailbox,capture=Mock(),
                        messages=queue.Queue(),last_capture_title='',latest_observation_id=0,
                        history_delta_monitor=Mock())
    first=mailbox.snapshot()
    def next_frame(*_args):
        if mailbox.generation()==0:
            return first
        stop.set()
        return mailbox.snapshot()
    def invalidated_read(*_args):
        mailbox.invalidate('other account')
        return SimpleNamespace(active=True)
    with patch.object(mailbox,'wait_snapshot',side_effect=next_frame), \
         patch('forgely.read_atelier',side_effect=invalidated_read):
        Forgely.observer_worker(obj)
    assert obj.messages.empty()
    assert obj.latest_observation_id==0


def test_previous_observer_session_queued_message_is_ignored():
    old=LatestFrameMailbox();old.publish('pixels','A',1,0)
    obj=Mock(frame_mailbox=LatestFrameMailbox())
    obj.messages=queue.Queue()
    obj.winfo_exists.return_value=False
    obj.messages.put(('worker_message',(old,0,'A','error','old session')))
    Forgely.process_messages(obj)
    obj.status.set.assert_not_called()


def test_old_observer_cannot_reset_new_session_after_wakeup():
    old=LatestFrameMailbox();old.publish('pixels','A',1,0)
    stop=threading.Event()
    fresh_track=object();fresh_monitor=Mock()
    obj=SimpleNamespace(stop_event=stop,frame_mailbox=old,capture=Mock(),messages=queue.Queue(),
                        track=fresh_track,history_delta_monitor=fresh_monitor)
    def restart(*_args):
        stop.set();old.invalidate('stopped')
        obj.frame_mailbox=LatestFrameMailbox()
        return old.snapshot()
    with patch.object(old,'wait_snapshot',side_effect=restart):
        Forgely.observer_worker(obj)
    assert obj.track is fresh_track
    fresh_monitor.reset.assert_not_called()


def test_accepted_event_survives_restart_and_keeps_original_equipment():
    from forgely_pipeline import AcceptedRuneEvent
    old=LatestFrameMailbox();old.publish('pixels','A',1,0)
    event=SimpleNamespace(rune='Fo',outcome='SC',evidence='confirmed old result')
    receipt=AcceptedRuneEvent(1,event,'Old item',old,0,'A')
    obj=Mock(frame_mailbox=LatestFrameMailbox())
    obj.fusion_pairing=FusionPairing()
    obj.messages=queue.Queue();obj.messages.put(('accepted_event',receipt))
    obj.saved_auto=0;obj.live_jet={'Force':50};obj.live_pool=10
    obj.item.get.return_value='New item';obj.winfo_exists.return_value=False
    with patch('forgely.insert_observation') as insert,patch('forgely.insert_unassigned') as unknown:
        Forgely.process_messages(obj)
    insert.assert_called_once_with('Old item','Fo','SC','ocr_auto','confirmed old result')
    unknown.assert_not_called()
    assert obj.live_jet=={'Force':50}


def test_current_accepted_event_is_not_persisted_twice():
    from forgely_pipeline import AcceptedRuneEvent
    mailbox=LatestFrameMailbox();mailbox.publish('pixels','A',1,0)
    event=SimpleNamespace(rune='Fo',outcome='SC',evidence='confirmed current result')
    receipt=AcceptedRuneEvent(1,event,'Current item',mailbox,0,'A')
    obj=Mock(frame_mailbox=mailbox)
    obj.fusion_pairing=FusionPairing()
    obj.messages=queue.Queue();obj.messages.put(('accepted_event',receipt))
    obj.saved_auto=0;obj.live_jet={'Force':50};obj.live_pool=10
    obj.last_full_event_frame_id=0;obj.last_displayed_result_frame_id=0
    obj.item.get.return_value='Current item';obj.active_equipment_verified=True
    obj.winfo_exists.return_value=False
    with patch('forgely.insert_observation') as insert:
        Forgely.process_messages(obj)
    assert insert.call_count==1
    assert obj.saved_auto==1


def test_unbound_accepted_event_is_kept_as_unassigned():
    from forgely_pipeline import AcceptedRuneEvent
    mailbox=LatestFrameMailbox();mailbox.publish('pixels','A',1,0)
    receipt=AcceptedRuneEvent(1,SimpleNamespace(rune='Fo',outcome='EC',evidence='seen'),None,mailbox,0,'A')
    obj=Mock(frame_mailbox=mailbox)
    obj.fusion_pairing=FusionPairing()
    obj.messages=queue.Queue();obj.messages.put(('accepted_event',receipt))
    obj.winfo_exists.return_value=False
    with patch('forgely.insert_observation') as insert,patch('forgely.insert_unassigned') as unknown:
        Forgely.process_messages(obj)
    insert.assert_not_called()
    assert unknown.call_count==1


def test_receipt_binding_requires_prior_matching_context():
    from forgely_pipeline import VerifiedItemContext,bind_event_item
    mailbox=LatestFrameMailbox()
    icon=Image.new('RGB',(32,32),'gold')
    ImageDraw.Draw(icon).ellipse((5,5,27,27),fill='blue')
    context=VerifiedItemContext(mailbox,0,'A',2,'Known item',icon,())
    assert bind_event_item(context,mailbox,0,'A',3,icon,())=='Known item'
    assert bind_event_item(context,mailbox,0,'B',3,icon,()) is None
    assert bind_event_item(context,mailbox,1,'A',3,icon,()) is None
    assert bind_event_item(context,mailbox,0,'A',1,icon,()) is None
    assert bind_event_item(context,mailbox,0,'A',3,icon,(),name_hint='Different item') is None


def test_atomic_sink_preserves_accepted_receipt_after_later_invalidation():
    from forgely_pipeline import AcceptedRuneEvent
    mailbox=LatestFrameMailbox();mailbox.publish('pixels','A',1,0)
    messages=queue.Queue()
    sink=FrameMessageSink(messages,mailbox,0,'A',threading.Event())
    receipt=AcceptedRuneEvent(1,object(),'Known',mailbox,0,'A')
    sink.put(('accepted_event',receipt))
    mailbox.invalidate('closed')
    assert messages.get_nowait()==('accepted_event',receipt)

