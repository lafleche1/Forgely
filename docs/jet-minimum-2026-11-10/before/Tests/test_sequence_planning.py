from copy import deepcopy
from forgely_sequence import plan_sequences


def state():
    return [{'stat':'Force','value':38,'min':20,'max':40,'weight':1}]


def test_complete_target_is_terminal_and_never_spends_another_rune():
    assert plan_sequences(state(),0,{'Force':38},level=200,seed=1)=={}


def test_planning_preserves_live_inputs_and_is_reproducible():
    lines=state();saved=deepcopy(lines)
    first=plan_sequences(lines,5,{'Force':40},level=200,seed=10,trials=16,horizon=4)
    assert lines==saved
    assert first==plan_sequences(lines,5,{'Force':40},level=200,seed=10,trials=16,horizon=4)
    assert set(first)=={'Fo'}
    evidence=first['Fo']
    assert evidence['kind']=='sequence_rollouts'
    assert evidence['real_observations']==0
    assert 0<=evidence['completed']<=16
    assert 0<=evidence['value']<=1
    assert evidence['horizon']==4


def test_stale_context_cancels_the_whole_comparison():
    assert plan_sequences(state(),5,{'Force':40},level=200,seed=1,cancelled=lambda:True) is None


def test_final_success_has_priority_over_partial_progress():
    # A completed jet has value 1; every incomplete state remains below .1.
    from forgely_sequence import target_value
    assert target_value({'Force':40,'Vitalité':100},{'Force':40,'Vitalité':100})==1
    assert target_value({'Force':39,'Vitalité':100},{'Force':40,'Vitalité':100})<.1


def test_sequence_results_can_reverse_immediate_ranking():
    from forgely_decision import candidates
    def evidence(rune):
        return {'kind':'local_dofocus_model','blocked':False,
                'probabilities':{'SC':50,'SN':50,'EC':0},
                'sequence':{'kind':'sequence_rollouts','source':'simulation','real_observations':0,
                            'trials':16,'horizon':4,'completed':16 if rune=='Fo' else 0,
                            'value':1. if rune=='Fo' else .01,'mean_steps':3}}
    plain=candidates({'Force':36},{'Force':40},{'Force':40},5)
    assert plain[0][1]=='Pa Fo'
    planned=candidates({'Force':36},{'Force':40},{'Force':40},5,simulation_for=evidence)
    assert planned[0][1]=='Fo'


def test_partial_or_invalid_comparisons_never_replace_the_ranking():
    from forgely_decision import candidates
    args=({'Force':36},{'Force':40},{'Force':40},5)
    baseline=candidates(*args)
    assert candidates(*args,simulation_for=lambda r:{'sequence':{'value':float('nan')}})==baseline


def test_real_calibration_is_verified_and_uses_common_prior():
    from forgely_sequence import calibrated_probabilities
    base={'sc':10.,'sn':40.,'ec':50.}
    sparse={'usable':True,'quality':'exploratoire_ocr_non_verifie','n':30,
            'counts':{'SC':0,'SN':0,'EC':30}}
    assert calibrated_probabilities(base,sparse) is None
    sparse={**sparse,'quality':'local_verified','verified':True}
    result=calibrated_probabilities(base,sparse)
    assert 45 < result['ec'] < 65
    assert sum(result[k] for k in ('sc','sn','ec'))==100
    assert result['weights']=={'simulation':1-30/230,'real':30/230}
    assert result['discordant'] is True
    assert calibrated_probabilities(base,{**sparse,'usable':False}) is None


def test_difficult_training_replays_failures_but_evaluates_original_sessions(tmp_path):
    from forgely_training import run_training,TrainingConfig
    result=run_training(TrainingConfig(item_id=14092,targets={'Force':40,'Intelligence':40},
                       episodes=8,max_steps=2,evaluation_episodes=3),tmp_path)
    assert result['curriculum']['replayed_episodes']>0
    assert result['curriculum']['evaluation_replay'] is False
    assert result['evaluation']['baseline']['episodes']==3


def test_holdout_rejects_a_sequence_that_loses_against_the_baseline():
    from forgely_sequence import validate_choice
    planned={'Fo':{'value':.5,'mean_steps':2},'Pa Fo':{'value':.2,'mean_steps':2}}
    holdout={'Fo':{'value':.1,'completed':1},'Pa Fo':{'value':.3,'completed':3}}
    assert validate_choice(planned,holdout,'Pa Fo')['accepted'] is False
    assert validate_choice(planned,holdout,'Fo')['selected']=='Fo'


def test_background_calibration_uses_real_context_and_revision():
    import threading
    from test_simulation_live import cycloid
    from forgely_simulation_live import SimulationWorker
    item,jet=cycloid();jet['Force']=39
    ready=threading.Event()
    def real_for(item_name,rune,current,pool):
        assert item_name==item.identity_name and current==jet
        return {'usable':True,'n':100,'counts':{'SC':100,'SN':0,'EC':0},'quality':'local_verified','verified':True}
    worker=SimulationWorker(trials=16,real_for=real_for,on_ready=lambda key:ready.set())
    try:
        context=worker.context(item.identity_name,jet,0,{'Force':40},revision=1)
        assert ready.wait(10)
        row=context.evidence('Fo')['sequence']
        assert row['calibration']['observations']==100
        assert row['calibration']['weights']=={'simulation':1-100/300,'real':100/300}
        assert row['validation']['statistical_superiority'] is False
        second=worker.context(item.identity_name,jet,0,{'Force':40},revision=2)
        assert second.key!=context.key
    finally:worker.stop()


def test_one_complete_rollout_beats_any_number_of_partial_only_rollouts():
    from forgely_sequence import rollout_value
    assert rollout_value(1,32,1)>rollout_value(0,32,3.2)
    assert rollout_value(32,32,32)==1


def test_published_advice_keeps_the_exact_holdout_validated_choice():
    from forgely_decision import candidates
    def evidence(rune):
        return {'kind':'local_dofocus_model','blocked':False,
                'probabilities':{'SC':50,'SN':50,'EC':0},
                'sequence':{'kind':'sequence_rollouts','source':'simulation','real_observations':0,
                    'trials':16,'horizon':4,'completed':8,'value':.5 if rune=='Fo' else .51,'mean_steps':3,
                    'validation':{'accepted':True,'selected':'Fo','baseline':'Pa Fo'}}}
    assert candidates({'Force':36},{'Force':40},{'Force':40},5,simulation_for=evidence)[0][1]=='Fo'


def test_continuations_use_the_shared_line_guards_without_extra_cumulative_over_cap():
    from forgely_sequence import options
    lines=[{'stat':'Force','value':60,'min':20,'max':40,'weight':1},
           {'stat':'Intelligence','value':80,'min':20,'max':40,'weight':1}]
    assert {row[1] for row in options(lines,0,{'Intelligence':85})}=={'Ine','Pa Ine'}
    lines[1]['value']=101
    assert options(lines,0,{'Intelligence':102})==[]
