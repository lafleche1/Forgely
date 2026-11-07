from types import SimpleNamespace
from unittest.mock import patch
from forgely import Forgely


def app_state():
    return SimpleNamespace(observation_only=False, plan={'item': 'Anneau', 'stats': {'Force': {'target': 10}}},
                           active_equipment_verified=True, item=SimpleNamespace(get=lambda: 'Anneau'),
                           live_jet={'Force': 0}, live_pool=30, live_after_fusion=False,
                           budget_start_cursor=0, live_laboratory=SimpleNamespace(estimate=lambda *args: None))


def test_saved_economy_prices_drive_actual_app_advice():
    cfg = {'strategy': 'Budget optimisé', 'budget_kamas': 50, 'prices': {'Fo': 1, 'Pa Fo': 20, 'Ra Fo': 100}}
    with patch('forgely.read_settings', return_value=cfg), \
         patch('forgely.cost_since', return_value={'known_cost': 0, 'complete': True, 'unpriced_attempts': 0}), \
         patch('forgely.natural_bounds', return_value={'Force': (0, 100)}), \
         patch('forgely.stats', return_value=(0, {})):
        p = Forgely.strategy_current(app_state())
    assert p.rune == 'Fo'
    assert p.estimates['objective']['mode'] == 'Budget optimisé'
    assert p.estimates['objective']['remaining_budget'] == 50


def test_unpriced_consumption_blocks_limited_budget_advice():
    cfg = {'strategy': 'Chances maximales', 'budget_kamas': 50, 'prices': {'Fo': 1}}
    with patch('forgely.read_settings', return_value=cfg), \
         patch('forgely.cost_since', return_value={'known_cost': 0, 'complete': False, 'unpriced_attempts': 1}), \
         patch('forgely.natural_bounds', return_value={}), \
         patch('forgely.stats', return_value=(0, {})):
        p = Forgely.strategy_current(app_state())
    assert p.rune is None
    assert 'incomplet' in p.summary.lower()
