import threading
import cv2
import numpy as np
import pytest
from forgely_video_analysis import Timeline, video_info, frame_at, analyze_video, validate_zones, DEFAULT_ZONES
from forgely_video_store import VideoStore


def read(pa, history, pool=17):
    return {'item_id': 2469, 'natural_max': {'PA': 1}, 'jet': {'PA': pa},
            'pool': pool, 'rune': 'Ga Pa', 'history': history, 'raw': {}}


OLD = 'Gelano\nÉchec ancien A\nÉchec ancien B\nÉchec ancien C'
NEW = 'Gelano\nSuccès critique Ga Pa\nÉchec ancien A\nÉchec ancien B\nÉchec ancien C'


def feed(timeline, pa, history, start):
    for i in range(3):
        timeline.observe(start + i*.2, read(pa, history), f'{start+i}.png')


def test_pairing_freezes_pre_state_and_never_counts_persistent_history_twice():
    t = Timeline()
    feed(t, 0, OLD, 0)
    feed(t, 1, NEW, 1)
    feed(t, 1, NEW, 2)
    t.finish()
    assert len(t.events) == 1
    event = t.events[0]
    assert event['before']['jet'] == {'PA': 0}
    assert event['after']['jet'] == {'PA': 1}
    assert event['event_confirmed'] and event['stable']


def test_multi_event_and_cut_never_create_eligible_pair():
    t = Timeline(); feed(t, 0, OLD, 0)
    twice = NEW.replace('Succès critique Ga Pa', 'Succès critique Ga Pa\nÉchec Ga Pa')
    feed(t, 1, twice, 1); t.finish()
    assert t.events and 'multiple_events' in t.events[0]['issues']
    t = Timeline(); feed(t, 0, OLD, 0); t.boundary('cut')
    feed(t, 1, NEW, 1); t.finish()
    assert not any(e['event_confirmed'] for e in t.events)


def test_unknown_pool_remains_unknown():
    t = Timeline()
    for time, pa, hist in [(0,0,OLD),(.2,0,OLD),(1,1,NEW),(1.2,1,NEW),(1.4,1,NEW)]:
        t.observe(time, read(pa,hist,pool=None), 'proof.png')
    t.finish()
    assert t.events[0]['before']['pool'] is None


def test_jet_can_update_before_journal_without_losing_pre_state():
    t=Timeline();feed(t,0,OLD,0)
    feed(t,1,OLD,1)  # effects redraw before delayed journal update
    feed(t,1,NEW,2);t.finish()
    assert t.events[0]['before']['jet']=={'PA':0}


def test_journal_can_update_before_jet_without_finalizing_old_after():
    new='Gelano\nÉchec Rune Ga Pa\nÉchec ancien A\nÉchec ancien B\nÉchec ancien C'
    t=Timeline()
    for second,pa,hist in [(0,1,OLD),(.2,1,OLD),(.4,1,OLD),(1,1,new),(1.2,1,new),
                           (1.4,0,new),(1.6,0,new),(1.8,0,new),(2,0,new)]:
        t.observe(second,read(pa,hist,pool=0),'proof.png')
    t.finish()
    assert len(t.events)==1 and t.events[0]['after']['jet']=={'PA':0}


def test_overlapping_attempts_quarantine_both_sides_of_unsafe_pairing():
    from forgely_video_store import qualify_event
    one=NEW.replace('Succès critique Ga Pa','Succès critique Rune Ga Pa')
    two=one.replace('Succès critique Rune Ga Pa','Échec Rune Ga Pa\nSuccès critique Rune Ga Pa')
    t=Timeline();feed(t,0,OLD,0)
    for second,pa,hist in [(1,1,one),(1.2,1,one),(1.4,0,two),(1.6,0,two),
                           (1.8,0,two),(2,0,two),(2.2,0,two)]:
        t.observe(second,read(pa,hist,pool=0),'proof.png')
    t.finish()
    assert len(t.events)==2
    assert all('multiple_events' in e['issues'] for e in t.events)
    assert not any(qualify_event(e)['eligible'] for e in t.events)


