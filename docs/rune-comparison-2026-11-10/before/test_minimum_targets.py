import pytest

from forgely_decision import advise, candidates
from forgely_dashboard import stat_rows
from forgely_general_policy import make_policy, score_actions
from forgely_rl import ForgemagingEnv
from forgely_sequence import target_value
from forgely_simulateur import simulate_target


@pytest.mark.parametrize('current', [39, 40, 45])
def test_minimum_completion_and_display(current):
    proposal = advise({'Force': current}, {'Force': 40}, {'Force': 60}, 0)
    row = stat_rows({'Force': current}, {'Force': 40}, verified=True)[0]
    if current >= 40:
        assert proposal.kind == 'atteint'
        assert proposal.rune is None
        assert row[3:] == ('Atteint', 'success')
        assert target_value({'Force': current}, {'Force': 40}) == 1
    else:
        assert proposal.kind != 'atteint'
        assert row[3:] == ('À compléter', 'pending')
        assert target_value({'Force': current}, {'Force': 40}) < 1


def test_ranking_has_no_penalty_for_crossing_minimum():
    # Both goals take the same one-point rune to finish; its physical risk is identical.
    scores = []
    for goal in (39.5, 40):
        rows = candidates({'Force': 39}, {'Force': goal}, {'Force': 60}, 100)
        scores.append(next(r[5]['decision_trace']['heuristic_score'] for r in rows if r[1] == 'Fo'))
    # Balance depends on missing mass, but the surplus must not halve utility.
    assert scores[0] >= scores[1] * .99


def test_legacy_learned_surplus_parameter_cannot_penalize_crossing_target():
    lines = [dict(stat='Force', value=39, min=1, max=60, weight=1)]
    plain = make_policy((1, 0, 1, 0), episodes=1)
    legacy = make_policy((1, 0, 1, 4), episodes=1)
    assert score_actions(lines, 10, {'Force': 40}, 200, ['Pa Fo'], plain) == score_actions(
        lines, 10, {'Force': 40}, 200, ['Pa Fo'], legacy)


@pytest.mark.parametrize('current', [40, 45])
def test_single_line_simulator_accepts_already_satisfied_target(current):
    result = simulate_target('Fo', current, 40, 0, None, 1, 0, 0, trials=3)
    assert result.completed == 3
    assert result.mean_attempts == 0
    assert (result.sc, result.sn, result.ec, result.truncated) == (0, 0, 0, 0)


def test_trainer_can_finish_with_indivisible_minimal_rune():
    env = ForgemagingEnv([dict(stat='Vitalité', value=299, min=250, max=300, weight=.2)],
                        10, {'Vitalité': 300})
    assert 'Vi' in env.get_valid_actions()
    assert 'Pa Vi' not in env.get_valid_actions()


def test_nominal_finish_paths_accept_natural_overshoot():
    from forgely_finish_paths import compare_finish_paths
    rows = candidates({'Force': 34}, {'Force': 35}, {'Force': 40}, 10)
    paths = compare_finish_paths(rows, {'Force': 34}, {'Force': 35}, {'Force': 40}, 10)
    assert paths['Pa Fo']['path'] == ['Pa Fo']


def test_pool_plan_can_finish_above_minimum_within_natural_bounds():
    from forgely_pool_repair import pool_repair_plan
    rows = candidates({'Force': 34}, {'Force': 35}, {'Force': 40}, 3)
    plan, spent = pool_repair_plan([r for r in rows if r[1] == 'Pa Fo'], 3, {'Force': 40})
    assert plan == ('Pa Fo',)
    assert spent == 3


def test_pool_plan_does_not_count_surplus_as_additional_target_progress():
    from forgely_pool_repair import pool_repair_plan
    rows = candidates({'Force': 0}, {'Force': 10}, {'Force': 100}, 30)
    plan, spent = pool_repair_plan(rows, 30, {'Force': 100})
    assert plan == ('Ra Fo',)
    assert spent == 10


def test_satisfied_line_is_not_repaired_while_other_line_is_missing():
    rows = candidates({'Force': 45, 'Intelligence': 20}, {'Force': 40, 'Intelligence': 30},
                      {'Force': 60, 'Intelligence': 60}, 10)
    assert rows and all(r[2] == 'Intelligence' for r in rows)


def test_training_reward_ignores_surplus_loss_above_minimum():
    env = ForgemagingEnv([dict(stat='Force', value=45, min=1, max=60, weight=1)], 0, {'Force': 40})
    before = env.get_state()
    env.lines[0]['value'] = 41
    after = env.get_state()
    assert env.reward(before, after, cost=0) == 0
    assert env.get_valid_actions() == ['stop']


def test_explicit_over_minimum_does_not_cap_legal_rune_gain():
    rows = candidates({'Force': 44}, {'Force': 45}, {'Force': 40}, 10)
    assert 'Pa Fo' in {r[1] for r in rows}
    env = ForgemagingEnv([dict(stat='Force', value=44, min=1, max=40, weight=1)], 10, {'Force': 45})
    assert 'Pa Fo' in env.get_valid_actions()


def test_minimum_does_not_bypass_game_density_limit():
    rows = candidates({'Force': 100}, {'Force': 101}, {'Force': 40}, 100)
    assert {r[1] for r in rows} == {'Fo'}
    env = ForgemagingEnv([dict(stat='Force', value=100, min=1, max=40, weight=1)], 100, {'Force': 101})
    assert env.get_valid_actions() == ['Fo', 'stop']


@pytest.mark.parametrize('current, expected', [(39, 1), (40, 0), (45, 0)])
def test_progress_deficit_is_nonnegative_and_clamped_at_minimum(current, expected):
    from forgely_simulation_live import SimulationWorker
    assert SimulationWorker._deficit({'Force': current}, (('Force', 40),)) == expected


def test_signed_minimum_accepts_less_negative_current():
    assert advise({'Force': -5}, {'Force': -10}, {'Force': -1}, 0).kind == 'atteint'
    assert target_value({'Force': -5}, {'Force': -10}) == 1


def test_training_accepts_already_satisfied_initial_jet(tmp_path):
    from forgely_training import TrainingConfig, run_training
    result = run_training(TrainingConfig(14092, {'Force': 35}, initial_preset='maximum',
                          episodes=1, evaluation_episodes=1, max_steps=2), tmp_path)
    assert result['evaluation']['learned']['successes'] == 1
    assert result['evaluation']['baseline']['successes'] == 1
