import pytest
import forgely_expert as expert
from forgely_decision import advise, candidates, pool_transition


@pytest.mark.parametrize('mode', ['Chances maximales', 'Budget optimisé'])
def test_natural_target_restoration_precedes_available_exotic_finish(mode):
    options = candidates({'PA': 0, 'Force': 0}, {'PA': 1, 'Force': 60},
                         {'Force': 60}, 0, mode=mode,
                         prices={'Ga Pa': 1, 'Fo': 100000, 'Pa Fo': 100000, 'Ra Fo': 100000})
    assert options and all(row[3] == 'fm_classique' for row in options)


def test_exotic_without_pool_and_pool_over_101_remain_valid():
    assert advise({'PA': 0}, {'PA': 1}, natural_max={}, pool=0).rune == 'Ga Pa'
    assert pool_transition(150, 1, 0, 'SC') == 150


def board(jets=None, targets=None, pool=46, **kwargs):
    jets = {'Force': 0} if jets is None else jets
    targets = {'Force': 10} if targets is None else targets
    p = advise(jets, targets, natural_max={'Force': 100}, pool=pool)
    return expert.build_dashboard(p, jets, targets, pool, natural_max={'Force': 100}, **kwargs)


def test_sc_scenario_keeps_pool_and_never_claims_final_probability():
    b = board()
    assert b['branches']['SC']['pool'] == 46
    assert b['branches']['SC']['next_rune'] is None  # target reached by Ra Fo
    assert b['branches']['SC']['status'] == 'Objectif atteint'
    assert b['goal_probability'] is None
    assert b['confidence_percent'] is None
    assert b['branches']['SN']['pool'] is None
    assert b['branches']['EC']['next_rune'] is None


def test_sc_branch_spends_only_the_attempt_price_from_budget():
    jets, targets = {'Force': 0}, {'Force': 2}
    p = advise(jets, targets, natural_max={'Force': 100}, pool=10,
               mode='Budget optimisé', prices={'Fo': 36}, remaining_budget=36)
    b = expert.build_dashboard(p, jets, targets, 10, natural_max={'Force': 100},
                              mode='Budget optimisé', prices={'Fo': 36}, remaining_budget=36)
    assert b['branches']['SC']['remaining_budget'] == 0
    assert b['branches']['SC']['next_rune'] is None
    assert b['branches']['SC']['status'] == 'Budget épuisé'


@pytest.mark.parametrize('kwargs', [{'verified': False}, {'after_fusion': True}])
def test_provisional_state_never_exposes_action_or_numeric_pool(kwargs):
    b = board(**kwargs)
    assert b['action']['rune'] is None
    assert b['pool']['value'] is None
    assert not b['branches']


def test_target_reached_stops_without_98_percent_threshold():
    b = board(jets={'Force': 98}, targets={'Force': 100})
    assert b['action']['rune'] is not None
    b = board(jets={'Force': 98}, targets={'Force': 98})
    assert b['stop'] and b['action']['rune'] is None


def test_sn_audit_counts_loss_on_the_same_line_as_the_gain():
    b = {'jet': {'Force': 10}, 'pool': 5}
    a = {'jet': {'Force': 10}, 'pool': 5}
    audit = expert.audit_transition('Fo', 'SN', b, a, complete=True)
    assert audit['lost_weight'] == 1  # +1 nominal and -1 loss cancel visually
    assert audit['calculated_pool'] == 5
    assert audit['status'] == 'cohérent'


def test_partial_reading_does_not_certify_pool_calculation():
    audit = expert.audit_transition('Fo', 'EC',
        {'jet': {'Force': 10}, 'pool': 5}, {'jet': {'Force': 10}, 'pool': 4})
    assert audit['calculated_pool'] is None
    assert audit['lost_weight'] is None
    assert audit['status'] == 'partiel'


def test_audit_rejects_contradictory_sc_and_nonfinite_readings():
    b = {'jet': {'Force': 10}, 'pool': 5}
    assert expert.audit_transition('Fo', 'SC', b,
        {'jet': {'Force': 9}, 'pool': 5}, complete=True)['status'] == 'contradictoire'
    assert expert.audit_transition('Fo', 'EC', b,
        {'jet': {'Force': 10}, 'pool': float('nan')}, complete=True)['status'] == 'invalide'


def test_rendered_dashboard_has_three_conditional_branches_and_unknown_odds():
    text = expert.render_dashboard(board())
    assert all(label in text for label in ('SC', 'SN', 'EC', 'PUITS', 'ACTION', 'RISQUE'))
    assert 'non estimée' in text