def test_cancel_reanalysis_preserves_reviewed_later_events(tmp_path):
    from test_video_store import event
    path=tmp_path/'again.mp4'
    writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'mp4v'),10,(160,100))
    for i in range(30):writer.write(np.zeros((100,160,3),np.uint8))
    writer.release()
    store=VideoStore(tmp_path/'review');cancel=threading.Event()
    session=analyze_video(path,store,DEFAULT_ZONES,cancel,lambda x:None,reader=lambda im:read(0,OLD))
    corrected=event();corrected.update(reviewed_at='2026-11-08',status='rejected',time=2)
    session['events']=[corrected];store.save_session(session)
    def progress(info):
        if info['phase']=='analysis':cancel.set()
    again=analyze_video(path,store,DEFAULT_ZONES,cancel,progress,reader=lambda im:read(0,OLD))
    assert again['events'][0]['status']=='rejected'
    assert store.load_session(session['id'])['events'][0]['reviewed_at']


def test_confirmed_object_override_does_not_fill_missing_stats():
    from forgely_video_analysis import apply_item_override
    r=read(0,OLD);r['item_id']=None;r['natural_max']={};r['jet']={}
    r=apply_item_override(r,2469)
    assert r['item_id']==2469 and r['jet']=={}
    with pytest.raises(ValueError):apply_item_override(r,-1234)


def test_reader_recognizes_item_from_journal_and_uses_visual_rune_fallback():
    from forgely_video_analysis import VisualReader
    from PIL import Image
    reader=VisualReader(DEFAULT_ZONES,ocr=lambda image:'')
    class Icons:
        def predict(self,image):
            from types import SimpleNamespace
            return SimpleNamespace(rune='Ga Pa')
    reader.icons=Icons()
    outputs=iter(['', '0 PA', '', 'Gelano\nÉchec critique Ga Pa', 'Reliquat: 17'])
    reader.ocr=lambda image:next(outputs)
    # use a direct jet reader in this test so its OCR recovery passes don't consume unrelated text
    import forgely_jet
    original=forgely_jet.read_effects_ocr
    try:
        forgely_jet.read_effects_ocr=lambda image,ocr:ocr(image)
        result=reader(Image.new('RGB',(1200,700)))
    finally:forgely_jet.read_effects_ocr=original
    assert result['item_id']==2469 and result['rune']=='Ga Pa'


def test_mp4_decoding_cancellation_and_cached_resume(tmp_path):
    path = tmp_path/'session.mp4'
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*'mp4v'), 10, (160,100))
    assert writer.isOpened()
    for i in range(30):
        writer.write(np.full((100,160,3), 30+i, np.uint8))
    writer.release()
    assert video_info(path)['duration'] == pytest.approx(3)
    assert frame_at(path, 1).size == (160,100)
    cancel = threading.Event(); calls=[]
    def reader(image):
        calls.append(1)
        return read(0, OLD)
    def progress(info):
        if info['time'] >= .5: cancel.set()
    store=VideoStore(tmp_path/'review')
    session=analyze_video(path,store,DEFAULT_ZONES,cancel,progress,reader=reader)
    assert session['status']=='paused'
    cancel.clear(); before=len(calls)
    session=analyze_video(path,store,DEFAULT_ZONES,cancel,lambda x:None,reader=reader)
    assert session['status']=='done' and len(calls)>before
    assert session['events']==[]
    assert path.exists()


def test_zones_validate_strictly():
    validate_zones(DEFAULT_ZONES)
    with pytest.raises(ValueError): validate_zones({**DEFAULT_ZONES,'jet': (0,0,2,1)})
    with pytest.raises(ValueError): validate_zones({})


def test_tightly_cropped_rune_label_accepts_exact_name_not_inventory_counts():
    from forgely_video_analysis import rune_label
    assert rune_label('Ga Pa\n')=='Ga Pa'
    assert rune_label('Rune Pa Ine')=='Pa Ine'
    assert rune_label('10 Force') is None
    assert rune_label('Ga Pa 125') is None
