import json
import sqlite3
import pytest
from forgely_labo_live import LiveLaboratory, compute_snapshot


def test_same_stat_names_with_different_values_never_share_rates(tmp_path):
    db = tmp_path / 'ctx.db'
    with sqlite3.connect(db) as c:
        c.execute('CREATE TABLE fusion_contexts(item,rune,outcome,before_json,source)')
        for value, outcome in ((10, 'SC'), (99, 'EC')):
            for _ in range(30):
                c.execute('INSERT INTO fusion_contexts VALUES(?,?,?,?,?)',
                          ('Anneau', 'Fo', outcome, json.dumps({'jet': {'Force': value}, 'pool': 5}), 'local_screen'))
    lab = LiveLaboratory(db)
    lab._snapshot = compute_snapshot(db)
    assert lab.estimate('Anneau', 'Fo', {'Force': 10}, 5)['percentages']['SC'] == 100
    assert lab.estimate('Anneau', 'Fo', {'Force': 99}, 5)['percentages']['SC'] == 0
    assert lab.estimate('Anneau', 'Fo', {'Force': 50}, 5) is None


@pytest.mark.parametrize('pool', [True, float('nan'), float('inf')])
def test_invalid_historical_pool_does_not_enter_samples(tmp_path, pool):
    db = tmp_path / 'ctx.db'
    with sqlite3.connect(db) as c:
        c.execute('CREATE TABLE fusion_contexts(item,rune,outcome,before_json,source)')
        c.execute('INSERT INTO fusion_contexts VALUES(?,?,?,?,?)',
                  ('Anneau', 'Fo', 'SC', json.dumps({'jet': {'Force': 10}, 'pool': pool}), 'local_screen'))
    result = compute_snapshot(db)
    assert result['observations'] == 0
    assert result['rejected'] == 1
