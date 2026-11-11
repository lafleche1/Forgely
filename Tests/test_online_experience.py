import pytest
from forgely_online_experience import OnlineExperience

BOUNDS={'Force':(1,40),'Vitalité':(1,300)}
BEFORE={'jet':{'Force':20,'Vitalité':290},'pool':5}
AFTER={'jet':{'Force':21,'Vitalité':290},'pool':5}


def test_first_confirmed_example_changes_score_with_small_influence():
    model=OnlineExperience()
    assert model.observe(1,'Anneau','Fo','SC',BEFORE,AFTER)
    result=model.evaluate('Anneau','Fo',BEFORE['jet'],5,{'Force':40},BOUNDS)
    assert result['n']==1 and 1<result['factor']<1.02
    assert result['kind']=='experience_locale_indicative'
    assert 'percentages' not in result


def test_close_states_share_experience_but_never_exact_rates():
    model=OnlineExperience();model.observe(1,'Anneau','Fo','SC',BEFORE,AFTER)
    close=model.evaluate('Anneau','Fo',{'Force':21,'Vitalité':289},5,{'Force':40},BOUNDS)
    assert close['n']==1 and close['exact']==0
    assert model.evaluate('Anneau','Fo',{'Force':39,'Vitalité':100},5,{'Force':40},BOUNDS) is None


def test_other_items_runes_incomplete_profiles_and_pool_regimes_are_isolated():
    model=OnlineExperience();model.observe(1,'Anneau','Fo','SC',BEFORE,AFTER)
    assert model.evaluate('Cape','Fo',BEFORE['jet'],5,{'Force':40},BOUNDS) is None
    assert model.evaluate('Anneau','Pa Fo',BEFORE['jet'],5,{'Force':40},BOUNDS) is None
    assert model.evaluate('Anneau','Fo',{'Force':20},5,{'Force':40},BOUNDS) is None
    assert model.evaluate('Anneau','Fo',BEFORE['jet'],0,{'Force':40},BOUNDS) is None


def test_collateral_damage_is_evaluated_against_current_targets():
    model=OnlineExperience()
    damaged={'jet':{'Force':21,'Vitalité':280},'pool':5}
    assert model.observe(1,'Anneau','Fo','SN',BEFORE,damaged)
    safe=model.evaluate('Anneau','Fo',BEFORE['jet'],5,{'Force':40},BOUNDS)
    fragile=model.evaluate('Anneau','Fo',BEFORE['jet'],5,{'Force':40,'Vitalité':300},BOUNDS)
    assert fragile['factor']<safe['factor']


@pytest.mark.parametrize('outcome,after',[
    ('SC',{'jet':{'Force':21,'Vitalité':280},'pool':5}),
    ('EC',AFTER),('SC',{'jet':{'Force':99,'Vitalité':290},'pool':5}),
    ('SC',{'jet':{'Force':True,'Vitalité':290},'pool':5}),
    ('SC',{'jet':{'Force':21},'pool':5}),
    ('SC',{'jet':{'Force':21,'Vitalité':300},'pool':5}),
    ('SN',{'jet':{'Force':21,'Vitalité':300},'pool':5}),
    ('EC',{'jet':{'Force':20,'Vitalité':300},'pool':5}),
])
def test_contradictory_or_missing_readings_do_not_train(outcome,after):
    model=OnlineExperience()
    assert not model.observe(1,'Anneau','Fo',outcome,BEFORE,after)
    assert model.evaluate('Anneau','Fo',BEFORE['jet'],5,{'Force':40},BOUNDS) is None


def test_replay_does_not_double_count_and_memory_is_bounded():
    model=OnlineExperience(max_samples=3)
    for index in range(1,8):model.observe(index,'Anneau','Fo','SC',BEFORE,AFTER)
    assert not model.observe(7,'Anneau','Fo','SC',BEFORE,AFTER)
    assert model.evaluate('Anneau','Fo',BEFORE['jet'],5,{'Force':40},BOUNDS)['n']==3


def test_experience_never_crosses_natural_to_over_boundary():
    model=OnlineExperience()
    before={'jet':{'Force':40,'Vitalité':290},'pool':5}
    after={'jet':{'Force':41,'Vitalité':290},'pool':5}
    model.observe(1,'Anneau','Fo','SC',before,after)
    assert model.evaluate('Anneau','Fo',{'Force':41,'Vitalité':290},5,{'Force':45},BOUNDS) is None


def test_same_item_name_from_manual_and_ocr_modes_shares_experience():
    model=OnlineExperience();model.observe(1,'Anneau du Cycloïde','Fo','SC',BEFORE,AFTER)
    assert model.evaluate('ANNEAU DU CYCLOÏDE','Fo',BEFORE['jet'],5,{'Force':40},BOUNDS)['n']==1
