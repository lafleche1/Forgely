import math
import pytest
from forgely_decision import advise, candidates
from forgely_fm_model import check_budget


def test_over_limit_is_total_line_not_only_surplus():
    assert not candidates({'Force': 101}, {'Force': 102}, {'Force': 100}, 100)
    assert check_budget({'Force': 102}, {'Force': 100})['valid'] is False
    assert check_budget({'Force': 120}, {'Force': 120})['valid'] is True


def test_overs_on_separate_lines_are_not_a_global_extra_budget():
    assert check_budget({'Force': 101, 'Agilité': 101}, {'Force': 1, 'Agilité': 1})['valid'] is True


def test_exotic_density_is_cumulative():
    assert check_budget({'PA': 1, 'Force': 2}, {})['valid'] is False
    assert check_budget({'PA': 1, 'Force': 1}, {})['valid'] is True


def test_incomplete_profile_never_proves_exotic():
    p = advise({'PA': 0}, {'PA': 1}, natural_max={'Force': 100}, pool=0,
               profile_complete=False)
    assert p.kind == 'inconnu'
    assert p.estimates['benchmark']['SC'] is None


def test_legacy_economic_mode_uses_target_progress():
    kw = dict(jets={'Force': 0}, targets={'Force': 10}, natural_max={'Force': 100},
              pool=30, prices={'Fo': 1, 'Pa Fo': 100, 'Ra Fo': 10000})
    chance = advise(**kw, mode='Chances maximales')
    economy = advise(**kw, mode='Budget optimisé')
    assert chance.rune == 'Ra Fo'
    assert economy.rune == chance.rune
    assert chance.estimates['benchmark']['SC'] is None
    assert economy.estimates['objective']['mode'] == 'Chances maximales'


def test_old_economy_and_remaining_budget_are_ignored():
    kw = dict(jets={'Force': 0}, targets={'Force': 10}, pool=30, mode='Budget optimisé')
    assert advise(**kw).rune == 'Ra Fo'
    assert advise(**kw, prices={'Fo': 5}, remaining_budget=4).rune == 'Ra Fo'
    assert advise(**kw, prices={'Fo': 5}, remaining_budget=5).rune == 'Ra Fo'
    assert advise(**kw, prices={'Fo': 5}, remaining_budget=0).rune == 'Ra Fo'


def test_natural_restoration_before_final_exotic():
    p = advise({'PA': 0, 'Force': 0}, {'PA': 1, 'Force': 60},
               natural_max={'Force': 60}, pool=100, mode='Chances maximales')
    assert p.rune != 'Ga Pa'


def test_small_gap_compares_covered_legal_finishing_tiers():
    p = advise({'Vitalité': 299}, {'Vitalité': 300}, natural_max={'Vitalité': 350}, pool=5)
    # A bigger rune stays natural and has better predicted success near this target.
    assert p.rune == 'Ra Vi'
    finishing=candidates({'Vitalité': 299}, {'Vitalité': 300}, {'Vitalité': 300}, 5)
    assert {row[1] for row in finishing}=={'Vi','Pa Vi'}
    assert finishing[0][3]=='over'


@pytest.mark.parametrize('bad', [math.nan, math.inf, -math.inf, True])
def test_invalid_numbers_never_produce_a_rune(bad):
    assert advise({'Force': bad}, {'Force': 10}, pool=5).rune is None
    assert advise({'Force': 0}, {'Force': 10}, pool=bad).rune is None


def test_goal_reached_stops_even_with_empty_budget():
    assert advise({'Force': 10}, {'Force': 10}, pool=0,
                  mode='Budget optimisé', remaining_budget=0).kind == 'atteint'


@pytest.mark.parametrize('price', ['invalid', math.nan, math.inf, True, -1])
def test_old_prices_are_absent_from_all_outputs(price):
    p = advise({'Force': 0}, {'Force': 1}, pool=5, prices={'Fo': price})
    assert p.rune == 'Fo'
    assert 'Prix' not in p.explanation
    assert 'price' not in p.estimates['objective']['alternatives'][0]
