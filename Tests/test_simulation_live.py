import threading
from math import floor
from forgely_equipment_catalog import EquipmentCatalog,equipment_bounds
from forgely_dofocus import canonical_stat
from forgely_simulation_live import SimulationWorker


def cycloid():
    item=EquipmentCatalog().get(14092)
    jet={canonical_stat(s):floor((a+b)/2+.5) for s,(a,b) in equipment_bounds(item).items()}
    return item,jet


def test_local_odds_available_without_waiting_for_background_trials():
    item,jet=cycloid();worker=SimulationWorker(trials=24)
    try:
        context=worker.context(item.identity_name,jet,0,{'Force':40})
        evidence=context.evidence('Fo')
        assert evidence['kind']=='local_dofocus_model'
        assert not evidence['real_observation']
        assert evidence['probabilities']['SC']==2
        assert abs(evidence['probabilities']['SN']-46.90973185943033)<1e-9
    finally:worker.stop()


def test_background_trials_return_only_for_matching_full_state():
    item,jet=cycloid();ready=threading.Event()
    worker=SimulationWorker(trials=24,on_ready=lambda key:ready.set())
    try:
        context=worker.context(item.identity_name,jet,0,{'Force':40})
        assert ready.wait(5)
        evidence=context.evidence('Fo')
        assert evidence['outlook']['trials']==24
        assert evidence['outlook']['mean_target_loss']>=0
        assert evidence['real_observation'] is False
        changed=dict(jet,Force=35)
        next_context=worker.context(item.identity_name,changed,5,{'Force':39})
        assert next_context.key!=context.key
        evidence['outlook']['trials']=999
        assert context.evidence('Fo')['outlook']['trials']==24
    finally:worker.stop()


def test_incomplete_unknown_or_nonfinite_states_never_get_simulated():
    item,jet=cycloid();worker=SimulationWorker()
    try:
        assert worker.context(item.name,{'Force':36},0,{'Force':40}) is None
        assert worker.context('Objet inventé',jet,0,{'Force':40}) is None
        assert worker.context(item.name,jet,float('nan'),{'Force':40}) is None
        assert worker.context(item.name,dict(jet,Force=30001),0,{'Force':40}) is None
    finally:worker.stop()
