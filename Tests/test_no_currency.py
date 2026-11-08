import json
from copy import deepcopy

from forgely_decision import advise, candidates
from forgely_rl import ForgemagingEnv
from forgely_training import TrainingConfig, run_training
from forgely_tools import read_settings, save_settings


def test_incomplete_prices_and_budget_do_not_block_advice():
    args=({'Force':20},{'Force':40},{'Force':40},0)
    baseline=candidates(*args)
    assert baseline
    for prices,budget in (({},0),({'Fo':10**12},1),({'Fo':float('nan')},-1)):
        assert candidates(*args,mode='Budget optimisé',prices=prices,remaining_budget=budget)==baseline
        proposal=advise(*args,mode='Budget optimisé',prices=prices,remaining_budget=budget)
        assert proposal.rune==baseline[0][1]
        assert 'remaining_budget' not in proposal.estimates['objective']


def test_rl_legacy_money_inputs_do_not_change_state_actions_or_transition():
    args=([{'stat':'Force','value':19,'min':0,'max':40,'weight':1}],0,{'Force':40})
    plain=ForgemagingEnv(*deepcopy(args),seed=3)
    legacy=ForgemagingEnv(*deepcopy(args),seed=3,prices={'Fo':1000000},budget=0)
    assert plain.get_state()==legacy.get_state()
    assert plain.get_valid_actions()==legacy.get_valid_actions()
    assert plain.step('Fo')==legacy.step('Fo')
    state=legacy.get_state()
    assert not {'budget','prices'} & state.keys()
    assert not any('budget' in field for field in state['features'])


def test_economic_settings_preserve_prices_on_read_and_save(tmp_path):
    path=tmp_path/'settings.json'
    path.write_text(json.dumps({'strategy':'Budget optimisé','prices':{'Fo':1000},'budget_kamas':1}))
    assert read_settings(path)=={'strategy':'Budget optimisé','prices':{'Fo':1000},'budget_kamas':1}
    save_settings({'strategy':'Budget optimisé','prices':{'Fo':1000},'budget_kamas':1},path)
    assert json.loads(path.read_text(encoding='utf8'))=={'strategy':'Budget optimisé','prices':{'Fo':1000},'budget_kamas':1}


def test_new_training_ignores_legacy_money_and_saves_no_currency(tmp_path):
    config=TrainingConfig(item_id=14092,targets={'Force':40},episodes=2,max_steps=8,
                          evaluation_episodes=2,prices={'Fo':1000000},budget=0)
    result=run_training(config,tmp_path)
    assert result['training_runes']
    assert result['evaluation']['learned']['stops']==0
    assert not {'prices','budget'} & result['configuration'].keys()
    assert 'prices_provided' not in result
    assert 'mean_cost' not in result['evaluation']['learned']
    report=(tmp_path/result['run_id']/'rapport.html').read_text(encoding='utf8').casefold()
    assert not any(word in report for word in ('prix','budget','kamas','coût'))


def test_illustrative_simulators_ignore_legacy_price_and_return_no_cost():
    from forgely_simulateur import simulate_target
    from forgely_tools import illustrative_scenario
    args=('Vi',0,10,20)
    assert simulate_target(*args,0,.3,.3,.4,trials=10)==simulate_target(*args,-999,.3,.3,.4,trials=10)
    result=illustrative_scenario('Vi',10,-999,.3,.3,.4)
    assert 'cost_kamas' not in result
    assert result==illustrative_scenario('Vi',10,10**12,.3,.3,.4)
