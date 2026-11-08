from unittest.mock import Mock, patch
import pytest
from forgely import Forgely
from forgely_continuous_identity import CurrentSlotTracker


def app_for_mode(mode):
    app=Mock()
    app.equipment_mode.get.return_value=mode
    app.running=False
    app.manual_equipment=None
    app.equipment_picker=None
    app.auto_floating.get.return_value=False
    return app


def test_automatic_observation_starts_without_manual_item_or_goal():
    app=app_for_mode('automatic')
    app.plan=None
    with patch('forgely.threading.Thread'):
        Forgely.toggle_observer(app)
    assert app.running is True
    app.open_equipment_picker.assert_not_called()
    assert app.item_selection_source=='none'


def test_switch_to_automatic_discards_manual_identity_and_live_evidence():
    app=app_for_mode('manual')
    app.manual_equipment=object()
    app.live_jet={'Force':40}
    app.live_pool=2.7
    Forgely.set_equipment_mode(app,'automatic')
    assert app.manual_equipment is None
    assert app.active_equipment_verified is False
    assert app._verified_item_context is None
    assert app.live_jet is None and app.live_pool is None
    assert isinstance(app.current_slot_tracker,CurrentSlotTracker)
    app.equipment_mode.set.assert_called_with('automatic')


def test_changing_mode_stops_running_capture_before_resetting():
    app=app_for_mode('automatic')
    app.running=True
    Forgely.set_equipment_mode(app,'manual')
    app.toggle_observer.assert_called_once()
    assert app.active_equipment_verified is False


def test_invalid_mode_does_not_change_session():
    app=app_for_mode('manual')
    with pytest.raises(ValueError):
        Forgely.set_equipment_mode(app,'invalid')
    app.equipment_mode.set.assert_not_called()


def test_manual_mode_requires_an_explicit_item_and_target():
    app=app_for_mode('manual')
    app.plan=None
    with patch('forgely.threading.Thread'):
        Forgely.toggle_observer(app)
    assert app.running is False
    app.open_equipment_quick.assert_called_once()


def test_manual_mode_starts_with_selected_item_and_target():
    from forgely_equipment_catalog import EquipmentCatalog
    from forgely_equipment_session import ManualEquipmentSession
    app=app_for_mode('manual')
    app.auto_floating.get.return_value=True
    equipment=EquipmentCatalog().search('Anneau','cycloide')[0]
    app.manual_equipment=ManualEquipmentSession(equipment)
    app.plan={'item':equipment.name,'stats':{'Force':{'target':40}}}
    with patch('forgely.threading.Thread'):
        Forgely.toggle_observer(app)
    assert app.running is True
    assert app.item_selection_source=='manual'
    app.after.assert_any_call(250,app.resume_game_after_targets)
    app.open_equipment_quick.assert_not_called()
