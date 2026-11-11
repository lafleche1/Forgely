import json
from forgely_video_store import transfer_session
from forgely_training import TrainingConfig,run_training
from auditer_politique import audit_policy
from forgely_labo_live import LiveLaboratory


def gelano_events():
    return [dict(id=f'e{i}',time=i+1,item_id=2469,rune='Ga Pme',outcome='EC',
                 before={'jet':{'PA':1,'PM':0},'pool':0},after={'jet':{'PA':0,'PM':0},'pool':10},
                 natural_max={'PA':1},event_confirmed=True,stable=True,issues=[],status='candidate',
                 evidence={'before':'before.png','after':'after.png'}) for i in range(30)]


def test_training_and_independent_audit_pin_real_evidence_snapshot(tmp_path):
    db=tmp_path/'obs.db';events=gelano_events()
    transfer_session({'id':'a'*64,'events':events},db)
    config=TrainingConfig(item_id=2469,targets={'PA':1,'PM':1},episodes=3,max_steps=5,
                           evaluation_episodes=3,use_real_observations=True)
    result=run_training(config,tmp_path/'training',empirical_db=db)
    assert result['empirical_observations']==30 and result['real_observations']==0
    folder=tmp_path/'training'/result['run_id']
    assert (folder/'empirical_snapshot.json').is_file()
    before=audit_policy(folder/'policy.json',episodes=3,seed=32)
    for event in events:event['status']='rejected'
    transfer_session({'id':'a'*64,'events':events},db)
    assert audit_policy(folder/'policy.json',episodes=3,seed=32)==before
    newer=run_training(config,tmp_path/'training',empirical_db=db)
    assert newer['signature']!=result['signature']
    assert not newer['resumed_from'] and newer['empirical_observations']==0


def test_live_calibration_and_simulator_receive_same_qualified_video_data(tmp_path):
    from forgely_simulation_live import SimulationWorker
    db=tmp_path/'obs.db';transfer_session({'id':'a'*64,'events':gelano_events()},db)
    live=LiveLaboratory(db);live.refresh_if_changed()
    record=live.estimate('Gelano','Ga Pme',{'PA':1,'PM':0},0)
    assert record['quality']=='local_verified' and record['counts']['EC']==30
    worker=SimulationWorker(empirical_for=live.empirical_model)
    context=worker.context('Gelano',{'PA':1,'PM':0},0,{'PA':1,'PM':1},revision=live.revision)
    assert context.evidence('Ga Pme')['empirical_n']==30
    from forgely_decision import advise
    proposal=advise({'PA':1,'PM':0},{'PA':1,'PM':1},pool=0,item='Gelano',
        simulation_for=context.evidence,context_for=lambda rune:live.calibration('Gelano',rune,{'PA':1,'PM':0},0))
    assert proposal.estimates['prediction']['SC']==context.evidence('Ga Pme')['probabilities']['SC']
    assert proposal.estimates['prediction']['calibration_n']==30
    assert proposal.estimates['source_comparison']['fallback']=='shared_posterior'
    assert context.environment().transition_model is not None
    worker.stop()
