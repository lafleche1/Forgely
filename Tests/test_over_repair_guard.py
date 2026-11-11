import pytest
from forgely_decision import advise


@pytest.mark.parametrize('predictive', [False, True])
@pytest.mark.parametrize('over', [1, 2])
def test_small_useful_rune_precedes_sagesse_with_fragile_intelligence(over, predictive):
    jets = {'Intelligence': 40 + over, 'Sagesse': 38, 'Vitalité': 145}
    targets = {'Intelligence': 40, 'Sagesse': 40, 'Vitalité': 200}
    natural = dict(targets, **{'Vitalité': 150})
    proposal = advise(jets, targets, natural, 58, predictive_policy=predictive)
    assert proposal.rune == 'Vi'
    if predictive:
        matrix = proposal.estimates['matrix']
        assert matrix['pool_repair_weight'] <= over
        assert matrix['pool_repair_sequence'] == ['Vi']


def test_multiple_runes_stay_within_total_excess_weight():
    proposal = advise({'Intelligence': 42, 'Sagesse': 38, 'Vitalité': 140},
                      {'Intelligence': 40, 'Sagesse': 40, 'Vitalité': 200},
                      {'Intelligence': 40, 'Sagesse': 40, 'Vitalité': 150},
                      58, predictive_policy=True)
    assert proposal.estimates['matrix']['pool_repair_sequence'] == ['Vi', 'Vi']
    assert proposal.estimates['matrix']['pool_repair_weight'] == 2


def test_guard_releases_after_over_disappears():
    jets = {'Intelligence': 40, 'Sagesse': 38, 'Vitalité': 145}
    targets = {'Intelligence': 40, 'Sagesse': 40, 'Vitalité': 200}
    proposal = advise(jets, targets, dict(targets, **{'Vitalité': 150}), 58,
                      predictive_policy=True)
    assert proposal.rune == 'Sa'


def test_no_small_useful_repair_does_not_block_advice():
    proposal = advise({'Intelligence': 42, 'Sagesse': 38},
                      {'Intelligence': 40, 'Sagesse': 40},
                      {'Intelligence': 40, 'Sagesse': 40}, 58, predictive_policy=True)
    assert proposal.rune is not None
