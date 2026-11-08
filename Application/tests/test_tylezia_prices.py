import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import forgely_tools as tools
from forgely_data import RUNES
from forgely_decision import advise


def activate(path):
    return tools.activate_tylezia_reference(path)


def test_fresh_install_has_all_screenshot_prices_and_economic_advice(tmp_path):
    cfg = activate(tmp_path / 'preferences.json')
    assert cfg['strategy'] == 'Budget optimisé'
    assert cfg['price_server'] == 'Tylezia'
    assert cfg['price_reference_date'] == '2026-11-08'
    assert len(cfg['prices']) == 105
    assert set(cfg['prices']) == set(RUNES)
    assert {k: cfg['prices'][k] for k in ('Age', 'Cha', 'Ga Pa', 'Ga Pme', 'Ra Vi', 'de chasse')} == {
        'Age': 74, 'Cha': 34, 'Ga Pa': 31053, 'Ga Pme': 23106, 'Ra Vi': 2368, 'de chasse': 6797}
    proposal = advise({'Force': 0}, {'Force': 10}, natural_max={'Force': 100}, pool=30,
                      mode=cfg['strategy'], prices=cfg['prices'])
    assert proposal.rune is not None
    assert proposal.estimates['objective']['mode'] == 'Budget optimisé'
    assert all(row['price'] is not None for row in proposal.estimates['objective']['alternatives'])
    prices = dict(cfg['prices'], Fo=1, **{'Pa Fo': 10000, 'Ra Fo': 10000})
    assert advise({'Force': 0}, {'Force': 10}, natural_max={'Force': 100}, pool=30,
                  mode=cfg['strategy'], prices=prices).rune == 'Fo'


def test_existing_preferences_backed_up_and_exact_reference_installed(tmp_path):
    path = tmp_path / 'preferences.json'
    old = {'strategy': 'Chances maximales', 'budget_kamas': 90000, 'prices': {'Fo': 999}}
    original = json.dumps(old)
    path.write_text(original)
    cfg = activate(path)
    assert cfg['prices']['Fo'] == 36
    assert cfg['budget_kamas'] == 90000
    assert cfg['strategy'] == 'Budget optimisé'
    assert path.with_suffix('.avant-tylezia-2026-11-08.json').read_text() == original


def test_restart_preserves_user_edits_mode_and_reference_metadata(tmp_path):
    path = tmp_path / 'preferences.json'
    cfg = activate(path)
    cfg['prices']['Fo'] = 123
    cfg['strategy'] = 'Chances maximales'
    tools.save_settings(cfg, path)
    assert activate(path)['prices']['Fo'] == 123
    assert activate(path)['strategy'] == 'Chances maximales'
    assert tools.read_settings(path)['price_server'] == 'Tylezia'
    assert not path.with_suffix('.avant-tylezia-2026-11-08.json').exists()


def test_corrupt_preferences_retained_in_backup(tmp_path):
    path = tmp_path / 'preferences.json'
    path.write_text('{broken', encoding='utf8')
    assert activate(path)['prices']['Vi'] == 248
    assert path.with_suffix('.avant-tylezia-2026-11-08.json').read_text() == '{broken'


def test_application_copilot_uses_activated_reference(tmp_path):
    from forgely import Forgely
    path = tmp_path / 'preferences.json'
    activate(path)
    from forgely_equipment_catalog import EquipmentCatalog,equipment_bounds
    item=EquipmentCatalog().get(14092)
    bounds=equipment_bounds(item)
    jet={stat:max(pair) for stat,pair in bounds.items()};jet['Force']=0
    app = SimpleNamespace(observation_only=False,
        plan={'item':item.identity_name,'stats':{'Force':{'target':10}}},
        active_equipment_verified=True,item=SimpleNamespace(get=lambda:item.identity_name),
        live_jet=jet,live_pool=30,live_after_fusion=False,
        live_laboratory=SimpleNamespace(estimate=lambda *a:None))
    with patch('forgely.read_settings',side_effect=lambda:tools.read_settings(path)), \
         patch('forgely_data.stats_by_rune',return_value={}):
        proposal=Forgely.strategy_current(app)
    assert proposal.rune in ('Fo', 'Pa Fo', 'Ra Fo')
    assert proposal.estimates['objective']['mode'] == 'Budget optimisé'
    assert str(tools.read_settings(path)['prices'][proposal.rune]) in proposal.explanation
