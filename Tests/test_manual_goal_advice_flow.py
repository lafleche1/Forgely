import queue
from time import perf_counter_ns
from unittest.mock import Mock
from PIL import Image,ImageDraw


def test_manual_object_and_saved_goal_reach_advice_on_third_fresh_reading():
    from forgely import Forgely,LatestFrameMailbox
    from forgely_equipment_session import ManualEquipmentSession
    from forgely_equipment_catalog import EquipmentCatalog,equipment_bounds
    from forgely_workshop_readings import WorkshopReadings
    from forgely_measured_goals import MeasuredGoals
    item=EquipmentCatalog().search('Anneau','cycloide')[0]
    app=Mock();app.messages=queue.Queue();app.frame_mailbox=LatestFrameMailbox()
    app.latest_observation_id=0;app.winfo_exists.return_value=False
    app.manual_equipment=ManualEquipmentSession(item)
    app.current_slot_tracker=app.manual_equipment.tracker
    app.workshop_readings=WorkshopReadings();app.measured_goals=MeasuredGoals()
    app.item.get.return_value=item.identity_name;app.active_equipment_verified=False
    app.pending_transition=None;app.fast_slot_evidence=None;app.observation_only=False
    app.plan={'item':item.identity_name,'stats':{k:{'current':None,'target':max(v)} for k,v in equipment_bounds(item).items()}}
    app.live_laboratory.estimate.return_value=None
    app.live_laboratory.experience.return_value=None;app.simulator=None
    app.process_manual_equipment.side_effect=lambda *args:Forgely.process_manual_equipment(app,*args)
    artwork=Image.new('RGB',(32,32),'#38394e')
    ImageDraw.Draw(artwork).ellipse((4,4,27,27),fill='red')
    jet={'Vitalité':297,'Force':38,'Intelligence':37,'Agilité':39,
         'Dommages Neutre':7,'Dommages Terre':7,'Dommages Feu':0,'Dommages Air':1,
         'Initiative':142,'% Résistance Eau':2,'Tacle':0}
    for frame in range(1,4):
        app.frame_mailbox.publish('pixels','DOFUS',perf_counter_ns(),0)
        generation=app.frame_mailbox.generation()
        for kind,data in [('atelier_read',(jet,.9)),('item_visual',
                          (None,None,'Nom choisi',artwork,None,None,(),[],None,None))]:
            app.messages.put(('worker_message',(app.frame_mailbox,generation,'DOFUS','observation',
                              (frame,perf_counter_ns(),kind,data))))
        Forgely.process_messages(app)
    assert app.active_equipment_verified
    assert app.live_jet==jet and app.live_pool==.9
    assert Forgely.strategy_current(app).rune is not None
