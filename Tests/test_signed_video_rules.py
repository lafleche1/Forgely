from decimal import Decimal
import pytest
from forgely_pool_ledger import PoolLedger
from forgely_expert import audit_transition


@pytest.mark.parametrize('before,after,rune,outcome,pool,expected', [
    ({'Agilité':-11},{'Agilité':-1},'Ra Age','SN',31.5,26.5),
    ({'Intelligence':-4},{'Intelligence':6},'Ra Ine','SN',33,23),
    ({'Intelligence':-4,'Agilité':-12},{'Intelligence':6,'Agilité':-15},'Ra Ine','SN',24.5,16),
    ({'Portée':1,'Chance':-5},{'Portée':0,'Chance':-5},'Ra Cha','EC',2,43),
    ({'Portée':0,'Force':-15},{'Portée':1,'Force':-15},'Po','SC',33,33),
    ({'Chance':-3,'Force':-9},{'Chance':0,'Force':-15},'Pa Cha','SN',36.5,36.5),
    ({'Chance':0,'Agilité':-15},{'Chance':-3,'Agilité':-15},'Pa Age','EC',36.5,36.5),
])
def test_video_transitions_agree_in_ledger_and_audit(before,after,rune,outcome,pool,expected):
    ledger=PoolLedger();ledger.observe(pool,'item')
    args=(before,after,rune,outcome,'pose','item',True)
    assert ledger.apply(*args)==Decimal(str(expected))
    assert ledger.apply(*args)==Decimal(str(expected))
    report=audit_transition(rune,outcome,{'jet':before,'pool':pool},
                            {'jet':after,'pool':expected},complete=True)
    assert report['status']=='cohérent'
    assert report['calculated_pool']==expected


def test_unverified_negative_stat_stays_unknown():
    ledger=PoolLedger();ledger.observe(10,'item')
    assert ledger.apply({'Force':-15,'Initiative':-10},
        {'Force':-14,'Initiative':-11},'Fo','SN',1,'item',True) is None


def test_partial_target_gain_is_not_assumed_to_be_a_full_rune():
    ledger=PoolLedger();ledger.observe(10,'item')
    assert ledger.apply({'Force':-5},{'Force':0},'Ra Fo','SN',1,'item',True) is None


def test_advice_explains_effective_charge_without_predicting_losses():
    from forgely_decision import advise
    p=advise({'Force':-15},{'Force':-14},{'Force':-15},2)
    assert p.estimates['attempted_weight']==0.5
    assert '0.5' in p.explanation
    assert p.estimates['prediction'] is None


def test_known_transition_detects_wrong_direct_pool_instead_of_accepting_it():
    report=audit_transition('Ra Ine','SN',{'jet':{'Intelligence':-4},'pool':33},
        {'jet':{'Intelligence':6},'pool':28},complete=True)
    assert report['status']=='contradictoire'
    assert report['calculated_pool']==23


def test_unknown_initial_pool_is_never_reconstructed_from_po_loss():
    ledger=PoolLedger()
    assert ledger.apply({'Portée':1,'Chance':-5},{'Portée':0,'Chance':-5},
        'Ra Cha','EC',1,'item',True) is None
