import pytest
from forgely_decision import advise, candidates
from forgely_rl import ForgemagingEnv

@pytest.mark.parametrize('stat,current,small,pa', [
    ('Sagesse',38,'Sa','Pa Sa'), ('Intelligence',39,'Ine','Pa Ine'),
    ('Force',39,'Fo','Pa Fo'), ('Chance',39,'Cha','Pa Cha'),
    ('Agilité',39,'Age','Pa Age')])
def test_finish_compares_tiers_instead_of_exact_gap(stat,current,small,pa):
    # Natural room exists: no game over is involved, only minimum overshoot.
    p=advise({stat:current},{stat:40},{stat:60},61,predictive_policy=True)
    assert p.rune == pa


def test_single_intelligence_finish_allows_legal_natural_over():
    p=advise({'Intelligence':39},{'Intelligence':40},{'Intelligence':40},61,predictive_policy=True)
    # Here the shared model slightly favors Ine (17% versus 16.77%).
    assert p.rune == 'Ine'
    assert p.estimates['tier_comparison']['Intelligence'][1]['eligible']


def test_kido_density_guard_beats_available_pool():
    p=advise({'Sagesse':38},{'Sagesse':40},{'Sagesse':40},61,predictive_policy=True)
    rows=p.estimates['tier_comparison']['Sagesse']
    assert [(r['gain'],r['weight']) for r in rows]==[(1,3),(3,9),(10,30)]
    assert [r['eligible'] for r in rows]==[True,False,False]
    assert all('Plafond' in r['exclusion_reason'] for r in rows[1:])


def test_verified_empirical_rates_can_keep_small_rune():
    def context(rune):
        return {'verified':True,'counts':{'SC':100000 if rune=='Ine' else 0,
                'SN':0,'EC':0 if rune=='Ine' else 100000}}
    p=advise({'Intelligence':39},{'Intelligence':40},{'Intelligence':60},61,
             predictive_policy=True,context_for=context)
    assert p.rune=='Ine'


def test_training_explores_legal_finish_over():
    env=ForgemagingEnv([dict(stat='Intelligence',value=39,min=21,max=40,weight=1)],61,{'Intelligence':40})
    assert 'Pa Ine' in env.get_valid_actions()
    assert 'Ra Ine' in env.get_valid_actions()

def test_verified_rates_can_reject_covered_reserve_over():
    def context(rune):
        return {'verified':True,'counts':{'SC':100000 if rune=='Ine' else 0,
                'SN':0,'EC':0 if rune=='Ine' else 100000}}
    p=advise({'Intelligence':39,'Force':10},{'Intelligence':40,'Force':11},
             {'Intelligence':40,'Force':40},61,predictive_policy=True,context_for=context)
    assert p.rune != 'Pa Ine'

@pytest.mark.parametrize('winner', ['Ine','Pa Ine','Ra Ine'])
def test_finish_tier_is_selected_by_verified_rates(winner):
    def context(rune):
        return {'verified':True,'counts':{'SC':100000 if rune==winner else 0,
                'SN':0,'EC':0 if rune==winner else 100000}}
    p=advise({'Intelligence':39},{'Intelligence':40},{'Intelligence':40},61,
             predictive_policy=True,context_for=context)
    assert p.rune==winner


def test_training_cannot_bypass_kido_density_guard():
    env=ForgemagingEnv([dict(stat='Sagesse',value=38,min=31,max=40,weight=3)],61,{'Sagesse':40})
    assert env.get_valid_actions()==['Sa','stop']


def test_heavy_natural_objective_remains_prioritized():
    p=advise({'Intelligence':39,'PA':0},{'Intelligence':40,'PA':1},
             {'Intelligence':40,'PA':1},100,predictive_policy=True)
    assert p.rune=='Ga Pa'
