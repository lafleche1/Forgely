from PIL import Image,ImageDraw
import pytest


def icon(color):
    im=Image.new('RGB',(32,32),'#38394e')
    ImageDraw.Draw(im).ellipse((4,4,27,27),fill=color)
    return im


def test_observed_jet_and_target_can_produce_advice_without_item_name():
    from forgely_measured_goals import MeasuredGoals
    goals=MeasuredGoals();goals.observe_slot(icon('red'),(),('account',1))
    goals.save({'Vitalité':300},{'Vitalité':297},goals.revision)
    proposal=goals.proposal(({'Vitalité':297},.9))
    assert proposal.rune is not None
    assert goals.proposal(None).rune is None


@pytest.mark.parametrize('mode',['Jet propre','Jet parfait','Exo PA','Exo PM','Exo PO'])
def test_real_copilot_mode_with_saved_350_vitality_target_produces_advice(mode):
    from forgely_measured_goals import MeasuredGoals
    jet={'Vitalité':297,'Force':38,'Intelligence':38,'Agilité':39,
         'Dommages Neutre':7,'Dommages Terre':7,'Dommages Feu':0,
         'Dommages Air':1,'Initiative':142,'% Résistance Eau':2,'Tacle':0}
    goals=MeasuredGoals();goals.observe_slot(icon('red'),(),('account',1))
    goals.save({**jet,'Vitalité':350},jet,goals.revision)
    assert goals.proposal((jet,.9),mode=mode).rune is not None


def test_refresh_replaces_define_target_message_with_real_advice():
    from unittest.mock import Mock
    from time import perf_counter_ns
    from forgely import Forgely,LatestFrameMailbox
    from forgely_continuous_identity import SlotEvidence
    from forgely_measured_goals import MeasuredGoals
    from forgely_workshop_readings import WorkshopReadings
    app=Mock();app.observation_only=False;app.plan=None
    app.active_equipment_verified=False;app.workshop_active=True;app.running=True
    app.live_jet=None;app.live_pool=None;app.live_after_fusion=True
    app.goal_mode.get.return_value='Jet propre'
    mailbox=LatestFrameMailbox();app.frame_mailbox=mailbox;app.last_capture_title='DOFUS'
    app.measured_goals=MeasuredGoals()
    app.measured_goals.observe_slot(icon('red'),(),(mailbox,'DOFUS'))
    app.measured_goals.save({'Vitalité':350},{'Vitalité':297},app.measured_goals.revision)
    app.workshop_readings=WorkshopReadings()
    for i in range(3):app.workshop_readings.observe({'Vitalité':297},.9,sequence=i)
    app.fast_slot_evidence=SlotEvidence((mailbox,mailbox.generation(),'DOFUS'),icon('red'),3,perf_counter_ns())
    app.strategy_current.side_effect=lambda:Forgely.strategy_current(app)
    app.waiting_for_item_label.side_effect=lambda:Forgely.waiting_for_item_label(app)
    Forgely.refresh_strategy(app)
    assert app.current_proposal.rune is not None
    text=app.overlay.show_advice.call_args.args[0]
    assert isinstance(text,str) and text not in ('Définir le jet souhaité','STOP')


def test_changed_slot_clears_targets_and_rejects_open_editor_save():
    from forgely_measured_goals import MeasuredGoals
    goals=MeasuredGoals();goals.observe_slot(icon('red'),(),('account',1))
    rev=goals.revision;goals.save({'Vitalité':300},{'Vitalité':297},rev)
    goals.observe_slot(None,(),('account',1))
    assert goals.targets  # A focus pause is not a replaced item.
    goals.observe_slot(icon('blue'),(),('account',1))
    assert not goals.targets
    with pytest.raises(ValueError):goals.save({'Vitalité':300},{'Vitalité':297},rev)


def test_application_strategy_and_card_use_slot_goal_without_verified_name():
    from types import SimpleNamespace
    from unittest.mock import Mock
    from forgely import Forgely
    from forgely_measured_goals import MeasuredGoals,current_snapshot
    from forgely_workshop_readings import WorkshopReadings
    from forgely_dashboard import current_card
    from forgely import LatestFrameMailbox
    from forgely_continuous_identity import SlotEvidence
    from time import perf_counter_ns
    mailbox=LatestFrameMailbox();goals=MeasuredGoals()
    goals.observe_slot(icon('red'),(),(mailbox,'DOFUS'))
    goals.save({'Vitalité':300},{'Vitalité':297},goals.revision)
    readings=WorkshopReadings()
    for i in range(3):readings.observe({'Vitalité':297},.9,sequence=i)
    app=SimpleNamespace(observation_only=False,measured_goals=goals,
        workshop_active=True,frame_mailbox=mailbox,last_capture_title='DOFUS',
        workshop_readings=readings,equipment_mode=Mock(),item=Mock(),
        active_equipment_verified=False,manual_equipment=None,plan=None)
    app.fast_slot_evidence=SlotEvidence((mailbox,mailbox.generation(),'DOFUS'),icon('red'),3,perf_counter_ns())
    app.equipment_mode.get.return_value='automatic';app.item.get.return_value=''
    assert Forgely.strategy_current(app).rune
    assert current_card(app)['targets']=={'Vitalité':300}
    assert current_card(app)['title']=='Objet de l’atelier'
    previous=app.fast_slot_evidence
    app.fast_slot_evidence=None
    assert current_snapshot(app) is None
    assert Forgely.strategy_current(app).rune is None
    app.fast_slot_evidence=previous
    app.last_capture_title='AUTRE COMPTE'
    assert current_snapshot(app) is None
    assert Forgely.strategy_current(app).rune is None


