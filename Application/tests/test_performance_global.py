from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import pytest


def test_names_warm_lookup_does_not_normalize_whole_registry():
    import forgely_item_vision as module
    names=[(i,f'Amulette fictive {i}') for i in range(1000)]+[(2000,'Anneau du Cycloïde')]
    assert module.identify_known('ANNEAU DU CYCLOÏDE',names)=='Anneau du Cycloïde'
    with patch.object(module,'key_for',wraps=module.key_for) as norm:
        assert module.identify_known('ANNEAU DU CYCLOÏDE',names)=='Anneau du Cycloïde'
        assert norm.call_count<=2
    assert module.identify_known('Anneau du Cycloïde',names+[(3000,'Anneau du Cycloïde')]) is None
    assert module.identify_known('Anneau du Cycloïde',names+[(3000,'Cycloïde')]) is None


def test_bounds_cache_reads_once_and_invalidates_on_replacement(tmp_path):
    import forgely_tools as tools
    path=tmp_path/'bounds.csv'
    path.write_text('equipement,statistique,min,max\nObjet,Force,0,100\n')
    first=tools.natural_bounds('Objet',path)
    with patch('builtins.open',side_effect=AssertionError('warm CSV reopened')):
        assert tools.natural_bounds('Objet',path)==first
    first['Force']=(0,1)
    assert tools.natural_bounds('Objet',path)['Force']==(0,100)
    new=tmp_path/'replacement.csv';new.write_text('equipement,statistique,min,max\nObjet,Force,0,200\n');new.replace(path)
    assert tools.natural_bounds('Objet',path)['Force']==(0,200)


def test_batch_counts_are_current_and_item_scoped(tmp_path):
    from forgely_data import insert_observation,stats_by_rune
    path=tmp_path/'obs.db'
    insert_observation('A','Fo','SC','manual',db_file=path)
    insert_observation('B','Fo','EC','manual',db_file=path)
    assert stats_by_rune('A',path)=={'Fo':{'SC':1,'SN':0,'EC':0}}
    insert_observation('A','Fo','EC','manual',db_file=path)
    assert stats_by_rune('A',path)['Fo']=={'SC':1,'SN':0,'EC':1}


def test_parsed_jets_are_fast_without_mutable_aliases():
    from forgely_jet import parse_jet
    text='30 Force\n-5 Résistance Critique\n3 % Résistance Air'
    first=parse_jet(text);first['Force']=999
    assert parse_jet(text)['Force']==30
    assert parse_jet('31 Force')['Force']==31


def test_stable_advice_cached_but_state_prices_and_learning_invalidate():
    import forgely
    cfg={'strategy':'Budget optimisé','budget_kamas':0,'prices':{'Fo':36,'Pa Fo':132,'Ra Fo':382}}
    app=SimpleNamespace(observation_only=False,plan={'item':'Test','stats':{'Force':{'target':10}}},
        active_equipment_verified=True,item=SimpleNamespace(get=lambda:'Test'),
        live_jet={'Force':0},live_pool=30,live_after_fusion=False,budget_start_cursor={'observations':0,'unassigned_actions':0},
        last_transition_audit=None,live_laboratory=SimpleNamespace(estimate=lambda *a:None,calibration=lambda *a:None,revision=0))
    with patch('forgely.read_settings',return_value=cfg), \
         patch('forgely.natural_bounds',return_value={'Force':(0,100)}), \
         patch('forgely.stats_by_rune',return_value={}), \
         patch('forgely.cost_since',side_effect=AssertionError('unlimited budget queried')), \
         patch('forgely.advise',wraps=forgely.advise) as engine:
        first=forgely.Forgely.strategy_current(app)
        first.estimates['prediction']['SC']=-1
        second=forgely.Forgely.strategy_current(app)
        assert second.estimates['prediction']['SC']>=0 and engine.call_count==1
        app.live_pool=29;forgely.Forgely.strategy_current(app)
        assert engine.call_count==2
        cfg['prices']['Fo']=37;forgely.Forgely.strategy_current(app)
        assert engine.call_count==3
        app.live_laboratory.revision=1;forgely.Forgely.strategy_current(app)
        assert engine.call_count==4
        app.live_after_fusion=True
        assert forgely.Forgely.strategy_current(app).rune is None


def test_sqlite_wal_changes_invalidate_revision(tmp_path):
    import sqlite3
    from forgely_runtime_cache import database_revision
    path=tmp_path/'wal.db'
    db=sqlite3.connect(path)
    try:
        db.execute('PRAGMA journal_mode=WAL');db.execute('CREATE TABLE t(x)');db.commit()
        before=database_revision(path)
        db.execute('INSERT INTO t VALUES(1)');db.commit()
        assert database_revision(path)!=before
    finally:db.close()


def test_unchanged_widgets_do_not_repeat_layout_updates():
    from forgely_runtime_cache import configure_if_changed
    class Widget:
        def __init__(self):self.values={'text':'A'};self.calls=0
        def cget(self,key):return self.values[key]
        def configure(self,**values):self.values.update(values);self.calls+=1
    widget=Widget()
    assert configure_if_changed(widget,text='A') is False
    assert configure_if_changed(widget,text='B') is True
    assert configure_if_changed(widget,text='B') is False
    widget.configure(text='external')
    assert configure_if_changed(widget,text='B') is True
    assert widget.calls==3


def test_manual_record_does_not_multiply_periodic_refresh_timers():
    from unittest.mock import Mock
    from forgely import Forgely
    app=SimpleNamespace(item=SimpleNamespace(get=lambda:'Test'),rune=SimpleNamespace(get=lambda:'Fo'),
                        status=Mock(),refresh_stats=Mock(),refresh_stats_now=Mock())
    with patch('forgely.insert_observation'):Forgely.record_manual(app,'SC')
    app.refresh_stats_now.assert_called_once()
    app.refresh_stats.assert_not_called()


def test_laboratory_skips_unchanged_database_but_refreshes_notifications(tmp_path):
    import forgely_labo_live as module
    lab=module.LiveLaboratory(tmp_path/'absent.db')
    with patch.object(module,'compute_snapshot',return_value={'groups':{},'observations':0,'rejected':0}) as rebuild:
        assert lab.refresh_if_changed() is True
        assert lab.refresh_if_changed() is False
        assert rebuild.call_count==1
        previous=lab.revision
        lab.notify_observation()
        assert lab.refresh_if_changed() is True
        assert lab.revision>previous and rebuild.call_count==2


def test_same_rune_icon_is_not_decoded_and_recreated_every_frame(tmp_path):
    from PIL import Image
    from unittest.mock import Mock
    from forgely import Forgely
    path=tmp_path/'Fo.png';Image.new('RGBA',(32,32),'red').save(path)
    app=SimpleNamespace(main_rune_icon=Mock(),main_rune_photo=None)
    with patch('forgely.rune_icon_path',return_value=path),patch('forgely.ImageTk.PhotoImage',return_value=object()) as photo:
        Forgely._update_main_rune_icon(app,'Fo');Forgely._update_main_rune_icon(app,'Fo')
        assert photo.call_count==1
        Image.new('RGBA',(32,32),'blue').save(path)
        Forgely._update_main_rune_icon(app,'Fo')
        assert photo.call_count==2


def test_capture_period_does_not_add_capture_time_to_the_wait():
    from forgely_runtime_cache import capture_wait
    assert capture_wait(.12,.04)==pytest.approx(.08)
    assert capture_wait(.12,.5)==pytest.approx(.005)
    assert capture_wait(0,0)==0
