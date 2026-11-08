from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Application'))
from forgely_detection import Observation
from forgely_pool_observer import PoolObserver


OLD = 'Equipment\nold result one\nold result two\nold result three'
NEW = 'Equipment\nnew result\nold result one\nold result two\nold result three'
EVENT = Observation('Fo', 'SN', '', '')


def baseline(observer, pool=5, context='a'):
    for frame in range(1, 4):
        result = observer.observe(context, OLD, {'Force': 10, 'PA': 1}, pool, None, True, frame)
    return result


def test_single_transition_hidden_after_pool():
    observer = PoolObserver()
    baseline(observer)
    for frame in (4, 5, 6):
        result = observer.observe('a', NEW, {'Force': 11, 'PA': 0}, None,
                                  EVENT if frame == 4 else None, True, frame)
        assert result['pending'] is (frame < 6)
    assert result['value'] == '104'
    assert result['origin'] == 'calculated'
    assert observer.observe('a', NEW, {'Force': 11, 'PA': 0}, None, None, True, 7)['value'] == '104'


def test_sc_and_duplicate_frames():
    observer = PoolObserver()
    baseline(observer)
    sc = Observation('Fo', 'SC', '', '')
    for _ in range(4):
        result = observer.observe('a', NEW, {'Force': 11, 'PA': 1}, None, sc, True, 4)
    assert result['pending']
    for frame in (5, 6):
        result = observer.observe('a', NEW, {'Force': 11, 'PA': 1}, None, None, True, frame)
    assert result['value'] == '5'


def test_unknown_initial_pool_and_read_precedence():
    observer = PoolObserver()
    baseline(observer, None)
    for frame in (4, 5, 6):
        result = observer.observe('a', NEW, {'Force': 11, 'PA': 0}, None, EVENT, True, frame)
    assert result['value'] is None
    observer.reset()
    baseline(observer)
    for frame in (4, 5, 6):
        result = observer.observe('a', NEW, {'Force': 11, 'PA': 0}, 77, EVENT, True, frame)
    assert result['value'] == '77'
    assert result['origin'] == 'read'


def test_gap_context_and_multiple_rows_invalidate():
    for mode in ('gap', 'context', 'multiple', 'incomplete'):
        observer = PoolObserver()
        baseline(observer)
        history = NEW if mode != 'multiple' else NEW.replace('new result', 'new result\nother result')
        if mode == 'gap':
            observer.observe('a', '', {}, None, None, False, 4)
        for frame in (5, 6, 7):
            result = observer.observe('b' if mode == 'context' else 'a', history,
                                      {'Force': 11, 'PA': 0}, None, EVENT,
                                      mode != 'incomplete', frame)
        assert result['value'] is None


def test_early_jet_change_keeps_frozen_before():
    observer = PoolObserver()
    baseline(observer)
    changed = {'Force': 11, 'PA': 0}
    for frame in (4, 5, 6):
        assert observer.observe('a', OLD, changed, None, None, True, frame)['value'] is None
    for frame in (7, 8, 9):
        result = observer.observe('a', NEW, changed, None, EVENT if frame == 8 else None, True, frame)
    assert result['value'] == '104'


def test_unread_frame_and_skipped_frame_break_calculated_continuity():
    for skipped in (False, True):
        observer = PoolObserver()
        baseline(observer)
        if not skipped:
            observer.observe('a', OLD, {}, None, None, False, 4)
        result = observer.observe('a', OLD, {'Force': 10, 'PA': 1}, None, None, True, 5)
        assert result['value'] is None


def test_post_read_does_not_become_before_baseline():
    observer = PoolObserver()
    baseline(observer)
    for frame in (4, 5, 6):
        result = observer.observe('a', NEW, {'Force': 11, 'PA': 0},
                                  77 if frame == 4 else None, EVENT, True, frame)
    assert result['value'] is None
    assert result['origin'] == 'unknown'
    assert observer.observe('a', NEW, {'Force': 11, 'PA': 0}, None, None, True, 7)['value'] is None
    for frame in (8, 9, 10):
        observer.observe('a', NEW, {'Force': 11, 'PA': 0}, 77, None, True, frame)
    assert observer.observe('a', NEW, {'Force': 11, 'PA': 0}, None, None, True, 11)['value'] == '77'


def test_unstable_pool_readings_cannot_anchor_hidden_transition():
    observer = PoolObserver()
    for frame, pool in enumerate((5, 6, 7), 1):
        result = observer.observe('a', OLD, {'Force': 10, 'PA': 1}, pool, None, True, frame)
        assert result['value'] == str(pool)
        assert result['origin'] == 'read'
    for frame in (4, 5, 6):
        result = observer.observe('a', NEW, {'Force': 11, 'PA': 0}, None, EVENT, True, frame)
    assert result['value'] is None


def test_conflicting_read_invalidates_resolved_hidden_pool_until_stable_reads():
    observer = PoolObserver()
    baseline(observer)
    for frame in (4, 5, 6):
        observer.observe('a', NEW, {'Force': 11, 'PA': 0}, None, EVENT, True, frame)
    assert observer.observe('a', NEW, {'Force': 11, 'PA': 0}, 77, None, True, 7)['origin'] == 'read'
    assert observer.observe('a', NEW, {'Force': 11, 'PA': 0}, None, None, True, 8)['value'] is None


def test_unidentified_transition_stops_requesting_captures():
    observer = PoolObserver()
    baseline(observer)
    for frame in range(4, 14):
        result = observer.observe('a', NEW, {'Force': 11, 'PA': 0}, None, None, True, frame)
        assert result['value'] is None
        assert result['origin'] == 'unknown'
        if frame >= 9:
            assert result['pending'] is False


def test_unidentified_transition_can_establish_fresh_direct_baseline():
    observer = PoolObserver()
    baseline(observer)
    for frame in range(4, 10):
        result = observer.observe('a', NEW, {'Force': 11, 'PA': 0}, 77, None, True, frame)
    assert result['pending'] is False
    assert observer.observe('a', NEW, {'Force': 11, 'PA': 0}, None, None, True, 10)['value'] == '77'
