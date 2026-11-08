import sqlite3
import json
import pytest
from forgely_hybrid import ItemState, TheoreticalEngine, EmpiricalCorrector, DecisionEnvironment
from forgely_dofocus_engine import attempt


def state(pool=3.5):
    return ItemState("test", [{"stat":"Force","value":19,"min":10,"max":20,"weight":1}], pool)


def test_unknown_pool_is_never_simulated():
    s=state(None)
    assert TheoreticalEngine().predict_outcome(s,"Fo")["sc"] >= 0
    with pytest.raises(ValueError): DecisionEnvironment(s, {"Force":20})


def test_missing_database_falls_back_without_creating_file(tmp_path):
    path=tmp_path/"absent.db"
    c=EmpiricalCorrector(path)
    base=TheoreticalEngine().predict_outcome(state(),"Fo")
    assert c.get_adjusted_probabilities(state(),"Fo",base)==base
    assert not path.exists()


def test_only_exact_real_contexts_calibrate(tmp_path):
    path=tmp_path/"e.db"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE fusion_contexts(item,rune,outcome,before_json,source)")
        raw=json.dumps({"jet":{"Force":19},"pool":3.5})
        db.executemany("INSERT INTO fusion_contexts VALUES(?,?,?,?,?)",[("test","Fo","EC",raw,"local_screen")]*30)
        db.executemany("INSERT INTO fusion_contexts VALUES(?,?,?,?,?)",[("test","Fo","SC",raw,"simulation")]*100)
        db.execute("INSERT INTO fusion_contexts VALUES(?,?,?,?,?)",("test","Fo","SC",json.dumps({"jet":{"Force":18},"pool":3.5}),"local_screen"))
    c=EmpiricalCorrector(path)
    base=TheoreticalEngine().predict_outcome(state(),"Fo")
    result=c.get_adjusted_probabilities(state(),"Fo",base)
    assert result["sc"] == pytest.approx(base["sc"]*100/130)
    assert sum(result[k] for k in ("sc","sn","ec"))==pytest.approx(100)
    assert result["empirical_n"]==30
    a=DecisionEnvironment(state(),{"Force":20},corrector=c,seed=7)
    b=DecisionEnvironment(state(),{"Force":20},corrector=c,seed=7)
    assert a.step("Fo")==b.step("Fo")
    assert a.get_state()["pool_source"]=="simulation"


def test_adjusted_distribution_controls_actual_transition():
    s=state()
    r={"stat":"Force","gain":1,"weight":1}
    assert attempt(s.lines,r,s.pool,probabilities={"sc":100,"sn":0,"ec":0})["outcome"]=="SC"
    with pytest.raises(ValueError): attempt(s.lines,r,s.pool,probabilities={"sc":101,"sn":0,"ec":0})


def test_goal_recommendations_are_separate_from_legal_actions():
    e=DecisionEnvironment(state(),{"Force":20})
    assert 'Ga Pme' not in e.get_valid_actions()
    assert 'Ga Pme' in e.get_legal_actions()


def test_advice_weight_is_configurable_and_validated():
    from forgely_decision import combine_candidate_evidence, contextual_measurement
    sample={'kind':'local_dofocus_model','probabilities':{'SC':30,'SN':50,'EC':20}}
    real={'n':100,'counts':{'SC':50,'SN':0,'EC':50},'usable':True,'quality':'local_verified'}
    result=combine_candidate_evidence(sample,real,simulation_weight=.2)
    assert result['factor']==pytest.approx(.2*.8+.8*contextual_measurement(real)['success_ci95'][0])
    with pytest.raises(ValueError): combine_candidate_evidence(sample,real,simulation_weight=2)


def test_corrupt_database_falls_back(tmp_path):
    p=tmp_path/'broken.db'
    p.write_bytes(b'not a sqlite database')
    base=TheoreticalEngine().predict_outcome(state(),'Fo')
    assert EmpiricalCorrector(p).get_adjusted_probabilities(state(),'Fo',base)==base


def test_uncertain_pool_cannot_use_real_calibration(tmp_path):
    p=tmp_path/'e.db'
    with sqlite3.connect(p) as db:
        db.execute('CREATE TABLE fusion_contexts(item,rune,outcome,before_json,source)')
        raw=json.dumps({'jet':{'Force':19},'pool':3.5})
        db.executemany('INSERT INTO fusion_contexts VALUES(?,?,?,?,?)',[('test','Fo','EC',raw,'local_screen')]*30)
    s=state();s.pool_confidence=.5
    base=TheoreticalEngine().predict_outcome(s,'Fo')
    assert EmpiricalCorrector(p).get_adjusted_probabilities(s,'Fo',base)==base
