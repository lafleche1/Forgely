from unittest.mock import Mock, patch

import pytest
from PIL import Image

from forgely import Forgely
from forgely_equipment_catalog import EquipmentCatalog
from forgely_measured_goals import MeasuredGoals
from forgely_plan import save_plan, load_plan


def app_with_session():
    app = Mock()
    item = EquipmentCatalog().search('Anneau', 'cycloide')[0]
    app.item.get.return_value = item.identity_name
    app.equipment_mode.get.return_value = 'automatic'
    app.active_equipment_verified = True
    app.running = True
    app.measured_goals = MeasuredGoals()
    app.measured_goals.observe_slot(Image.effect_noise((32, 32), 50).convert('RGB'), (), ('mailbox', 'DOFUS'))
    app.measured_goals.equipment = item
    app.measured_goals.targets = {'Dommages Neutre': 10, 'Force': 40}
    app.plan = {'item': item.identity_name, 'stats': {'Dommages Neutre': {'target': 10}}}
    return app, item


def test_catalogue_editor_replaces_live_targets_including_zero_and_removed_lines(tmp_path):
    app, item = app_with_session()
    path = tmp_path / 'goals.json'
    with patch('forgely.save_plan', side_effect=lambda name, values, **kw: save_plan(name, values, path, **kw)):
        Forgely.commit_automatic_goals(app, item, {'Dommages Neutre': (None, 0)})
    assert app.measured_goals.targets == {'Dommages Neutre': 0}
    assert load_plan(path)['stats'] == {'Dommages Neutre': {'current': None, 'target': 0}}


def test_live_editor_persists_targets_for_reopening_catalogue_editor(tmp_path):
    app, item = app_with_session()
    path = tmp_path / 'goals.json'
    session = app.measured_goals
    with patch('forgely.save_plan', side_effect=lambda name, values, **kw: save_plan(name, values, path, **kw)):
        Forgely.commit_measured_goals(app, {'Dommages Neutre': 0},
                                     {'Dommages Neutre': 4}, session.revision)
    assert session.targets == {'Dommages Neutre': 0}
    assert app.plan == load_plan(path)
    assert app.plan['item'] == item.identity_name
    assert app.plan['stats']['Dommages Neutre']['target'] == 0


def test_failed_persistence_preserves_previous_session_targets():
    app, _ = app_with_session()
    old = dict(app.measured_goals.targets)
    with patch('forgely.save_plan', side_effect=OSError('write failed')), pytest.raises(OSError):
        Forgely.commit_measured_goals(app, {'Dommages Neutre': 0},
                                     {'Dommages Neutre': 4}, app.measured_goals.revision)
    assert app.measured_goals.targets == old


def test_stale_editor_cannot_replace_targets_or_saved_plan():
    app, _ = app_with_session()
    revision = app.measured_goals.revision
    app.measured_goals.reset()
    with patch('forgely.save_plan') as persist, pytest.raises(ValueError):
        Forgely.commit_measured_goals(app, {'Dommages Neutre': 0},
                                     {'Dommages Neutre': 4}, revision)
    persist.assert_not_called()
    assert app.measured_goals.targets == {}


def test_anonymous_slot_targets_do_not_overwrite_another_named_plan():
    app, _ = app_with_session()
    app.active_equipment_verified = False
    app.measured_goals.equipment = None
    previous = app.plan
    with patch('forgely.save_plan') as persist:
        Forgely.commit_measured_goals(app, {'Dommages Neutre': 0},
                                     {'Dommages Neutre': 4}, app.measured_goals.revision)
    persist.assert_not_called()
    assert app.plan is previous
    assert app.measured_goals.targets == {'Dommages Neutre': 0}
