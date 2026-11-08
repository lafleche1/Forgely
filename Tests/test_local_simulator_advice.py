import threading
from unittest.mock import patch
from forgely_decision import advise,candidates,combine_candidate_evidence
from forgely_simulation_live import SimulationWorker
from test_simulation_live import cycloid


def test_new_full_state_gets_local_predictions_and_keeps_players_separate():
    item,jet=cycloid();jet['Force']=39
    worker=SimulationWorker(trials=24)
    try:
        context=worker.context(item.name,jet,2.7,{'Force':40})
        with patch('forgely_decision.lookup_context',return_value=None), \
             patch('forgely_decision.lookup',return_value=None):
            proposal=advise(jet,{'Force':40},pool=2.7,item=item.name,simulation_for=context.evidence)
        assert proposal.rune=='Fo'
        assert proposal.estimates['local_simulation']['kind']=='local_dofocus_model'
        assert proposal.estimates['dofocus'] is None
        assert proposal.estimates['source_comparison']['observations']==0
        assert 'modèle local' in proposal.explanation
        assert proposal.sample==0
    finally:worker.stop()


def test_virtual_loss_tests_affect_ranking_without_counting_as_real_trials():
    sample={'kind':'local_dofocus_model','blocked':False,'probabilities':{'SC':30,'SN':50,'EC':20},
        'display':{'SC':'30','SN':'50','EC':'20'},'real_observation':False}
    args=({'Force':20},{'Force':40},{'Force':40},5)
    baseline=candidates(*args,simulation_for=lambda rune:sample)
    risky={**sample,'outlook':{'trials':48,'mean_target_loss':5,'real_observations':0,'kind':'virtual_trials'}}
    adjusted=candidates(*args,simulation_for=lambda rune:risky)
    assert next(x[0] for x in adjusted if x[1]=='Fo')<next(x[0] for x in baseline if x[1]=='Fo')
    fused=combine_candidate_evidence(risky,None)
    assert fused['sources']==['modele_local_dofocus'] and fused['observations']==0


def test_local_cap_cannot_be_overridden_by_an_old_reference():
    recorded={'blocked':False,'display':{'SC':'30','SN':'50','EC':'20'}}
    with patch('forgely_decision.lookup_context',return_value={'Fo':recorded}):
        result=candidates({'Force':39},{'Force':40},{'Force':40},5,item='Anneau',
            simulation_for=lambda rune:{'kind':'local_dofocus_model','blocked':True})
    assert result==[]
