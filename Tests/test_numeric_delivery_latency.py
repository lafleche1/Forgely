import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from PIL import Image

from forgely_atelier import read_atelier, crop_zone


def test_numbers_are_delivered_while_history_and_modifications_are_still_running():
    image = Image.new('RGB', (1648, 928), '#38394e')
    # Force the modification reader to request OCR too.
    from PIL import ImageDraw
    ImageDraw.Draw(image).rectangle((780, 400, 790, 410), fill='white')
    release = threading.Event()
    delivered = threading.Event()
    received = []

    def ocr(patch_image):
        if patch_image.size == crop_zone(image, 'current_jet').size:
            return '295 Vitalité\n0 Tacle'
        if patch_image.size == crop_zone(image, 'reliquat').size:
            return 'reliquat : 2'
        assert release.wait(5), 'Slow nonnumeric zone was not released'
        return 'old history'

    def numeric_ready(reading):
        received.append(reading)
        delivered.set()

    with patch('forgely_atelier.workshop_visual_fallback', return_value=True), \
         patch('forgely_jet.read_current_jet_ocr', side_effect=lambda im, reader, **kwargs: reader(im)), \
         patch('forgely_atelier.read_reliquat_ocr', side_effect=lambda im, reader, **kwargs: reader(im)), \
         ThreadPoolExecutor(max_workers=1) as worker:
        job = worker.submit(read_atelier, image, ocr, title_cache={}, five_zones=True,
                            on_numeric=numeric_ready)
        try:
            assert delivered.wait(2), 'Numeric delivery waited for the history'
            assert not job.done()
            assert received[0].effects == '295 Vitalité\n0 Tacle'
            assert received[0].reliquat == 'reliquat : 2'
        finally:
            release.set()
        result = job.result(timeout=5)
    assert len(received) == 1
    assert result.history == 'old history'


def test_partial_numeric_delivery_cannot_be_reused_as_complete_history():
    from forgely_copilot_continuity import ConfirmedAtelierRead, read_current_atelier
    from unittest.mock import Mock
    context = (object(), 'DOFUS', 123, (1648, 928))
    partial = ConfirmedAtelierRead(context, ('pixels',), object(), ({'Tacle': 0}, 2.0),
                                  complete=False)
    reader = Mock(return_value='complete reading')
    result, reused = read_current_atelier(partial, context, ('pixels',), reader)
    assert result == 'complete reading'
    assert not reused


def test_skipped_rune_zone_is_not_reported_as_an_ocr_failure():
    from forgely_ocr_diagnostic import evaluate
    raw = 'HISTORIQUE\n-1 Intelligence\nEFFETS\n295 Vitalité\nRUNES (Pa / Ra)\n\nRELIQUAT\n2\nVISION\n'
    diagnostic = evaluate(raw, running=True, item_verified=True, jet_verified=True,
                          rune_zone_read=False)
    assert not any('Zone des runes illisible' in reason for reason in diagnostic.reasons)
    assert any('SC/SN/EC' in reason for reason in diagnostic.reasons)
    # The normal reader still reports an actual missing rune zone.
    normal = evaluate(raw, running=True, item_verified=True, jet_verified=True)
    assert any('Zone des runes illisible' in reason for reason in normal.reasons)


def test_observer_forwards_numbers_before_the_history_reader_returns():
    import queue
    from unittest.mock import Mock
    from PIL import ImageDraw
    from forgely import Forgely, LatestFrameMailbox
    from forgely_pipeline import VerifiedItemContext

    image = Image.new('RGB', (1648, 928), '#38394e')
    icon = image.resize((32, 32))
    ImageDraw.Draw(icon).ellipse((4, 4, 27, 27), fill='red')
    mailbox = LatestFrameMailbox()
    mailbox.publish(image, 'DOFUS', 1, 0)
    release = threading.Event()
    delivered = threading.Event()
    class Messages(queue.Queue):
        def put(self, message, *args, **kwargs):
            super().put(message, *args, **kwargs)
            if message[0] == 'worker_message' and message[1][3] == 'observation':
                if message[1][4][2] == 'atelier_read':
                    delivered.set()
    app = Mock()
    app.frame_mailbox = mailbox
    app.stop_event = threading.Event()
    app.capture = Mock(last_handle=123, manual_handle=None)
    app.messages = Messages()
    app.capture_debug_requested = threading.Event()
    app._confirmed_atelier_read = None
    app._verified_item_context = VerifiedItemContext(mailbox, 0, 'DOFUS', 0, 'known item', icon, ())
    app.active_equipment_verified = True
    app.item.get.return_value = 'known item'

    def ocr(patch_image):
        if patch_image.size == crop_zone(image, 'current_jet').size:
            return '295 Vitalité\n0 Tacle'
        if patch_image.size == crop_zone(image, 'reliquat').size:
            return 'reliquat : 2'
        assert release.wait(5)
        return ''
    with patch('forgely_atelier.workshop_visual_fallback', return_value=True), \
         patch('forgely.current_icon', return_value=icon), \
         patch('forgely.extract_text', side_effect=ocr), \
         patch('forgely_jet.read_current_jet_ocr', side_effect=lambda im, reader, **kwargs: reader(im)), \
         patch('forgely_atelier.read_reliquat_ocr', side_effect=lambda im, reader, **kwargs: reader(im)), \
         ThreadPoolExecutor(max_workers=1) as worker:
        job = worker.submit(Forgely.observer_worker, app)
        try:
            assert delivered.wait(2), 'Observer did not forward numeric delivery'
            assert not job.done()
            _, payload = app.messages.get_nowait()
            data = payload[4][3]
            assert data[:2] == ({'Vitalité': 295, 'Tacle': 0}, 2.0)
            assert data[2].complete is False
        finally:
            app.stop_event.set()
            release.set()
        job.result(timeout=5)


def test_history_completion_does_not_count_as_another_numeric_capture():
    import queue
    from dataclasses import replace
    from unittest.mock import Mock
    from forgely import Forgely
    from forgely_copilot_continuity import ConfirmedAtelierRead
    from forgely_workshop_readings import WorkshopReadings
    readings = WorkshopReadings()
    for frame in range(3):
        readings.observe({'Tacle': 0}, 2.0, sequence=frame)
    partial = ConfirmedAtelierRead(('same source',), ('pixels',), object(),
        ({'Tacle': 0}, 2.0), numeric_signature=('numeric pixels',), complete=False)
    complete = replace(partial, complete=True)
    app = Mock()
    app.messages = queue.Queue()
    app.messages.put(('atelier_read_complete', complete))
    app.workshop_readings = readings
    app._confirmed_atelier_read = partial
    app.winfo_exists.return_value = False
    Forgely.process_messages(app)
    assert readings.jet_streak == 3
    assert readings.pool_streak == 3
    assert app._confirmed_atelier_read is complete
