"""The displayed copilot session survives occlusion; learning does not."""
import os
from pathlib import Path
import subprocess
import sys


def test_mask_keeps_identity_goal_and_advice_but_invalidates_learning(tmp_path):
    application=Path(__file__).resolve().parents[1]/'Application'
    script=r'''
from forgely import Forgely,LatestFrameMailbox
from PIL import Image,ImageDraw
from forgely_measured_goals import MeasuredGoals
from forgely_pipeline import VerifiedItemContext
from forgely_continuous_identity import SlotEvidence
from time import perf_counter_ns
import forgely_measured_goals
# The capture worker normally refreshes this evidence every 120 ms. This test
# does not start workers, so use a fixed freshness clock while driving messages.
capture_clock=perf_counter_ns()
forgely_measured_goals.perf_counter_ns=lambda:capture_clock
app=Forgely()
try:
    app.observation_only=False
    app.running=True
    app.item.set('ANNEAU DU CYCLOÏDE')
    app.active_equipment_verified=True
    app.workshop_active=True
    app.last_capture_title='DOFUS'
    app.frame_mailbox=LatestFrameMailbox()
    from forgely_history_delta import HistoryDeltaMonitor
    app.history_delta_monitor=HistoryDeltaMonitor()
    icon=Image.new('RGB',(32,32),'#38394e')
    ImageDraw.Draw(icon).ellipse((4,4,27,27),fill='red')
    for _ in range(3):app.current_slot_tracker.observe(icon)
    app.measured_goals=MeasuredGoals()
    app.measured_goals.observe_slot(icon,(),(app.frame_mailbox,'DOFUS'))
    app.measured_goals.save({'Vitalité':350},{'Vitalité':297},app.measured_goals.revision)
    jet={'Vitalité':297,'Force':38,'Intelligence':38,'Agilité':39,
         'Dommages Neutre':7,'Dommages Terre':7,'Dommages Feu':0,
         'Dommages Air':1,'Initiative':142,'% Résistance Eau':2,'Tacle':0}
    for i in range(3):app.workshop_readings.observe(jet,4.9,sequence=i)
    app.fast_slot_evidence=SlotEvidence((app.frame_mailbox,app.frame_mailbox.generation(),'DOFUS'),icon,3,capture_clock)
    app._verified_item_context=VerifiedItemContext(app.frame_mailbox,app.frame_mailbox.generation(),'DOFUS',1,app.item.get(),icon,())
    app.refresh_strategy()
    proposal=app.current_proposal
    assert proposal.rune is not None, repr(proposal)
    revision=app.measured_goals.revision
    import queue
    while not app.messages.empty():
        try:app.messages.get_nowait()
        except queue.Empty:break
    app.messages.put(('atelier_read',({'Vitalité':297},4.9)))
    for _ in range(20):app.process_messages()
    assert app.current_proposal.rune is None, 'A partial reading kept an actionable old rune'
    app.messages.put(('atelier_masked','Fenêtre temporairement masquée'))
    for _ in range(20):app.process_messages()
    assert app.active_equipment_verified, 'An overlay erased the identified item'
    assert app.measured_goals.revision==revision
    assert app.measured_goals.targets=={'Vitalité':350}
    assert app.workshop_readings.snapshot() is None, 'Masked pixels cannot authorize learning'
    assert app._verified_item_context is None
    app.refresh_strategy()
    assert app.current_proposal.rune is None, 'A masked reading kept an actionable old rune'
    assert app.strategy_current().kind=='calcul'
    # Neither a hidden icon nor contradictory tooltip text is a new item.
    for observed in (None,icon):
        app.messages.put(('item_visual',(None,None,'tooltip',observed,None,None,
            (('vitalite',1,2),('force',1,2),('agilite',1,2)),(),None,None)))
        for _ in range(20):app.process_messages()
        assert app.active_equipment_verified
        assert app.measured_goals.revision==revision
        assert app.current_proposal.rune is None
    # Reading resumes on the SAME item, with new jet/pool and unchanged goal.
    jet['Vitalité']=292
    for i in range(3):
        app.fast_slot_evidence=SlotEvidence((app.frame_mailbox,app.frame_mailbox.generation(),'DOFUS'),icon,3,capture_clock)
        app.messages.put(('atelier_read',(dict(jet),3.9)))
        for _ in range(20):app.process_messages()
    assert app._copilot_masked is False
    assert app.live_jet['Vitalité']==292
    assert app.live_pool==3.9
    assert app.measured_goals.revision==revision
    assert app.current_proposal.rune is not None
    resumed=app.current_proposal
    generation=app.frame_mailbox.invalidate('Capture native indisponible pendant un masquage')
    app.messages.put(('capture_invalidated',(app.frame_mailbox,generation,
        'Capture native indisponible pendant un masquage')))
    for _ in range(20):app.process_messages()
    assert app.active_equipment_verified
    assert app.current_proposal.rune is None
    other=Image.new('RGB',(32,32),'#38394e')
    ImageDraw.Draw(other).rectangle((4,4,27,27),fill='blue')
    for i in range(3):
        app.frame_mailbox.publish(Image.new('RGB',(1648,928)),'DOFUS',perf_counter_ns(),0)
        generation,frame=app.frame_mailbox.snapshot()
        app.messages.put(('worker_message',(app.frame_mailbox,generation,'DOFUS','identity_observation',
            (frame[0],perf_counter_ns(),'item_visual',(None,None,'',other,None,None,(),(),None,None)))))
        for _ in range(20):app.process_messages()
        if i<2:
            assert app.active_equipment_verified
            assert app.measured_goals.targets=={'Vitalité':350}
    assert not app.active_equipment_verified
    assert not app.measured_goals.targets
finally:
    app.running=False
    app.close()
'''
    env=dict(os.environ,PYTHONPATH=str(application),LOCALAPPDATA=str(tmp_path/'profile'),
             APPDATA=str(tmp_path/'roaming'),TEMP=str(tmp_path),TMP=str(tmp_path))
    result=subprocess.run([sys.executable,'-c',script],cwd=application,env=env,
                          capture_output=True,text=True,timeout=50)
    assert result.returncode==0,result.stdout+result.stderr


