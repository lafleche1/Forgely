from types import SimpleNamespace
from unittest.mock import Mock
import pytest


@pytest.mark.parametrize('running,detected,expected',[
    (True,True,'active'),(True,False,'waiting'),(False,True,'paused'),(False,False,'paused'),
])
def test_workshop_indicator_only_describes_detection(running,detected,expected):
    from forgely_copilote import workshop_state
    assert workshop_state(running,detected)==expected


def test_status_changes_cannot_replace_the_advisors_message():
    from forgely_overlay import FloatingBadge
    overlay=SimpleNamespace(_prediction='current report',feed_label=Mock(),advice_label=Mock(),
                            status_dot=Mock(),status_text=Mock())
    FloatingBadge.state_color(overlay,'waiting')
    overlay.advice_label.configure.assert_not_called()
    overlay.feed_label.configure.assert_not_called()
    assert overlay._prediction=='current report'


def test_valid_detection_notice_sets_shared_detection_state():
    import queue
    from PIL import Image
    from forgely import Forgely,LatestFrameMailbox
    app=Mock();app.messages=queue.Queue();app.winfo_exists.return_value=False
    app.frame_mailbox=LatestFrameMailbox();app.frame_mailbox.publish(Image.new('RGB',(32,32)),'DOFUS',1,0)
    app.running=True;app.workshop_active=False
    app.messages.put(('workshop_detected',(app.frame_mailbox,app.frame_mailbox.generation(),'DOFUS')))
    Forgely.process_messages(app)
    assert app.workshop_active is True
    app.confirmation_requested.set.assert_called()
    app.overlay.state_color.assert_called_with('active')


def test_opening_badge_cannot_turn_an_undetected_workshop_green():
    from forgely import Forgely
    app=SimpleNamespace(running=True,workshop_active=False,overlay=Mock(),withdraw=Mock())
    Forgely.minimize_to_badge(app)
    app.overlay.state_color.assert_called_once_with('waiting')


@pytest.mark.parametrize('message',['waiting_window','atelier_waiting'])
def test_unavailable_game_cannot_retain_a_green_detection_indicator(message):
    import queue
    from forgely import Forgely
    app=Mock();app.messages=queue.Queue();app.winfo_exists.return_value=False
    app.running=True;app.workshop_active=True;app.retain_masked_copilot.return_value=True
    app.messages.put((message,'Capture indisponible'))
    Forgely.process_messages(app)
    assert app.workshop_active is False
    app.overlay.state_color.assert_called_with('waiting')


def test_structural_recovery_restores_indicator_before_numeric_reading():
    import queue
    from forgely import Forgely
    app=Mock();app.messages=queue.Queue();app.winfo_exists.return_value=False
    app.running=True;app.workshop_active=False
    app.messages.put(('atelier_masked','Structure reconnue, jet illisible'))
    Forgely.process_messages(app)
    assert app.workshop_active is True
    app.retain_masked_copilot.assert_called_once()
    app.overlay.state_color.assert_called_with('active')
