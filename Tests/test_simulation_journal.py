import sqlite3
from forgely_simulation_journal import SimulationJournal


def test_virtual_trials_have_own_persistent_totals_and_do_not_become_real(tmp_path):
    db=tmp_path/'simulations.db';journal=SimulationJournal(db)
    key=('model',14092,'state')
    results={'Fo':{'trials':48,'counts':{'SC':4,'SN':24,'EC':20},'kind':'virtual_trials','real_observations':0}}
    assert journal.record(key,results)
    assert not journal.record(key,results)
    totals=SimulationJournal(db).totals()
    assert journal.totals_by_item()=={14092:48}
    assert totals['virtual']==48 and totals['SC']==4 and totals['SN']==24 and totals['EC']==20
    with sqlite3.connect(db) as connection:
        names={r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert 'fusion_contexts' not in names and 'observations' not in names
