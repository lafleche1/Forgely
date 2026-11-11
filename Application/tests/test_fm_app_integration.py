from types import SimpleNamespace
from unittest.mock import patch
from forgely import Forgely


def app_state():
    return SimpleNamespace(observation_only=False,plan={'item':'Anneau','stats':{'Force':{'target':10}}},
        active_equipment_verified=True,item=SimpleNamespace(get=lambda:'Anneau'),
        live_jet={'Force':0},live_pool=30,live_after_fusion=False,
        live_laboratory=SimpleNamespace(estimate=lambda *args:None))


def test_live_app_reads_economic_mode_without_disabling_guards():
    with patch('forgely.read_settings',return_value={'strategy':'Budget optimisé','prices':{'Fo':1,'Pa Fo':100,'Ra Fo':10000},'budget_kamas':0}), \
         patch('forgely_decision.natural_profile',return_value={'Force':100}), \
         patch('forgely.natural_bounds',return_value={'Force':(0,100)}), \
         patch('forgely.complete_learning_profile',return_value={'Force':100}), \
         patch('forgely_data.stats_by_rune',return_value={}):
        proposal=Forgely.strategy_current(app_state())
    assert proposal.rune=='Ra Fo'
    assert proposal.estimates['objective']['mode']=='Chances maximales'
    assert 'remaining_budget' not in proposal.estimates['objective']


def test_budget_planner_is_available_without_forcing_a_budget_stop():
    from forgely_tools import settings_default
    assert callable(Forgely.open_budget)
    assert settings_default().get('stop_at_budget',False) is False
