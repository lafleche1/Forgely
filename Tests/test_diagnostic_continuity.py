from unittest.mock import Mock, patch
from PIL import Image, ImageDraw

from forgely_fast_preview import FastRunePreview
from forgely_workshop_readings import WorkshopReadings


def artwork(color):
    image = Image.new('RGB', (32, 32), '#38394e')
    ImageDraw.Draw(image).ellipse((4, 4, 27, 27), fill=color)
    return image


def test_missing_icon_suspends_history_without_erasing_identity():
    preview = FastRunePreview(('Fo',))
    image = Image.new('RGB', (1648, 928), '#38394e')
    icon = artwork('red')
    with patch('forgely_fast_preview.workshop_visual_fallback', return_value=True), \
         patch('forgely_fast_preview.current_icon', side_effect=[icon, None, icon]):
        preview.read(image, 'DOFUS', Mock(return_value=''))
        ocr = Mock(side_effect=AssertionError('Unreadable slot must suspend OCR'))
        suspended = preview.read(image, 'DOFUS', ocr)
        assert not suspended.event
        assert preview.context == 'DOFUS'
        assert preview.icon is not None
        assert 'icone_actuelle_absente' not in preview.reset_counts
        resumed = preview.read(image, 'DOFUS', Mock(return_value=''))
        assert not resumed.event
        assert not resumed.changes


def test_single_different_icon_does_not_replace_reference():
    preview = FastRunePreview(('Fo',))
    image = Image.new('RGB', (1648, 928), '#38394e')
    old = artwork('red')
    new = artwork('blue')
    with patch('forgely_fast_preview.workshop_visual_fallback', return_value=True), \
         patch('forgely_fast_preview.current_icon', side_effect=[old, new, old, new, new, new]):
        for index in range(6):
            preview.read(image, 'DOFUS', Mock(return_value=''))
            assert preview.icon.tobytes() == (new if index == 5 else old).tobytes()


def test_partial_reading_keeps_complete_display_but_disables_snapshot():
    readings = WorkshopReadings()
    for _ in range(3):
        readings.observe({'Vitalité': 342, 'Tacle': 0}, 4.9)
    for _ in range(3):
        readings.observe({'Tacle': 0}, None)
    assert readings.snapshot() is None
    assert readings.display_jet == {'Vitalité': 342, 'Tacle': 0}


def test_unchanged_preview_history_does_not_repeat_full_ocr():
    preview = FastRunePreview(('Fo',))
    image = Image.new('RGB', (1648, 928), '#38394e')
    ocr = Mock(return_value='')
    with patch('forgely_fast_preview.workshop_visual_fallback', return_value=True), \
         patch('forgely_fast_preview.current_icon', return_value=image.resize((32, 32))), \
         patch.object(preview.visual, 'observe', return_value=Mock(groups=())):
        for _ in range(4):
            preview.read(image, 'DOFUS', ocr)
        assert ocr.call_count == 1


def test_confirmed_current_jet_zone_survives_cache_expiry():
    from forgely_zone_cache import ZoneCache
    image = Image.new('RGB', (100, 100), 'white')
    cache = ZoneCache(refresh_seconds=0)
    cache.remember('current_jet', image, '342 Vitalité')
    cache.confirm_numeric(tuple(cache.entries.items()))
    ocr = Mock(return_value='unreadable')
    assert cache.read('current_jet', image, ocr) == '342 Vitalité'
    ocr.assert_not_called()
    image.putpixel((10, 10), (0, 0, 0))
    assert cache.read('current_jet', image, ocr) == 'unreadable'


def test_delayed_numeric_read_is_rejected_when_latest_workshop_changed():
    from forgely import Forgely, LatestFrameMailbox, workshop_change_signature
    from forgely_copilot_continuity import ConfirmedAtelierRead, numeric_frame_signature
    from types import SimpleNamespace
    import queue
    import threading
    image = Image.new('RGB', (1648, 928), '#38394e')
    mailbox = LatestFrameMailbox()
    reading = ConfirmedAtelierRead((mailbox, 'DOFUS', 123, image.size),
                                  workshop_change_signature(image), None, ({'Tacle': 0}, 4.9),
                                  numeric_signature=numeric_frame_signature(image))
    changed = image.copy()
    ImageDraw.Draw(changed).rectangle((600, 300, 620, 320), fill='white')
    mailbox.publish(changed, 'DOFUS', 2, 0)
    app = SimpleNamespace(frame_mailbox=mailbox, messages=queue.Queue(),
        capture=SimpleNamespace(last_handle=123), workshop_readings=WorkshopReadings(),
        live_jet={'Tacle': 0}, live_pool=4.9, refresh_strategy=Mock(),
        confirmation_requested=threading.Event(), winfo_exists=lambda: False)
    app.messages.put(('atelier_read', ({'Tacle': 0}, 4.9, reading)))
    Forgely.process_messages(app)
    assert app.live_jet is None
    assert app.live_pool is None
    assert app.confirmation_requested.is_set()
