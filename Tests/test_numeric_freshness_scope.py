from dataclasses import replace

import pytest
from PIL import Image, ImageDraw

from forgely_copilot_continuity import ConfirmedAtelierRead


def reading_for(image, context):
    from forgely import workshop_change_signature
    from forgely_copilot_continuity import numeric_frame_signature
    return ConfirmedAtelierRead(context, workshop_change_signature(image), None,
        ({'Vitalité': 295, 'Tacle': 0}, 2.0),
        numeric_signature=numeric_frame_signature(image))


@pytest.mark.parametrize('box', [(300, 350, 310, 360), (820, 280, 830, 290),
                                  (780, 350, 790, 360)])
def test_history_rune_and_modification_changes_do_not_restart_numeric_confirmation(box):
    image = Image.new('RGB', (1648, 928), '#38394e')
    context = (object(), 'DOFUS', 123, image.size)
    reading = reading_for(image, context)
    changed = image.copy()
    ImageDraw.Draw(changed).rectangle(box, fill='white')
    from forgely import workshop_change_signature
    assert not reading.matches(context, workshop_change_signature(changed))
    assert reading.matches_numeric(context, changed)


@pytest.mark.parametrize('box', [(600, 300, 620, 320), (550, 185, 565, 200),
                                  (650, 185, 660, 200)])
def test_changed_jet_pool_or_item_still_rejects_numeric_reading(box):
    image = Image.new('RGB', (1648, 928), '#38394e')
    context = (object(), 'DOFUS', 123, image.size)
    reading = reading_for(image, context)
    changed = image.copy()
    ImageDraw.Draw(changed).rectangle(box, fill='white')
    assert not reading.matches_numeric(context, changed)


def test_numeric_freshness_never_crosses_window_or_dimension_boundary():
    image = Image.new('RGB', (1648, 928), '#38394e')
    context = (object(), 'DOFUS', 123, image.size)
    reading = reading_for(image, context)
    assert reading.matches_numeric(context, image.copy())
    assert not reading.matches_numeric((context[0], 'OTHER', 123, image.size), image)
    assert not reading.matches_numeric((context[0], 'DOFUS', 456, image.size), image)
    assert not reading.matches_numeric(context, image.resize((1600, 900)))


def test_legacy_read_without_numeric_provenance_fails_closed():
    image = Image.new('RGB', (1648, 928), '#38394e')
    context = (object(), 'DOFUS', 123, image.size)
    reading = replace(reading_for(image, context), numeric_signature=None)
    assert not reading.matches_numeric(context, image)


@pytest.mark.parametrize('pool', [0.0, 2.0, 2.9])
def test_cycloid_jet_stabilizes_through_history_animation_with_below_minimum_values(pool):
    import queue
    import threading
    from unittest.mock import Mock
    from forgely import Forgely, LatestFrameMailbox
    from forgely_workshop_readings import WorkshopReadings

    jet = {'Vitalité': 295, 'Force': 40, 'Intelligence': 40, 'Agilité': 20,
           'Dommages Neutre': 7, 'Dommages Terre': 10, 'Dommages Feu': 10,
           'Dommages Air': 7, 'Initiative': 195, '% Résistance Eau': 8, 'Tacle': 0}
    mailbox = LatestFrameMailbox()
    image = Image.new('RGB', (1648, 928), '#38394e')
    app = Mock()
    app.frame_mailbox = mailbox
    app.capture.last_handle = 123
    app.messages = queue.Queue()
    app.workshop_readings = WorkshopReadings()
    app.active_equipment_verified = True
    app.item.get.return_value = 'ANNEAU DU CYCLOÏDE'
    app.manual_equipment = None
    app.measured_goals = None
    app.fusion_pairing = None
    app.pending_transition = None
    app.live_jet = app.live_pool = None
    app.latest_observation_id = 0
    app.confirmation_requested = threading.Event()
    app.winfo_exists.return_value = False
    app.dashboard = None
    context = (mailbox, 'DOFUS', 123, image.size)
    for frame_id in range(1, 4):
        reading = replace(reading_for(image, context), numeric=(dict(jet), pool))
        latest = image.copy()
        ImageDraw.Draw(latest).rectangle((300, 350, 320, 360), fill=(frame_id * 70, 0, 0))
        mailbox.publish(latest, 'DOFUS', frame_id, 0)
        app.messages.put(('worker_message', (mailbox, mailbox.generation(), 'DOFUS',
            'observation', (frame_id, 1, 'atelier_read', (dict(jet), pool, reading)))))
        Forgely.process_messages(app)
        assert (app.workshop_readings.snapshot() is not None) == (frame_id == 3)
    assert app.live_jet == jet
    assert app.live_pool == pool
    assert app.item.get() == 'ANNEAU DU CYCLOÏDE'
