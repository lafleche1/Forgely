import queue
from unittest.mock import Mock
from PIL import Image
import pytest
from forgely_decision import advise
from forgely import Forgely
from forgely_workshop_readings import WorkshopReadings


@pytest.mark.parametrize('pool',[0,.1,.9])
def test_video_near_max_lines_can_use_pa_without_covered_pool(pool):
    jet={'Vitalité':294,'Force':39,'Intelligence':39,'Agilité':36,
         'Dommages Neutre':8,'Dommages Terre':10,'Dommages Feu':10,
         'Dommages Air':8,'Initiative':156,'% Résistance Eau':8,'Tacle':1}
    target={'Vitalité':300,'Force':40,'Intelligence':40,'Agilité':0,
            'Dommages Neutre':0,'Dommages Terre':0,'Dommages Feu':0,
            'Dommages Air':0,'Initiative':100,'% Résistance Eau':0,'Tacle':0}
    p=advise(jet,target,None,pool,item='Anneau du Cycloïde',level=200,predictive_policy=True)
    assert p.rune in ('Pa Fo','Pa Ine')
    assert 'exposition' in p.explanation
    assert 'réserve' in p.explanation


@pytest.mark.parametrize('identity_frame',[10,12])
def test_late_hidden_icon_does_not_suspend_newer_confirmed_numbers(identity_frame):
    app=Mock();app.messages=queue.Queue();app.winfo_exists.return_value=False
    app.latest_observation_id=10
    app.item.get.return_value='objet';app.active_equipment_verified=True
    app.current_slot_tracker.icon=Image.new('RGB',(32,32),'red')
    app.measured_goals=None
    app.workshop_readings=WorkshopReadings()
    for _ in range(3):app.workshop_readings.observe({'Force':39},.1)
    app._stable_numeric_frame=(None,12,'objet')
    app.live_jet={'Force':39};app.live_pool=.1;app.live_after_fusion=False
    data=(None,None,'',None,None,None,(),(),None,None)
    app.messages.put(('observation',(identity_frame,0,'item_visual',data)))
    Forgely.process_messages(app)
    app.retain_masked_copilot.assert_not_called()
    assert app.workshop_readings.snapshot()==({'Force':39},.1)


def test_current_hidden_icon_still_suspends_old_snapshot():
    app=Mock();app.messages=queue.Queue();app.winfo_exists.return_value=False
    app.latest_observation_id=10
    app.item.get.return_value='objet';app.active_equipment_verified=True
    app.current_slot_tracker.icon=Image.new('RGB',(32,32),'red')
    app.measured_goals=None
    app.workshop_readings=WorkshopReadings()
    for _ in range(3):app.workshop_readings.observe({'Force':39},.1)
    app._stable_numeric_frame=(None,10,'objet');app.live_after_fusion=False
    data=(None,None,'',None,None,None,(),(),None,None)
    app.messages.put(('observation',(12,0,'item_visual',data)))
    Forgely.process_messages(app)
    app.retain_masked_copilot.assert_called_once()


def test_uncovered_pa_does_not_override_more_plausible_natural_repair():
    jet={'Force':39,'Dommages Terre':9}
    target={'Force':40,'Dommages Terre':10}
    p=advise(jet,target,target,.1,predictive_policy=True,level=200)
    assert p.rune=='Do Terre'


def test_uncovered_pa_does_not_override_verified_simple_rune_success():
    def calibration(rune):
        return {'verified':True,'counts':{'SC':10000 if rune=='Fo' else 0,
                'SN':0,'EC':0 if rune=='Fo' else 10000}}
    p=advise({'Force':39,'Intelligence':39},{'Force':40,'Intelligence':40},
             {'Force':40,'Intelligence':40},.1,predictive_policy=True,
             context_for=calibration)
    assert p.rune=='Fo'