def test_inline_target_editor_saves_values_without_equipment_picker():
    import tkinter as tk
    from forgely_overlay import FloatingBadge
    try:root=tk.Tk()
    except tk.TclError:pytest.skip('Tk display unavailable')
    root.withdraw();overlay=None
    try:
        overlay=FloatingBadge(root,lambda:None,lambda:None,lambda:None)
        overlay.withdraw();saved=[]
        overlay.open_targets({'Vitalité':297},{'Intelligence':40},saved.append)
        overlay.goal_panel.fields['Vitalité'].set('300')
        overlay.sync_review(100)
        assert overlay.goal_editing and overlay.goal_panel.winfo_manager()=='place'
        root.deiconify();overlay.deiconify();root.update()
        button=overlay.goal_panel.save_button
        assert button.winfo_ismapped()
        assert button.winfo_rooty()+button.winfo_height() <= overlay.goal_panel.winfo_rooty()+overlay.goal_panel.winfo_height()
        actions=overlay.goal_panel.winfo_children()[-1]
        actions.winfo_children()[0].invoke()
        assert saved==[{'Vitalité':300,'Intelligence':40}]
        assert overlay.goal_panel.winfo_toplevel() is overlay
        overlay.close_targets()
        assert not overlay.goal_editing
    finally:
        if overlay is not None:overlay.destroy()
        root.destroy()


def test_long_target_list_keeps_checkbox_and_validation_inside_panel():
    import tkinter as tk
    from forgely_overlay import FloatingBadge
    from forgely_rules import RUNE_CHOICES
    try:root=tk.Tk()
    except tk.TclError:pytest.skip('Tk display unavailable')
    root.perfect_goal_checked=tk.BooleanVar(value=False);overlay=None
    try:
        overlay=FloatingBadge(root,lambda:None,lambda:None,lambda:None)
        rows=dict.fromkeys(list(RUNE_CHOICES)[:18],1)
        overlay.open_targets(rows,{},lambda _:None,on_perfect=lambda:None)
        root.update()
        panel=overlay.goal_panel;button=panel.save_button
        assert button.winfo_ismapped()
        assert button.winfo_rooty()+button.winfo_height()<=panel.winfo_rooty()+panel.winfo_height()
        panel.fill_targets({'Vitalité':300,'Intelligence':40})
        assert panel.fields['Intelligence'].get()=='40'
    finally:
        if overlay is not None:overlay.destroy()
        root.destroy()


def test_save_resumes_only_the_selected_game_window():
    from unittest.mock import Mock,patch
    from forgely import Forgely
    app=Mock();app.capture.last_handle=12345
    with patch('forgely_windows.activate_game_window') as activate:
        Forgely.resume_game_after_targets(app)
        activate.assert_called_once_with(12345)


def test_rune_rereads_values_without_losing_slot_goal_or_reidentifying():
    from types import SimpleNamespace
    from unittest.mock import Mock
    from time import perf_counter_ns
    from forgely import Forgely,LatestFrameMailbox
    from forgely_measured_goals import MeasuredGoals
    from forgely_continuous_identity import SlotEvidence
    from forgely_workshop_readings import WorkshopReadings
    from forgely_dashboard import current_card
    mailbox=LatestFrameMailbox();goals=MeasuredGoals();readings=WorkshopReadings()
    artwork=icon('red');goals.observe_slot(artwork,(),(mailbox,'DOFUS'))
    goals.save({'Intelligence':40},{'Intelligence':38},goals.revision)
    for i in range(3):readings.observe({'Intelligence':38},.9,sequence=i)
    app=SimpleNamespace(measured_goals=goals,workshop_readings=readings,
        frame_mailbox=mailbox,last_capture_title='DOFUS',workshop_active=True,
        running=True,observation_only=False,active_equipment_verified=False,
        last_item_candidate='',provisional_slot_id=1,current_slot_tracker=SimpleNamespace(count=3),
        manual_equipment=None,equipment_mode=Mock(),item=Mock(),plan=None,
        fast_slot_evidence=SlotEvidence((mailbox,mailbox.generation(),'DOFUS'),artwork,4,perf_counter_ns()))
    app.equipment_mode.get.return_value='automatic';app.item.get.return_value=''
    readings.invalidate()  # Same path as the auto_event handler after a rune.
    assert Forgely.waiting_for_item_label(app)=='Actualisation du jet'
    assert current_card(app)['title']=='Objet de l’atelier'
    assert current_card(app)['targets']=={'Intelligence':40}
    assert readings.display_jet=={'Intelligence':38}
    assert readings.line_states['Intelligence']=='stale'
    assert Forgely.strategy_current(app).rune is None
    for i in range(3,6):readings.observe({'Intelligence':37},.9,sequence=i)
    assert Forgely.waiting_for_item_label(app) is None
    assert goals.targets=={'Intelligence':40}
    assert readings.display_jet=={'Intelligence':37}
    assert Forgely.strategy_current(app).rune is not None


def test_changed_jet_requests_fresh_captures_until_stable():
    import queue,threading
    from unittest.mock import Mock
    from forgely import Forgely
    from forgely_workshop_readings import WorkshopReadings
    app=Mock();app.messages=queue.Queue();app.workshop_readings=WorkshopReadings()
    app.active_equipment_verified=False;app.measured_goals=None
    app.confirmation_requested=threading.Event();app.winfo_exists.return_value=False
    for i in range(3):
        app.confirmation_requested.clear()
        app.messages.put(('atelier_read',({'Intelligence':37},.9)))
        Forgely.process_messages(app)
        assert app.confirmation_requested.is_set()==(i<2)
