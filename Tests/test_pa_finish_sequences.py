import pytest
from forgely_decision import advise, candidates
from forgely_dofocus import RUNE_CHOICES

@pytest.mark.parametrize('stat', ['Force','Intelligence','Agilité','Chance','Sagesse'])
@pytest.mark.parametrize('current', [31,34,37])
def test_pa_paths_survive_small_pool_policy(stat,current):
    p=advise({stat:current},{stat:40},{stat:40},1.3,level=200,predictive_policy=True)
    assert p.rune==RUNE_CHOICES[stat][1]
    trace=p.estimates['decision_trace']['candidates'][p.rune]
    path=trace['nominal_sequence']
    assert path['path']==[p.rune]*((40-current)//3)
    assert path['cost']>0
    assert path['source']=='provisional_nominal_paths'


def test_other_useful_pool_repair_before_force():
    p=advise({'Force':34,'Vitalité':288},{'Force':40,'Vitalité':300},
             {'Force':40,'Vitalité':300},1.3,level=200,predictive_policy=True)
    assert p.rune=='Vi'


def test_target_one_point_away_accepts_better_natural_finishing_path():
    # Pa Fo finishes at 37: crossing the desired 35 is accepted below max 40.
    assert advise({'Force':34},{'Force':35},{'Force':40},1.3,level=200,predictive_policy=True).rune=='Pa Fo'


def test_comparable_evidence_can_favor_simple_rune():
    def context(rune):
        return {'verified':True,'counts':{'SC':10000 if rune=='Fo' else 0,'SN':0,'EC':0 if rune=='Fo' else 10000}}
    p=advise({'Force':34},{'Force':40},{'Force':40},1.3,level=200,
             predictive_policy=True,context_for=context)
    assert p.rune=='Fo'


def test_capture_cycloide_uses_pool_on_other_target_and_keeps_two_pa_path():
    jet={'Vitalité':288,'Force':34,'Intelligence':40,'Agilité':38,
         'Dommages Neutre':9,'Dommages Terre':10,'Dommages Feu':10,
         'Dommages Air':5,'Initiative':176,'% Résistance Eau':7,'Tacle':6}
    maximum=dict(zip(jet,(300,40,40,40,10,10,10,10,300,8,6)))
    target={**maximum,'Initiative':100,'Tacle':0}
    p=advise(jet,target,maximum,1.3,level=200,predictive_policy=True)
    assert p.rune=='Vi'
    paths=p.estimates['decision_trace']['candidates']
    assert paths['Pa Fo']['nominal_sequence']['path']==['Pa Fo','Pa Fo']
    assert paths['Pa Fo']['nominal_sequence']['cost']<paths['Fo']['nominal_sequence']['cost']


def test_future_steps_do_not_reuse_current_context():
    calls=[]
    def context(rune):
        calls.append(rune)
        return None
    candidates({'Force':31},{'Force':40},{'Force':40},1.3,level=200,
               context_for=context)
    assert calls==['Fo','Pa Fo']


def test_price_does_not_change_pa_path():
    from forgely_pricing import PriceBook
    book=PriceBook({'Fo':1,'Pa Fo':100000},server='test',observed_on='2026-11-10')
    p=advise({'Force':34},{'Force':40},{'Force':40},1.3,level=200,
             predictive_policy=True,price_book=book)
    assert p.rune=='Pa Fo'
    assert 'pricing' not in p.estimates


def test_other_stats_and_partial_profiles_do_not_get_pa_rule():
    for jet,target,complete in [({'Vitalité':31},{'Vitalité':40},True),
                               ({'Force':34},{'Force':40},False)]:
        p=advise(jet,target,target,1.3,profile_complete=complete,predictive_policy=True)
        assert all('nominal_sequence' not in r for r in p.estimates['decision_trace']['candidates'].values())
