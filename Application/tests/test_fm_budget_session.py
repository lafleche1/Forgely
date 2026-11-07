from forgely_tools import observation_cursor, cost_since, read_settings, save_settings
from forgely_data import insert_observation, insert_unassigned


def test_cost_excludes_previous_sessions_and_counts_all_current_items(tmp_path):
    db = tmp_path / 'obs.db'
    insert_observation('Ancien', 'Fo', 'EC', 'manual', db_file=db)
    cursor = observation_cursor(db)
    insert_observation('Objet A', 'Fo', 'SC', 'manual', db_file=db)
    insert_observation('Objet B', 'Pa Fo', 'EC', 'manual', db_file=db)
    cost = cost_since(cursor, {'Fo': 5}, db)
    assert cost['known_cost'] == 5
    assert cost['unpriced_attempts'] == 1
    assert cost['total_attempts'] == 2
    assert not cost['complete']
    assert cost_since(cursor, {'Fo': 5, 'Pa Fo': 20}, db)['known_cost'] == 25


def test_both_modes_persist_and_legacy_economy_migrates(tmp_path):
    p = tmp_path / 'prefs.json'
    for mode in ('Chances maximales', 'Budget optimisé', 'Économique'):
        save_settings({'strategy': mode, 'budget_kamas': 500, 'prices': {'Fo': 2}}, p)
        cfg = read_settings(p)
        assert cfg['strategy'] == ('Budget optimisé' if mode == 'Économique' else mode)


def test_default_mode_is_chances(tmp_path):
    assert read_settings(tmp_path / 'absent')['strategy'] == 'Chances maximales'


def test_unassigned_attempts_after_launch_are_unknown_expenses(tmp_path):
    db = tmp_path / 'obs.db'
    insert_unassigned('EC', db_file=db)
    cursor = observation_cursor(db)
    assert cost_since(cursor, {}, db)['complete']
    insert_unassigned('SC', db_file=db)
    result = cost_since(cursor, {'Fo': 5}, db)
    assert result['total_attempts'] == 1
    assert result['unpriced_attempts'] == 1
    assert result['unassigned_attempts'] == 1
    assert not result['complete']
