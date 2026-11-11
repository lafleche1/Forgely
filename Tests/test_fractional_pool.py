import pytest
from forgely_decision import advise
from forgely_dofocus import reference


@pytest.mark.parametrize('pool',[.1,.2,.5,.9])
@pytest.mark.parametrize(('stat','rune'),[('Agilité','Pa Age'),('Force','Pa Fo'),('Intelligence','Pa Ine'),('Chance','Pa Cha')])
def test_unusable_fraction_cannot_exclude_exact_finishing_rune(pool,stat,rune):
    jet={'Vitalité':20,stat:17};target={'Vitalité':20,stat:20}
    p=advise(jet,target,target,pool,predictive_policy=True)
    assert p.rune==rune
    assert rune not in p.estimates['matrix']['excluded']


@pytest.mark.parametrize('pool',[1,2])
def test_usable_pool_still_prefers_a_covered_repair(pool):
    p=advise({'Vitalité':20,'Agilité':17},{'Vitalité':20,'Agilité':20},
             {'Vitalité':20,'Agilité':20},pool,predictive_policy=True)
    assert reference(p.rune).weight<=pool
    assert p.estimates['matrix']['pool_repair_preferred'] is True
