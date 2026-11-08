import pytest
from types import SimpleNamespace
from unittest.mock import Mock,patch


def test_only_perfect_preset_is_exposed():
    from forgely_copilote import MODES
    assert MODES==('Jet parfait',)


def test_unchecking_perfect_preserves_the_target_values_for_manual_editing():
    from forgely import Forgely
    app=Mock();app.perfect_goal_checked.get.return_value=False
    app.plan={'stats':{'Vitalité':{'target':300}}}
    Forgely.toggle_perfect_goal(app)
    app.apply_perfect_goal.assert_not_called()
    assert app.plan['stats']['Vitalité']['target']==300
    app.goal_mode.set.assert_called_once_with('')


def test_inline_perfect_control_is_a_checkbox():
    import tkinter as tk
    from forgely_overlay import FloatingBadge
    try:root=tk.Tk()
    except tk.TclError:pytest.skip('Tk display unavailable')
    root.withdraw();overlay=None
    try:
        root.perfect_goal_checked=tk.BooleanVar(value=False)
        selected=[]
        overlay=FloatingBadge(root,lambda:None,lambda:None,lambda:None)
        overlay.withdraw()
        overlay.open_targets({'Vitalité':297},{},lambda _:None,
                             on_perfect=lambda:selected.append(root.perfect_goal_checked.get()))
        controls=[w for w in overlay.goal_panel.winfo_children() if isinstance(w,tk.Checkbutton)]
        assert len(controls)==1 and controls[0].cget('text')=='Jet parfait'
        controls[0].invoke();controls[0].invoke()
        assert selected==[True,False]
    finally:
        if overlay is not None:overlay.destroy()
        root.destroy()


def test_perfect_target_is_all_theoretical_maxima_not_the_observed_jet():
    from forgely_equipment_catalog import EquipmentCatalog,equipment_bounds
    from forgely_perfect_goal import perfect_goal
    from forgely_equipment_session import ManualEquipmentSession
    item=EquipmentCatalog().search('Anneau','cycloide')[0]
    app=SimpleNamespace(manual_equipment=ManualEquipmentSession(item),active_equipment_verified=False)
    name,ident,targets=perfect_goal(app)
    assert name==item.identity_name and ident==item.item_id
    assert targets=={k:max(v) for k,v in equipment_bounds(item).items()}
    assert targets['Vitalité']==300 and targets['Intelligence']==40 and targets['Dommages Feu']==10


def test_unknown_item_does_not_invent_perfect_values():
    from forgely_perfect_goal import perfect_goal
    with pytest.raises(ValueError):
        perfect_goal(SimpleNamespace(manual_equipment=None,active_equipment_verified=False))


def test_unique_natural_ranges_can_supply_perfect_targets_without_history_name():
    from forgely_perfect_goal import perfect_goal,signature_equipment
    from forgely_measured_goals import MeasuredGoals
    session=MeasuredGoals()
    session.signature=(('vitalite',251,300),('force',31,40),('intelligence',31,40),
                       ('agilite',31,40),('initiative',201,300),('tacle',4,6))
    name,_,targets=perfect_goal(SimpleNamespace(manual_equipment=None,active_equipment_verified=False,measured_goals=session))
    assert name=='Anneau du Cycloïde' and targets['Vitalité']==300
    assert signature_equipment((('vitalite',251,300),)) is None


def test_maximum_fill_clears_exotic_targets_and_uses_best_negative_bound():
    from forgely_equipment_picker import EquipmentPicker
    app=Mock();app.bounds={'Vitalité':(251,300),'Tacle':(-4,-6)}
    app.fields={k:Mock() for k in ('Vitalité','Tacle','PA')}
    EquipmentPicker.fill_maximum(app)
    app.fields['PA'].set.assert_called_once_with('')
    assert app.fields['Vitalité'].set.call_args.args==('300',)
    assert app.fields['Tacle'].set.call_args.args==('-4',)


def test_perfect_goal_replaces_saved_custom_targets_including_unread_lines():
    from forgely import Forgely
    from forgely_equipment_catalog import EquipmentCatalog
    from forgely_equipment_session import ManualEquipmentSession
    app=Mock();app.manual_equipment=ManualEquipmentSession(EquipmentCatalog().search('Anneau','cycloide')[0])
    app.active_equipment_verified=False;app.live_jet={'Vitalité':297}
    app.workshop_readings.partial_jet={'Vitalité':297};app.measured_goals=None
    with patch('forgely.save_plan',return_value={'item':'Anneau du Cycloïde'}) as save:
        Forgely.apply_perfect_goal(app)
    values=save.call_args.args[1]
    assert values['Vitalité']==(297,300)
    assert values['Intelligence']==(None,40)
    app.goal_mode.set.assert_called_once_with('Jet parfait')
