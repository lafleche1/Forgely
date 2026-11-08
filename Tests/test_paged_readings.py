from forgely_workshop_readings import WorkshopReadings


def page(reader, jet, pool=0):
    for _ in range(3):
        ready = reader.observe(jet, pool)
    return ready


def test_scroll_merges_by_stat_not_row_and_keeps_zero_and_negative():
    r = WorkshopReadings()
    r.configure('padgref', ['Vitalité', 'Agilité', 'Tacle'])
    assert not page(r, {'Vitalité': 96, 'Agilité': 58})
    assert r.snapshot() is None
    assert page(r, {'Agilité': 58, 'Tacle': -4})
    assert r.snapshot() == ({'Vitalité': 96, 'Agilité': 58, 'Tacle': -4}, 0)
    assert not r.atomic_snapshot
    r.configure('other', ['Vitalité'])
    assert r.snapshot() is None
    assert page(r, {'Vitalité': 0})
    assert r.snapshot() == ({'Vitalité': 0}, 0)


def test_attempt_keeps_old_values_for_display_but_requires_reread():
    r = WorkshopReadings()
    r.configure('same', ['Vitalité', 'Tacle'])
    assert page(r, {'Vitalité': 96, 'Tacle': -4})
    r.invalidate()
    assert r.snapshot() is None
    assert r.line_states['Tacle'] == 'stale'
    assert not page(r, {'Vitalité': 90})
    assert r.line_states['Tacle'] == 'stale'
    assert page(r, {'Tacle': -4})
    assert r.snapshot()[0]['Vitalité'] == 90


def test_unannounced_change_invalidates_hidden_rows_immediately():
    r = WorkshopReadings()
    r.configure('same', ['Vitalité', 'Tacle'])
    page(r, {'Vitalité': 96, 'Tacle': -4})
    assert not r.observe({'Vitalité': 95}, 0)
    assert r.snapshot() is None
    assert r.line_states['Tacle'] == 'stale'


def test_unknown_profile_never_claims_complete_and_aliases_merge():
    r = WorkshopReadings()
    r.configure('unknown', None)
    assert not page(r, {'Vitalité': 10})
    r.configure('known', ['Invocations', 'Vitalité'])
    assert not page(r, {'Invocation': 1})
    assert page(r, {'Vitalité': 10})
    assert len(r.snapshot()[0]) == 2


def test_pool_change_also_expires_offscreen_values():
    r = WorkshopReadings()
    r.configure('same', ['Vitalité', 'Tacle'])
    page(r, {'Vitalité': 96, 'Tacle': -4}, 0)
    assert not page(r, {'Vitalité': 96}, 4)
    assert r.line_states['Tacle'] == 'stale'


def test_repeated_frame_does_not_confirm_a_page():
    r = WorkshopReadings()
    r.configure('same', ['Vitalité'])
    for _ in range(5):
        assert not r.observe({'Vitalité': 96}, 0, sequence=1)
    assert not r.observe({'Vitalité': 96}, 0, sequence=2)
    assert r.observe({'Vitalité': 96}, 0, sequence=3)


def test_table_distinguishes_stale_offscreen_and_missing():
    from forgely_dashboard import stat_rows
    rows = stat_rows({'Vitalité': 96, 'Tacle': -4}, {'PA': 1},
                     states={'Vitalité': 'offscreen', 'Tacle': 'stale'}, verified=False)
    assert rows[0][3] == 'Lu · hors écran'
    assert rows[1][3] == 'À revérifier'
    assert rows[2][3] == 'À lire'


def test_new_stat_names_from_scroll_are_not_an_item_change():
    from forgely_continuous_identity import strong_signature_change
    top = [('vitalite',71,100), ('intelligence',41,60), ('agilite',41,60)]
    bottom = [('dommages critiques',8,12), ('tacle',-6,-4), ('esquive pm',-4,-3)]
    assert not strong_signature_change(top, bottom)
    other = [('vitalite',200,250), ('intelligence',60,80), ('agilite',60,80)]
    assert strong_signature_change(top, other)


def test_slot_absence_remains_visible_to_session_invalidation():
    from forgely_continuous_identity import CurrentSlotTracker
    tracker = CurrentSlotTracker()
    for _ in range(3):
        tracker.observe(None)
    assert tracker.misses >= 3
def test_stable_lines_are_confirmed_before_item_identity():
    from forgely_workshop_readings import WorkshopReadings
    tracker=WorkshopReadings()
    for sequence in range(3):
        tracker.observe({'Intelligence':40},1.9,sequence=sequence)
    assert tracker.line_states == {'Intelligence':'confirmed'}
    tracker.observe({'Intelligence':39},1.9,sequence=3)
    assert tracker.line_states == {'Intelligence':'stale'}