def test_replacement_requires_distinct_frames_and_ignores_hidden_icon():
    from forgely_copilot_continuity import IconReplacement
    from PIL import Image,ImageDraw
    old=Image.new('RGB',(32,32),'#38394e')
    new=old.copy()
    ImageDraw.Draw(old).ellipse((4,4,27,27),fill='red')
    ImageDraw.Draw(new).rectangle((4,4,27,27),fill='blue')
    latch=IconReplacement()
    assert latch.observe(old,new,1)=='pending'
    assert latch.observe(old,new,1)=='pending'
    assert latch.observe(old,None,2)=='hidden'
    assert latch.observe(old,old,3)=='same'
    assert latch.observe(old,new,4)=='pending'
    assert latch.observe(old,new,5)=='pending'
    assert latch.observe(old,new,6)=='changed'


def test_editing_goal_does_not_retain_previous_goals_advice():
    from forgely_copilot_continuity import advice_key,held_advice
    from forgely_measured_goals import MeasuredGoals
    from types import SimpleNamespace
    from unittest.mock import Mock
    app=SimpleNamespace(_copilot_masked=True,item=Mock(),goal_mode=Mock(),
                        measured_goals=MeasuredGoals(),plan=None,current_proposal=object())
    app.item.get.return_value='Objet';app.goal_mode.get.return_value='Jet propre'
    app.measured_goals.targets={'Vitalité':300}
    app._held_advice_key=advice_key(app)
    assert held_advice(app) is app.current_proposal
    app.measured_goals.targets={'Vitalité':350}
    assert held_advice(app) is None



