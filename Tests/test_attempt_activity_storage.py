from forgely_attempt_activity import record_activity, activity_total, activity_recent
from forgely_data import stats, insert_observation


def test_observed_group_is_idempotent_and_never_changes_sc_sn_ec_rates(tmp_path):
    db = tmp_path / 'events.sqlite3'
    insert_observation('Test', 'Vi', 'SC', 'ocr_auto', db_file=db)
    assert record_activity('session:1:group', 'Test', 'pixels hash', db_file=db)
    assert not record_activity('session:1:group', 'Test', 'pixels hash', db_file=db)
    assert activity_total('Test', db_file=db) == 1
    assert activity_recent(db_file=db)[0][1] == 'Test'
    assert stats('Test', db_file=db) == (1, {'SC': 1, 'SN': 0, 'EC': 0})


def test_unattributed_activity_is_visible_without_assigning_it_to_an_item(tmp_path):
    db = tmp_path / 'events.sqlite3'
    record_activity('session:1', '', 'unidentified slot', db_file=db)
    record_activity('session:2', 'Other', 'other slot', db_file=db)
    assert activity_total('Test', db_file=db) == 0
    assert activity_total('Test', include_unattributed=True, db_file=db) == 1
    assert activity_total('', db_file=db) == 2
