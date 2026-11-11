from unittest.mock import Mock, patch

from forgely import Forgely
from forgely_equipment_catalog import EquipmentCatalog


def test_manual_target_save_leaves_passive_observation():
    app=Mock()
    app.running=False
    app.observation_only=True
    equipment=EquipmentCatalog().search('Anneau','cycloide')[0]
    with patch('forgely.save_plan',return_value={'item':equipment.name}), \
         patch('forgely.register_item'), \
         patch('forgely_observation_mode.save_observation_mode') as persist:
        Forgely.commit_equipment_selection(app,equipment,{'Force':(38,40)})
    assert app.observation_only is False
    persist.assert_called_once()
    assert persist.call_args.args[1] is False
    app.update_mode_button.assert_called_once()
    assert app.live_jet is None
    assert app.active_equipment_verified is False


def test_automatic_target_save_also_activates_copilot():
    app=Mock();app.running=True;app.observation_only=True
    equipment=EquipmentCatalog().search('Anneau','cycloide')[0]
    app.equipment_mode.get.return_value='automatic'
    app.active_equipment_verified=True
    app.item.get.return_value=equipment.identity_name
    with patch('forgely.save_plan',return_value={'item':equipment.name}), \
         patch('forgely_observation_mode.save_observation_mode') as persist:
        Forgely.commit_automatic_goals(app,equipment,{'Force':(38,40)})
    assert app.observation_only is False
    persist.assert_called_once()

