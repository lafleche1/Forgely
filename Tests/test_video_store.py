import copy
import json
import pytest
from forgely_video_store import VideoStore, qualify_event, transfer_session, qualified_video_rows


def event():
    return dict(id='e1', time=2., item_id=2469, rune='Ga Pa', outcome='SC',
                before={'jet': {'PA': 0}, 'pool': 17.}, after={'jet': {'PA': 1}, 'pool': 17.},
                natural_max={'PA': 1}, event_confirmed=True, stable=True, issues=[],
                status='candidate', evidence={'before': 'before.png', 'after': 'after.png'})


def test_sc_pool_and_unknown_context_are_not_fabricated():
    e = event()
    assert qualify_event(e)['eligible']
    e['after']['pool'] = 0
    assert not qualify_event(e)['eligible']
    e = event(); e['before']['pool'] = None
    assert not qualify_event(e)['eligible']
    e = event(); e['natural_max'] = {'PA': 2}
    assert not qualify_event(e)['eligible']
    e = event(); e['event_confirmed'] = False
    assert not qualify_event(e)['eligible']


def test_partial_profile_and_multi_event_never_promoted_by_confirmation():
    e = event(); e['before']['jet'] = {'Force': 5}; e['status'] = 'confirmed'
    assert not qualify_event(e)['eligible']
    e = event(); e['issues'] = ['multiple_events']; e['status'] = 'confirmed'
    assert not qualify_event(e)['eligible']


def test_store_atomic_save_edit_history_and_transfer_retract(tmp_path):
    store = VideoStore(tmp_path/'review')
    session = {'id': 'a'*64, 'path': 'original.mp4', 'events': [event()], 'status': 'done'}
    store.save_session(session)
    assert store.load_session(session['id'])['events'][0] == event()
    db = tmp_path/'forgely.sqlite'
    assert transfer_session(session, db)['accepted'] == 1
    assert transfer_session(copy.deepcopy(session), db)['accepted'] == 1
    assert len(qualified_video_rows(db)) == 1
    session['events'][0]['status'] = 'rejected'
    store.save_session(session)
    assert len(store.load_session(session['id'])['history']) == 1
    assert transfer_session(session, db)['accepted'] == 0
    assert qualified_video_rows(db) == []
    assert not list((tmp_path/'review').rglob('*.tmp'))


def test_malformed_and_duplicate_events_fail_closed(tmp_path):
    assert not qualify_event({'item_id': None})['eligible']
    e = event()
    with pytest.raises(ValueError):
        transfer_session({'id': 'a'*64, 'events': [e, e]}, tmp_path/'db')
    with pytest.raises(ValueError):
        VideoStore(tmp_path).load_session('../escape')


def test_video_database_handles_close_after_reads_and_writes(tmp_path):
    db=tmp_path/'db.sqlite'
    transfer_session({'id':'a'*64,'events':[event()]},db)
    assert len(qualified_video_rows(db))==1
    db.unlink()  # On Windows an open SQLite handle prevents this.
    assert not db.exists()
