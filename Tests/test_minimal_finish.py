import pytest
from forgely_decision import advise,candidates


@pytest.mark.parametrize('pool',[0,.2,1,3])
def test_champetre_can_finish_vitality_with_one_minimal_over(pool):
    jet={'Vitalité':16,'Agilité':20};target={'Vitalité':20,'Agilité':20}
    p=advise(jet,target,target,pool,item='Anneau Champêtre',predictive_policy=True)
    assert p.rune=='Vi'
    assert p.kind=='over'
    assert '21' in p.explanation
    assert 'over de 1' in p.explanation
    assert p.estimates['matrix']['optimal']['finishing_over'] is True


def test_no_larger_tier_is_added_to_force_a_finish():
    jet={'Vitalité':16,'Agilité':20};target={'Vitalité':20,'Agilité':20}
    assert [r[1] for r in candidates(jet,target,target,0)]==['Vi']


def test_exact_natural_finish_still_uses_normal_rune():
    jet={'Vitalité':15,'Agilité':20};target={'Vitalité':20,'Agilité':20}
    p=advise(jet,target,target,0,predictive_policy=True)
    assert p.rune=='Vi' and p.kind=='fm_classique'


def test_line_density_limit_still_blocks_finishing_over():
    p=advise({'Vitalité':503},{'Vitalité':504},{'Vitalité':504},0,predictive_policy=True)
    assert p.rune is None
    assert 'phase de puits' not in p.summary


def test_compact_copilot_reports_the_finishing_over():
    from forgely_predictive import report_text
    jet={'Vitalité':16,'Agilité':20};target={'Vitalité':20,'Agilité':20}
    p=advise(jet,target,target,0,predictive_policy=True)
    assert 'finition à 21 (over 1)' in report_text(p,jet,target,target,0,compact=True)


def test_natural_repairs_still_precede_a_fragile_finishing_over():
    jet={'Vitalité':16,'Agilité':19};target={'Vitalité':20,'Agilité':20}
    assert advise(jet,target,target,0,predictive_policy=True).rune=='Age'
