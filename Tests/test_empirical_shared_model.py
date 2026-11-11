from copy import deepcopy
from random import Random
import pytest
from forgely_empirical_model import EmpiricalModel, load_empirical_model
from forgely_video_store import item_profile, transfer_session
from forgely_equipment_catalog import equipment_bounds
from forgely_dofocus_engine import odds


def records(count=30):
    item,profile=item_profile(14092)
    before=dict(profile);before['Force']=10
    after=dict(before);after['Force']=8
    return [dict(id=f'e{i}',time=i+1,item_id=14092,rune='Fo',outcome='EC',
                 before={'jet':before,'pool':0},after={'jet':after,'pool':1},natural_max=profile,
                 event_confirmed=True,stable=True,issues=[],status='candidate',
                 evidence={'before':'b.png','after':'a.png'},source='video_verified') for i in range(count)]


def lines():
    item,profile=item_profile(14092);bounds=equipment_bounds(item)
    from forgely_dofocus import WEIGHT_PER_POINT
    return [dict(stat=s,value=10 if s=='Force' else maximum,min=bounds[s][0],max=maximum,weight=WEIGHT_PER_POINT[s]) for s,maximum in profile.items()]


def test_real_video_updates_probabilities_and_observed_loss_distribution(tmp_path):
    events=records();db=tmp_path/'obs.db'
    transfer_session({'id':'a'*64,'events':events},db)
    model=load_empirical_model(db)
    spec=dict(stat='Force',gain=1,weight=1)
    base=odds(lines(),spec,level=200)
    adjusted=model.probabilities(14092,lines(),spec,0,level=200)
    assert adjusted['empirical_n']==30
    assert adjusted['ec']==pytest.approx((200*base['ec']+3000)/230)
    sampled=[]
    for seed in range(100):
        result=model.attempt(14092,lines(),spec,0,level=200,rng=Random(seed))
        if result.get('empirical_loss_sampled'):
            sampled.append(result)
            assert result['pool']==1
            assert next(x['value'] for x in result['lines'] if x['stat']=='Force')==8
    assert sampled
    for other in (12114,None):
        assert 'empirical_n' not in model.probabilities(other,lines(),spec,0,level=200)
    assert 'empirical_n' not in model.probabilities(14092,lines(),spec,1,level=200)


def test_snapshot_is_reproducible_and_rejection_retracts_without_mutating_old_model(tmp_path):
    events=records();db=tmp_path/'obs.db';session={'id':'a'*64,'events':events}
    transfer_session(session,db);model=load_empirical_model(db)
    path=tmp_path/'snapshot.json';model.save(path)
    assert EmpiricalModel.load(path).digest==model.digest
    for e in events:e['status']='rejected'
    transfer_session(session,db)
    assert load_empirical_model(db).sample_count==0
    assert model.sample_count==30


def test_no_uncertified_or_simulated_transition_is_used():
    bad=records(1)[0];bad['source']='simulation'
    assert EmpiricalModel([bad]).sample_count==0
    bad=records(1)[0];bad['issues']=['multiple_events']
    assert EmpiricalModel([bad]).sample_count==0
    model=EmpiricalModel(records(29))
    assert 'empirical_n' not in model.probabilities(14092,lines(),dict(stat='Force',gain=1,weight=1),0,level=200)


def test_unrelated_objects_do_not_change_an_items_model_revision():
    from test_video_store import event
    other=event();other['source']='video_verified'
    a=EmpiricalModel(records());b=EmpiricalModel([*records(),other])
    assert a.for_item(14092).digest==b.for_item(14092).digest
    assert b.for_item(2469).sample_count==1


def test_snapshot_preserves_conditional_loss_rng_order(tmp_path):
    events=records()
    for i,e in enumerate(events):
        e['after']=deepcopy(e['after'])
        if i%2:e['after']['jet']['Force']=7;e['after']['pool']=2
    model=EmpiricalModel(events);path=tmp_path/'snapshot.json';model.save(path)
    restored=EmpiricalModel.load(path);spec=dict(stat='Force',gain=1,weight=1)
    assert model.digest==restored.digest
    for seed in range(100):
        assert model.attempt(14092,lines(),spec,0,rng=Random(seed))==restored.attempt(14092,lines(),spec,0,rng=Random(seed))
