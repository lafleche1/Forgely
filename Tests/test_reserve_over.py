import pytest
from forgely_decision import advise, candidates


def test_cycloide_compares_reserve_progression_instead_of_forcing_vitality():
    jet = {'Vitalité': 289, 'Force': 39, 'Intelligence': 39,
           'Dommages Neutre': 8, 'Dommages Terre': 9}
    maximum = {'Vitalité': 300, 'Force': 40, 'Intelligence': 40,
               'Dommages Neutre': 10, 'Dommages Terre': 10}
    p = advise(jet, maximum, maximum, 3.1, level=200, predictive_policy=True)
    assert p.rune == 'Pa Fo'
    assert p.kind == 'over'
    assert p.estimates['matrix']['optimal']['proposed'] == 42
    assert 'réserve' in p.explanation


@pytest.mark.parametrize('stat,rune', [('Force','Pa Fo'), ('Intelligence','Pa Ine'),
                                     ('Chance','Pa Cha'), ('Agilité','Pa Age')])
def test_pa_reserve_on_targeted_nearly_complete_line(stat, rune):
    jet = {stat: 39, 'Dommages Terre': 9}
    maximum = {stat: 40, 'Dommages Terre': 10}
    p = advise(jet, maximum, maximum, 3.1, level=200, predictive_policy=True)
    assert p.rune == rune


@pytest.mark.parametrize('pool,complete', [(0,False),(2.9,False),(3.1,False)])
def test_reserve_needs_complete_profile(pool, complete):
    rows = candidates({'Force':39,'Dommages Terre':9},
                      {'Force':40,'Dommages Terre':10},
                      {'Force':40,'Dommages Terre':10},pool,profile_complete=complete)
    assert 'Pa Fo' not in [r[1] for r in rows]


def test_no_reserve_when_goal_is_complete_or_line_is_ignored():
    assert advise({'Force':40},{'Force':40},{'Force':40},3.1,predictive_policy=True).rune is None
    rows = candidates({'Force':39,'Dommages Terre':9},
                      {'Force':0,'Dommages Terre':10},
                      {'Force':40,'Dommages Terre':10},3.1)
    assert 'Pa Fo' not in [r[1] for r in rows]


def test_ra_reserve_is_available_with_covered_weight():
    rows = candidates({'Vitalité':289,'Dommages Terre':9},
                      {'Vitalité':300,'Dommages Terre':10},
                      {'Vitalité':300,'Dommages Terre':10},10.1)
    assert 'Ra Vi' in [r[1] for r in rows]
    assert 'Ra Vi' not in [r[1] for r in candidates(
        {'Vitalité':289,'Dommages Terre':9}, {'Vitalité':300,'Dommages Terre':10},
        {'Vitalité':300,'Dommages Terre':10},3.1)]


@pytest.mark.parametrize('pool', [10,10.1,20,60])
@pytest.mark.parametrize('stat,rune', [('Vitalité','Ra Vi'),('Force','Ra Fo'),
                                     ('Intelligence','Ra Ine'),('Chance','Ra Cha'),
                                     ('Agilité','Ra Age')])
def test_ra_is_considered_at_ten_or_more_pool(pool,stat,rune):
    current,goal=(289,300) if stat=='Vitalité' else (39,40)
    p=advise({stat:current,'Dommages Terre':9},
             {stat:goal,'Dommages Terre':10},{stat:goal,'Dommages Terre':10},
             pool,predictive_policy=True)
    trace=p.estimates['decision_trace']['candidates'][rune]
    assert trace['reserve_over'] is True
    assert trace['phase_kept'] is True
