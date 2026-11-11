import pytest
from forgely_decision import advise
from forgely_dofocus import reference


@pytest.mark.parametrize('pool',[1,3,5,10])
def test_use_available_pool_to_restore_target_without_uncovered_weight(pool):
    jet={'Force':20,'Vitalité':280,'Dommages Terre':5}
    target={'Force':40,'Vitalité':300,'Dommages Terre':10}
    result=advise(jet,target,target,pool,predictive_policy=True)
    assert reference(result.rune).weight<=pool
    assert result.estimates['matrix']['pool_repair_preferred'] is True


def test_larger_pool_can_restore_heavy_deficits():
    jet={'Force':20,'Vitalité':280,'Dommages Terre':5}
    target={'Force':40,'Vitalité':300,'Dommages Terre':10}
    result=advise(jet,target,target,20,predictive_policy=True)
    assert result.rune=='Pa Do Terre'


def test_no_covered_repair_does_not_block_advice():
    jet={'Vitalité':195,'Dommages Terre':0}
    target={'Vitalité':200,'Dommages Terre':10}
    result=advise(jet,target,target,.1,predictive_policy=True)
    assert result.rune is not None
    assert reference(result.rune).weight>.1


def test_fractional_pool_keeps_unusable_fraction_and_never_exceeds_targets():
    jet={'Force':39,'Intelligence':39}
    target={'Force':40,'Intelligence':40}
    result=advise(jet,target,target,2.2,predictive_policy=True)
    data=result.estimates['matrix']
    assert data['pool_repair_weight']==2
    assert data['pool_repair_remainder']==.2
    assert sorted(data['pool_repair_sequence'])==['Fo','Ine']


def test_exact_combination_can_mix_several_stats_and_tiers():
    jet={'Force':30,'Dommages Terre':8}
    target={'Force':40,'Dommages Terre':10}
    result=advise(jet,target,target,17,predictive_policy=True)
    data=result.estimates['matrix']
    assert data['pool_repair_weight']==17
    assert data['pool_repair_remainder']==0
    assert all(reference(r).weight<=17 for r in data['pool_repair_sequence'])


def test_natural_repair_sequence_stops_at_natural_max_before_over_goal():
    result=advise({'Force':30},{'Force':50},{'Force':40},20,predictive_policy=True)
    data=result.estimates['matrix']
    assert sum(reference(r).gain for r in data['pool_repair_sequence'])<=10
    assert data['pool_repair_weight']==10
