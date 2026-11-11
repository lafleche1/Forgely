from unittest.mock import patch
import pytest
from forgely_decision import candidates,advise,combine_candidate_evidence


def simulation(sc='30',sn='50',ec='20'):
    return {'blocked':False,'display':{'SC':sc,'SN':sn,'EC':ec},
        'kind':'simulation_reference','real_observation':False,'captured_on':'2026-11-07'}


def observations(sc,sn,ec):
    return {'n':sc+sn+ec,'counts':{'SC':sc,'SN':sn,'EC':ec},
        'usable':True,'quality':'exploratoire_ocr_non_verifie'}


def test_player_results_adjust_reference_instead_of_multiplying_same_event_twice():
    base=combine_candidate_evidence(simulation(),None)
    calibrated=combine_candidate_evidence(simulation(),observations(100,0,0))
    assert calibrated['factor']>base['factor']
    assert calibrated['observations']==100
    assert calibrated['sources']==['simulation_dofocus','observations_joueurs_contextuelles']
    assert calibrated['is_game_probability'] is False


def test_disagreement_is_visible_and_real_failures_reduce_the_factor():
    result=combine_candidate_evidence(simulation(),observations(5,5,90))
    assert result['discordant']
    assert result['factor']<.8
    assert result['observations']==100


def test_too_few_or_malformed_player_results_cannot_claim_calibration():
    for record in (observations(1,0,0),{'n':100,'usable':True,'counts':{'SC':1000}}):
        result=combine_candidate_evidence(simulation(),record)
        assert result['observations']==0
        assert result['sources']==['simulation_dofocus']


def test_rounded_tiny_reference_is_not_mathematical_impossibility():
    result=combine_candidate_evidence(simulation('~0','~0','100'),None)
    assert 0<result['factor']<.01
    assert result['reference_interval'][0]==0


def test_unmatched_source_is_not_fabricated_and_no_players_are_invented():
    result=combine_candidate_evidence(None,observations(60,20,20))
    assert result['sources']==['observations_joueurs_contextuelles']
    assert result['observations']==100 and result['reference_interval'] is None


@patch('forgely_predictive.estimate',return_value=None)
def test_actual_candidate_score_uses_fused_factor_once(_video_model):
    state={'Force':20};targets={'Force':40};maximum={'Force':40}
    with patch('forgely_decision.lookup_context',return_value=None):
        original=next(row[0] for row in candidates(state,targets,maximum,5,item='Anneau') if row[1]=='Fo')
    sample=simulation();record=observations(100,0,0)
    with patch('forgely_decision.lookup_context',return_value={'Fo':sample}):
        score=next(row[0] for row in candidates(state,targets,maximum,5,item='Anneau',
            simulation_for=lambda rune:sample if rune=='Fo' else None,
            contextual_for=lambda rune:record if rune=='Fo' else None) if row[1]=='Fo')
    factor=combine_candidate_evidence(sample,record)['factor']
    assert score==pytest.approx((original+.0004)*factor-.0004)


def test_proposal_exposes_disagreement_and_separates_sources():
    # All real successes disagree with the active model at 39/40, independently
    # of the historical Dofocus display retained for descriptive comparison.
    sample=simulation();record=observations(100,0,0)
    with patch('forgely_decision.natural_profile',return_value={'Force':40}), \
         patch('forgely_decision.lookup_context',return_value={'Fo':sample}), \
         patch('forgely_decision.lookup',return_value=sample):
        result=advise({'Force':39},{'Force':40},pool=5,item='Anneau',
            simulation_for=lambda rune:sample,
            contextual_for=lambda rune:record)
    assert result.estimates['source_comparison']['discordant']
    assert 'Écart' in result.explanation
    assert result.estimates['objective']['goal_probability'] is None
