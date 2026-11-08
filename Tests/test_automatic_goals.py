from unittest.mock import Mock, patch
import os
import pytest
from forgely import Forgely
from forgely_equipment_catalog import EquipmentCatalog
from forgely_plan import save_plan, load_plan


def automatic_app():
    app=Mock()
    app.equipment_mode.get.return_value='automatic'
    app.equipment_picker=None
    app.manual_equipment=None
    app.active_equipment_verified=True
    app.item.get.return_value='ANNEAU DU CYCLOÏDE'
    app.theme_name='Obsidienne'
    app.running=True
    return app


def test_auto_goal_editor_opens_on_detected_item_and_locks_equipment():
    app=automatic_app()
    with patch('forgely_equipment_picker.EquipmentPicker') as picker:
        Forgely.open_equipment_picker(app,goals_only=True)
    args=picker.call_args
    args.args[2]('equipment','values',False)
    app.commit_automatic_goals.assert_called_once_with('equipment','values',False,
        detected_name='ANNEAU DU CYCLOÏDE')
    assert args.kwargs['goals_only'] is True
    assert args.kwargs['lock_equipment'] is True
    assert EquipmentCatalog().get(args.kwargs['selected_id']).name.casefold()=='anneau du cycloïde'


def test_auto_goal_editor_waits_for_confirmed_identity():
    app=automatic_app();app.active_equipment_verified=False
    with patch('forgely_equipment_picker.EquipmentPicker') as picker, \
         patch('forgely.messagebox.showinfo'):
        Forgely.open_equipment_picker(app,goals_only=True)
    picker.assert_not_called()


def test_auto_goals_save_without_stopping_capture_or_changing_identity(tmp_path):
    app=automatic_app()
    app.live_jet={'Force':37};app.live_pool=2.7
    context=app._verified_item_context
    equipment=EquipmentCatalog().search('Anneau','cycloide')[0]
    path=tmp_path/'goals.json'
    with patch('forgely.save_plan',side_effect=lambda item, values, **kw:save_plan(item,values,path,**kw)):
        Forgely.commit_automatic_goals(app,equipment,{'Force':(None,40)},True)
    assert load_plan(path)['item']=='ANNEAU DU CYCLOÏDE'
    assert app.plan['stats']['Force']['target']==40
    assert app.live_jet=={'Force':37} and app.live_pool==2.7
    assert app._verified_item_context is context
    assert app.manual_equipment is None
    app.equipment_mode.set.assert_not_called()
    app.toggle_observer.assert_not_called()
    assert app.running is True


@pytest.mark.parametrize('changed', ['identity','mode','unconfirmed'])
def test_stale_automatic_goal_editor_cannot_save_for_another_context(changed):
    app=automatic_app()
    if changed=='identity':app.item.get.return_value='Gelano'
    if changed=='mode':app.equipment_mode.get.return_value='manual'
    if changed=='unconfirmed':app.active_equipment_verified=False
    equipment=EquipmentCatalog().search('Anneau','cycloide')[0]
    with patch('forgely.save_plan') as save, pytest.raises(ValueError):
        Forgely.commit_automatic_goals(app,equipment,{'Force':(None,40)})
    save.assert_not_called()


def test_confirmed_editor_can_save_targets_while_its_window_masks_dofus(tmp_path):
    app=automatic_app();app.active_equipment_verified=False
    equipment=EquipmentCatalog().search('Anneau','cycloide')[0]
    path=tmp_path/'goals.json'
    with patch('forgely.save_plan',side_effect=lambda item, values, **kw:save_plan(item,values,path,**kw)):
        Forgely.commit_automatic_goals(app,equipment,{'Force':(None,40)},
            detected_name='ANNEAU DU CYCLOÏDE')
    assert load_plan(path)['stats']['Force']['target']==40
    assert app.active_equipment_verified is False
    app.toggle_observer.assert_not_called()


@pytest.mark.skipif(os.environ.get('FORGELY_GUI_TESTS')!='1',reason='requires a desktop')
def test_native_automatic_editor_saves_targets_and_keeps_mode(tmp_path):
    # Tk's native handles cannot safely share successive root lifetimes with
    # the other desktop suites. Exercise this complete app in its own process.
    if os.environ.get('FORGELY_AUTO_GOALS_GUI_CHILD')!='1':
        import subprocess
        import sys
        from pathlib import Path
        env=dict(os.environ,FORGELY_AUTO_GOALS_GUI_CHILD='1')
        result=subprocess.run([sys.executable,'-m','pytest',
            str(Path(__file__).resolve())+'::test_native_automatic_editor_saves_targets_and_keeps_mode',
            '-q','--tb=short'],env=env,capture_output=True,text=True,timeout=45)
        assert result.returncode==0,result.stdout+result.stderr
        return
    from forgely import physical_pixels
    physical_pixels()
    path=tmp_path/'automatic-goals.json'
    with patch('forgely.load_plan',return_value=None):
        app=Forgely()
    try:
        app.auto_floating.set(False)
        app.set_equipment_mode('automatic')
        app.item.set('ANNEAU DU CYCLOÏDE')
        app.active_equipment_verified=True
        app.open_plan_editor()
        app.update()
        picker=app.equipment_picker
        assert picker.stage=='goals' and picker.lock_equipment
        picker.show_catalogue()
        assert picker.stage=='goals'
        picker.fill_maximum()
        with patch('forgely.save_plan',side_effect=lambda item, values, **kw:save_plan(item,values,path,**kw)):
            picker.commit(False)
        assert not picker.winfo_exists()
        assert app.equipment_mode.get()=='automatic'
        assert app.manual_equipment is None
        assert app.active_equipment_verified
        assert load_plan(path)['stats']['Force']['target']==40
    finally:
        app.close()
