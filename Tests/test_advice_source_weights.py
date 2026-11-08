import pytest
from forgely_decision import combine_candidate_evidence, contextual_measurement


def test_fixed_40_60_weights_do_not_change_with_sample_count():
    simulation={'kind':'local_dofocus_model','probabilities':{'SC':30,'SN':50,'EC':20}}
    for n in (100,10000):
        real={'n':n,'counts':{'SC':n//2,'SN':0,'EC':n//2},'usable':True,'quality':'local_verified'}
        result=combine_candidate_evidence(simulation,real)
        assert result['weights']=={'simulation':.4,'real':.6}
        assert result['factor']==pytest.approx(.4*.8+.6*contextual_measurement(real)['success_ci95'][0])
        assert result['observations']==n


def test_missing_real_data_is_explicit_and_never_invented():
    result=combine_candidate_evidence({'kind':'local_dofocus_model',
        'probabilities':{'SC':30,'SN':50,'EC':20}},None)
    assert result['weights']=={'simulation':1.,'real':0.}
    assert result['configured_weights']=={'simulation':.4,'real':.6}
    assert result['fallback']=='simulation_only'


def test_recent_real_experience_uses_real_share_without_double_counting():
    sample={'kind':'local_dofocus_model','probabilities':{'SC':30,'SN':50,'EC':20}}
    experience={'kind':'experience_locale_indicative','n':2,'factor':.9}
    result=combine_candidate_evidence(sample,None,experience=experience)
    assert result['factor']==pytest.approx(.4*.8+.6*.8*.9)
    assert result['observations']==0
    assert result['experience_observations']==2


def test_failed_rare_exo_does_not_boost_the_advice_score():
    sample={'kind':'local_dofocus_model','probabilities':{'SC':1.5,'SN':0,'EC':98.5}}
    failure={'kind':'experience_locale_indicative','n':1,'factor':.99}
    assert combine_candidate_evidence(sample,None,experience=failure)['factor'] < .015


def test_learned_policy_adjusts_only_the_40_percent_simulation_share():
    sample={'kind':'local_dofocus_model','probabilities':{'SC':30,'SN':50,'EC':20},
        'trained_policy':{'kind':'trained_simulation_policy','source':'simulation',
                          'real_observations':0,'factor':1.2}}
    real={'n':100,'counts':{'SC':50,'SN':0,'EC':50},'usable':True,'quality':'local_verified'}
    result=combine_candidate_evidence(sample,real)
    assert result['factor']==pytest.approx(.4*.8*1.2+.6*contextual_measurement(real)['success_ci95'][0])
