from forgely_decision import advise


def test_live_policy_large_pool_prioritizes_heavy_natural_lines():
    p=advise({'Force':20,'Portée':0},{'Force':40,'Portée':1},
             natural_max={'Force':40,'Portée':1},pool=60,predictive_policy=True)
    assert p.rune=='Po'
    assert p.estimates['matrix']['phase']=='large'


def test_fractional_pool_compares_all_tiers_and_labels_theoretical_rates():
    p=advise({'Force':20},{'Force':40},natural_max={'Force':40},pool=.9,predictive_policy=True)
    assert p.rune in ('Fo','Pa Fo','Ra Fo')
    assert p.estimates['matrix']['phase']=='fractional'
    assert not p.estimates['matrix']['excluded']
    opt=p.estimates['matrix']['optimal']
    prediction=p.estimates['prediction']
    probability=prediction['SC']+prediction['SN']
    assert opt['success_band']==(probability,probability)
    assert opt['probability_source']=='shared_fm_model'
    assert opt['pool_SC']=='0.9'
    assert opt['pool_SN_EC_without_losses']=='0'


def test_requested_success_bands_and_no_rates_without_natural_profile():
    from forgely_predictive import success_band
    assert success_band('Force',10,1,{'Force':40},.5)==(60,70)
    assert success_band('Force',39,1,{'Force':40},.98)==(30,45)
    assert success_band('Force',40,3,{'Force':40},1)==(20,30)
    assert success_band('Force',40,10,{'Force':40},1)==(10,15)
    assert success_band('PA',0,1,{},1)==(1,1)
    assert success_band('Force',10,1,None,None) is None


def test_zero_pool_cleanup_is_risky_and_not_a_guaranteed_pool_gain():
    from forgely_predictive import report_text
    p=advise({'Force':5},{'Force':40},natural_max={'Force':40},pool=0,predictive_policy=True)
    assert p.rune=='Ra Fo'
    text=report_text(p,{'Force':5},{'Force':40},{'Force':40},0)
    assert '[ÉTAT MATRICIEL]' in text and '[PRÉDICTION DU TOUR]' in text and '[RECOMMANDATION IA]' in text
    assert 'nettoyage' in text.lower() and 'garanti' not in text.lower()


def test_medium_pool_targets_intermediate_lines_before_basic_stats():
    p=advise({'Sagesse':10,'Force':10},{'Sagesse':30,'Force':40},
             natural_max={'Sagesse':30,'Force':40},pool=30,predictive_policy=True)
    assert 'Sa' in p.rune


def test_large_pool_never_invents_a_heavy_target():
    p=advise({'Force':20},{'Force':40},natural_max={'Force':40},pool=51,predictive_policy=True)
    assert p.rune in ('Fo','Pa Fo','Ra Fo')
    assert p.estimates['matrix']['pool_repair_preferred'] is True


def test_partial_profile_cannot_prove_saturation_or_major_exo_rate():
    from forgely_predictive import success_band
    assert success_band('PA',0,1,{'Force':40},None,False) is None
    p=advise({'Force':20},{'Force':40},natural_max={'Force':40},profile_complete=False,
             pool=5,predictive_policy=True)
    assert p.estimates['matrix']['saturation'] is None
    assert p.estimates['matrix']['optimal']['success_band'] is None
