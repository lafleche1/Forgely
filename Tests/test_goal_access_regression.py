from types import SimpleNamespace
from unittest.mock import Mock
from PIL import Image,ImageDraw


def isolated_gui(name):
    import os,sys,subprocess
    from pathlib import Path
    if os.environ.get('FORGELY_GOAL_REGRESSION_CHILD')==name:return False
    result=subprocess.run([sys.executable,'-B','-m','pytest',str(Path(__file__).resolve())+'::'+name,'-q','--tb=short'],
        env=dict(os.environ,FORGELY_GOAL_REGRESSION_CHILD=name),capture_output=True,text=True,timeout=60)
    assert result.returncode==0,result.stdout+result.stderr
    return True


def partial_app():
    from forgely import LatestFrameMailbox
    from forgely_measured_goals import MeasuredGoals
    from forgely_workshop_readings import WorkshopReadings
    mailbox=LatestFrameMailbox();session=MeasuredGoals()
    icon=Image.new('RGB',(32,32),'#38394e');ImageDraw.Draw(icon).ellipse((4,4,26,28),fill='red')
    session.observe_slot(icon,(),(mailbox,'DOFUS'))
    readings=WorkshopReadings();readings.configure('item',{'Force':40,'Vitalité':300})
    for i in range(3):readings.observe({'Force':38},1.3,sequence=i)
    return SimpleNamespace(frame_mailbox=mailbox,measured_goals=session,workshop_readings=readings,
        last_capture_title='DOFUS',workshop_active=True,active_equipment_verified=False,
        observation_only=False,plan=None,overlay=SimpleNamespace(goal_editing=False),
        after=Mock(),prompt_measured_goals=Mock(),fast_slot_evidence=None)


def test_partial_reading_can_prompt_targets_without_authorizing_advice():
    from forgely_measured_goals import goal_editor_jet,maybe_prompt_goals,current_snapshot
    app=partial_app()
    assert current_snapshot(app) is None
    assert goal_editor_jet(app)=={'Force':38}
    assert maybe_prompt_goals(app)
    assert not maybe_prompt_goals(app)
    app.after.call_args.args[1]()
    app.prompt_measured_goals.assert_called_once()
    assert app.workshop_readings.snapshot() is None


def test_wrong_account_or_only_stale_values_cannot_supply_editor_values():
    from forgely_measured_goals import goal_editor_jet
    app=partial_app();app.last_capture_title='OTHER'
    assert goal_editor_jet(app) is None
    app.last_capture_title='DOFUS';app.workshop_readings.invalidate()
    assert goal_editor_jet(app) is None


def test_real_form_opens_saves_and_displays_targets_with_incomplete_ocr():
    if isolated_gui('test_real_form_opens_saves_and_displays_targets_with_incomplete_ocr'):return
    import tkinter as tk
    from forgely import Forgely
    from forgely_overlay import FloatingBadge
    from forgely_dashboard import current_card
    root=tk.Tk();root.withdraw();root.perfect_goal_checked=tk.BooleanVar(root,value=False)
    app=partial_app();app.perfect_goal_checked=root.perfect_goal_checked
    app.goal_mode=tk.StringVar(root,value='');app.item=tk.StringVar(root,value='')
    app.equipment_mode=tk.StringVar(root,value='automatic');app.status=tk.StringVar(root)
    app.render_plan=Mock();app.refresh_strategy=Mock();app.resume_game_after_targets=Mock()
    app.overlay=FloatingBadge(root,lambda:None,lambda:None,lambda:None,
                              on_goals=lambda:Forgely.prompt_measured_goals(app))
    try:
        assert {'Atelier','Observer','Jet cible','Détails'} <= {b.cget('text') for b in app.overlay.action_buttons}
        button=next(b for b in app.overlay.action_buttons if b.cget('text')=='Jet cible')
        from forgely_measured_goals import maybe_prompt_goals
        app.prompt_measured_goals=lambda:Forgely.prompt_measured_goals(app)
        assert maybe_prompt_goals(app)
        app.after.call_args.args[1]();root.update_idletasks()
        assert app.overlay.goal_editing
        panel=app.overlay.goal_panel
        panel.fields['Force'].set('40')
        app.observation_only=True
        from unittest.mock import patch
        with patch('forgely_observation_mode.save_observation_mode') as persist:
            panel.save_button.invoke()
        assert app.observation_only is False
        persist.assert_called_once()
        assert app.measured_goals.targets=={'Force':40}
        assert not app.overlay.goal_editing
        assert current_card(app)['targets']=={'Force':40}
        assert app.workshop_readings.snapshot() is None
        button.invoke();root.update_idletasks()
        assert app.overlay.goal_editing
        assert app.overlay.goal_panel.fields['Force'].get()=='40'
    finally:
        app.overlay.destroy();root.destroy()


def test_perfect_goal_uses_current_slot_even_if_automatic_identity_is_still_pending():
    if isolated_gui('test_perfect_goal_uses_current_slot_even_if_automatic_identity_is_still_pending'):return
    import tkinter as tk
    from pathlib import Path
    from forgely import Forgely
    from forgely_overlay import FloatingBadge
    from forgely_workshop_layout import WorkshopLocator
    from forgely_continuous_identity import current_icon
    app=partial_app()
    image=WorkshopLocator().normalize(Image.open(Path(__file__).parent/'fixtures/history_unity_20261109/162925.png'),'real')
    app.frame_mailbox.publish(image,'DOFUS',1,0)
    app.measured_goals.observe_slot(current_icon(image),(),(app.frame_mailbox,'DOFUS'))
    root=tk.Tk();root.withdraw();root.perfect_goal_checked=tk.BooleanVar(root,value=False)
    app.perfect_goal_checked=root.perfect_goal_checked;app.goal_mode=tk.StringVar(root,value='')
    app.item=tk.StringVar(root,value='');app.status=tk.StringVar(root)
    app.equipment_mode=tk.StringVar(root,value='automatic')
    app.render_plan=Mock();app.refresh_strategy=Mock();app.resume_game_after_targets=Mock()
    app.overlay=FloatingBadge(root,lambda:None,lambda:None,lambda:None)
    try:
        Forgely.prompt_measured_goals(app);root.update_idletasks()
        panel=app.overlay.goal_panel
        next(w for w in panel.winfo_children() if isinstance(w,tk.Checkbutton)).invoke()
        assert panel.fields['Vitalité'].get()=='300'
        assert panel.fields['Force'].get()=='40'
        assert panel.fields['Dommages Neutre'].get()=='10'
        assert panel.error.cget('text')==''
        panel.save_button.invoke()
        assert app.measured_goals.targets['Vitalité']==300
        assert app.measured_goals.targets['Force']==40
        assert app.goal_mode.get()=='Jet parfait'
        assert app.workshop_readings.snapshot() is None
        from forgely_equipment_catalog import equipment_bounds
        maxima={k:max(v) for k,v in equipment_bounds(app.measured_goals.equipment).items()}
        proposal=app.measured_goals.proposal(({**maxima,'Force':38},1.3),mode='Jet parfait')
        assert proposal.rune is not None
        assert proposal.estimates['prediction'] is not None
    finally:
        app.overlay.destroy();root.destroy()
