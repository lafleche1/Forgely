import pytest
from forgely_decision import candidates, advise
from forgely_predictive import rank_options

JET = {'Vitalité':288,'Force':38,'Intelligence':40,'Agilité':38,
       'Dommages Neutre':6,'Dommages Terre':10,'Dommages Feu':10,
       'Dommages Air':8,'Initiative':146,'% Résistance Eau':7,'Tacle':5}
MAX = dict(zip(JET, (300,40,40,40,10,10,10,10,300,8,6)))

@pytest.mark.parametrize('pool', [0,4.3])
def test_cycloide_compares_every_vitality_tier_including_covered_reserve(pool):
    p=advise(JET,MAX,MAX,pool,predictive_policy=True,level=200)
    rows=p.estimates['tier_comparison']['Vitalité']
    assert [r['rune'] for r in rows]==['Vi','Pa Vi','Ra Vi']
    assert [r['gain'] for r in rows]==[5,15,50]
    assert [r['weight'] for r in rows]==[1,3,10]
    assert [r['resulting_value'] for r in rows]==[293,303,338]
    assert [r['eligible'] for r in rows]==[True,pool>=3,False]
    assert rows[0]['expected_capped_progress']==pytest.approx(.85)
    assert all(r['expected_net_progress'] is None for r in rows)
    assert all(r['degradation_exposure']>=0 for r in rows)

@pytest.mark.parametrize('pool',[0, .3, 4.3, 30,100])
def test_pool_policy_compares_covered_and_exposed_reserves(pool):
    jets={'Vitalité':288,'Agilité':38}; targets={'Vitalité':300,'Agilité':40}
    rows=candidates(jets,targets,targets,pool)
    ordered,meta=rank_options(rows,jets,targets,pool)
    if pool>=3:
        assert ordered[0][1]=='Pa Vi'
        assert meta['reserve_over_preferred'] is True
    else:
        assert ordered[0][1]=='Pa Age'
        assert meta['reserve_over_preferred'] is True
        assert 'exposé' in meta['reason']

@pytest.mark.parametrize('value,maximum',[(288,300),(295,300),(98,100)])
def test_saturated_line_comparison_never_claims_official_probabilities(value,maximum):
    p=advise({'Vitalité':value},{'Vitalité':maximum},{'Vitalité':maximum},0)
    rows=p.estimates['tier_comparison']['Vitalité']
    assert len(rows)==3
    assert all(r['source']=='provisional_shared_model' for r in rows)
    assert all(r['expected_capped_progress']<=maximum-value for r in rows)

def test_nominal_pool_plan_cannot_override_validated_sequence():
    rows=candidates({'Force':37},{'Force':40},{'Force':40},1)
    rows.sort(key=lambda r:r[1]!='Pa Fo')
    for row in rows:row[5]['decision_trace']['sequence_used']=True
    ordered,meta=rank_options(rows,{'Force':37},{'Force':40},1)
    assert ordered[0][1]=='Pa Fo'
    assert meta['sequence_preserved'] is True

@pytest.mark.parametrize('pool',[0,4.3])
def test_visible_four_targets_compare_pa_reserves_even_without_pool(pool):
    targets={s:MAX[s] for s in ('Vitalité','Force','Intelligence','Agilité')}
    p=advise(JET,targets,MAX,pool,predictive_policy=True,level=200)
    assert p.rune==('Pa Vi' if pool>=3 else 'Pa Age')
    assert 'réserve' in p.explanation
    assert 'inconnue' in p.explanation
    assert p.estimates['tier_comparison']['Vitalité'][1]['eligible'] is (pool>=3)
