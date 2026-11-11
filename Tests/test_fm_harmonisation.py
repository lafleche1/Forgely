from random import Random
import pytest
from forgely_dofocus_engine import attempt, odds
from forgely_predictive import estimate
from forgely_rules import constraints


def line(stat,value,maximum=100,weight=1):
    return dict(stat=stat,value=value,min=0,max=maximum,weight=weight)


def test_large_pool_survives_failure_and_sc_without_artificial_cap():
    lines=[line('Force',10)]
    result=attempt(lines,{'stat':'Force','gain':1,'weight':1},180,
                   probabilities={'sc':0,'sn':0,'ec':100},rng=Random(2))
    assert result['pool']==179
    result=attempt(lines,{'stat':'Force','gain':1,'weight':1},180,
                   probabilities={'sc':100,'sn':0,'ec':0},rng=Random(2))
    assert result['pool']==180


@pytest.mark.parametrize('rune,spec,lines,maxima',[
    ('Fo',dict(stat='Force',gain=1,weight=1),[line('Force',15)],{'Force':100}),
    ('Pa Fo',dict(stat='Force',gain=3,weight=3),[line('Force',79)],{'Force':100}),
    ('Ga Pa',dict(stat='PA',gain=1,weight=100),[line('Force',20),dict(stat='PA',value=0,min=None,max=None,weight=100)],{'Force':100}),
    ('Ine',dict(stat='Intelligence',gain=1,weight=1),[line('Force',40,40),line('Intelligence',40,40)],{'Force':40,'Intelligence':40}),
])
def test_prediction_and_training_use_identical_base_probabilities(rune,spec,lines,maxima):
    jet={x['stat']:x['value'] for x in lines}
    p=estimate(jet,maxima,rune,level=160)
    q=odds(lines,spec,level=160)
    assert not q.get('blocked')
    assert [q[k.lower()] for k in ('SC','SN','EC')]==pytest.approx([p[k] for k in ('SC','SN','EC')])


def test_advisor_and_simulator_share_conservative_constraints():
    lines=[line('Force',100,40),line('Intelligence',100,40)]
    assert constraints({'Force':101,'Intelligence':100},{'Force':40,'Intelligence':40})['valid']
    assert not odds(lines,dict(stat='Force',gain=1,weight=1)).get('blocked')


def test_unverified_signed_rules_are_explicitly_unavailable_everywhere():
    from forgely_rl import ForgemagingEnv
    from forgely_decision import advise
    signed=[dict(stat='Force',value=-8,min=-20,max=-8,weight=1)]
    result=odds(signed,dict(stat='Force',gain=1,weight=1))
    assert result.get('blocked')=='signed-profile-unsupported'
    with pytest.raises(ValueError,match='malus'):
        ForgemagingEnv(signed,0,{'Force':0})
    p=advise({'Force':-8},{'Force':0},{'Force':-8},0)
    assert p.rune and 'malus' in p.explanation
    assert p.estimates['prediction'] is None


def test_already_calibrated_evidence_is_not_counted_twice():
    from forgely_decision import combine_candidate_evidence
    sample={'kind':'local_dofocus_model','probabilities':{'SC':70,'SN':0,'EC':30},'empirical_n':100}
    counts={'usable':True,'quality':'local_verified','n':100,'counts':{'SC':0,'SN':0,'EC':100}}
    result=combine_candidate_evidence(sample,counts)
    assert result['factor']==pytest.approx(.7)
    assert result['fallback']=='shared_posterior'


def test_pool_policy_does_not_override_shared_odds_with_old_fixed_bands():
    from forgely_predictive import rank_options,option_payload
    from forgely_dofocus import reference
    def row(rune,stat,current,goal,success):
        return (.5,rune,stat,'fm_classique',reference(rune),
                {'prediction':{'SC':success,'SN':0,'EC':100-success}},None,None,current,goal)
    options=[row('Fo','Force',39,40,1),row('Ine','Intelligence',40,41,99)]
    ranked,meta=rank_options(options,{'Force':39,'Intelligence':40},{'Force':40,'Intelligence':40},0)
    assert ranked[0][1]=='Ine'
    payload=option_payload(ranked[0],{'Force':40,'Intelligence':40},.99,0)
    assert payload['probability_source']=='shared_fm_model'
    assert payload['success_band']==(99,99)


def test_advice_uses_known_item_level_from_shared_live_prediction():
    from forgely_simulation_live import SimulationWorker
    from forgely_decision import advise
    worker=SimulationWorker(trials=16)
    try:
        context=worker.context('Gelano',{'PA':0},180,{'PA':1})
        proposal=advise({'PA':0},{'PA':1},pool=180,item='Gelano',simulation_for=context.evidence)
        assert proposal.estimates['prediction']['SC']==context.evidence('Ga Pa')['probabilities']['SC']
    finally:worker.stop()
