from pathlib import Path
from PIL import Image
from forgely_equipment_identity import bundled_identity_index
from forgely_jet import parse_jet, read_effects_ocr
from runeforge_observer import extract_text
from unittest.mock import Mock, patch

FIXTURES = Path(__file__).parent / 'fixtures'


def test_gelano_is_identified_even_when_it_has_only_one_natural_effect():
    with Image.open(FIXTURES / 'slot_gelano_20261108.png') as slot:
        decision = bundled_identity_index().resolve_slot(slot, ())
    assert decision.name == 'Gelano'


def test_sparse_workshop_is_validated_by_profession_title_without_item_name_ocr():
    from forgely_item_identity import ItemIdentityReader
    with Image.open(FIXTURES / 'workshop_gelano_sparse_20261108.png') as frame, \
         patch('forgely_item_identity.recognize_item_header', side_effect=AssertionError('No name OCR')):
        reading = ItemIdentityReader().read(frame, extract_text, [])
    assert reading is not None
    assert reading.known == 'Gelano'
    assert reading.catalogue_verified is True


def test_sparse_title_proof_is_bound_to_exact_pixels_and_capture_context():
    from forgely_atelier import workshop_title_signature, workshop_frame_verified
    with Image.open(FIXTURES / 'workshop_gelano_sparse_20261108.png') as frame:
        context = (object(), 1, 'DOFUS')
        proof = workshop_title_signature(frame, context)
        assert not workshop_frame_verified(frame, context)
        assert workshop_frame_verified(frame, context, proof)
        assert not workshop_frame_verified(frame, (context[0], 2, 'DOFUS'), proof)
        changed = frame.copy()
        changed.putpixel((round(.4*frame.width), round(.18*frame.height)), (255, 255, 255))
        assert not workshop_frame_verified(changed, context, proof)


def test_zero_pa_and_added_vitality_are_read_without_inventing_bounds():
    with Image.open(FIXTURES / 'effects_gelano_20261108.png') as effects:
        jet = parse_jet(read_effects_ocr(effects, extract_text))
    assert jet == {'Vitalité': 15, 'PA': 0}


def app_with_old_reading():
    import queue
    from forgely_continuous_identity import CurrentSlotTracker
    from forgely_item_icons import ItemVisualTracker
    from forgely_workshop_readings import WorkshopReadings
    from forgely_measured_goals import MeasuredGoals
    app = Mock()
    app.messages = queue.Queue()
    app.current_slot_tracker = CurrentSlotTracker()
    app.item_visual_tracker = ItemVisualTracker()
    app.workshop_readings = WorkshopReadings()
    app.workshop_readings.configure(('old', 'Lavanneau'), ('Sagesse', 'Dommages Feu'))
    for _ in range(3):
        app.workshop_readings.observe({'Sagesse': 40, 'Dommages Feu': 10}, 5)
    app.measured_goals = MeasuredGoals()
    app.measured_goals.targets = {'Sagesse': 40}
    app.active_equipment_verified = True
    app.equipment_mode.get.return_value = 'automatic'
    app.item.get.return_value = 'Lavanneau'
    app.winfo_exists.return_value = False
    icon = Image.effect_noise((32, 32), 50).convert('RGB')
    for _ in range(3):
        app.current_slot_tracker.observe(icon)
    return app, icon


def test_new_catalogue_name_clears_old_jet_profile_and_goals_even_if_narrow_icon_is_similar():
    from forgely import Forgely
    app, icon = app_with_old_reading()
    with patch('forgely.register_item', return_value=(1, 'Gelano')):
        for _ in range(3):
            app.messages.put(('item_visual', ('Gelano', None, '', icon, None, None,
                                              (('pa', 1, 1),), [], None, None, True)))
            Forgely.process_messages(app)
    assert app.active_equipment_verified is True
    app.item.set.assert_called_with('Gelano')
    assert app.workshop_readings.expected == set()
    assert app.workshop_readings.snapshot() is None
    assert app.measured_goals.targets == {}
    assert app.live_jet is None
    app.perfect_goal_checked.set.assert_called_with(False)
    app.goal_mode.set.assert_called_with('')


def test_unknown_automatic_slot_cannot_be_named_from_an_old_learned_icon():
    from forgely import Forgely
    app, icon = app_with_old_reading()
    app.active_equipment_verified = False
    app.measured_goals.targets = {}
    with patch('forgely.match_current_item', return_value='Lavanneau'), \
         patch('forgely.remember_provisional', return_value=1):
        app.messages.put(('item_visual', (None, None, '', icon, None, None, (), [], None, None)))
        Forgely.process_messages(app)
    assert app.active_equipment_verified is False
    assert app.workshop_readings.expected == set()
    assert app.workshop_readings.snapshot() is None


def test_identity_worker_revalidates_full_artwork_even_if_old_narrow_icon_matches():
    import queue, threading
    from types import SimpleNamespace
    from forgely import Forgely, LatestFrameMailbox
    from forgely_continuous_identity import CurrentSlotTracker
    from forgely_item_identity import ItemIdentityRead
    from forgely_performance import PerformanceTracker
    from time import perf_counter_ns
    icon = Image.effect_noise((32, 32), 50).convert('RGB')
    tracker = CurrentSlotTracker()
    for _ in range(3):
        tracker.observe(icon)
    stop = threading.Event()
    mailbox = LatestFrameMailbox()
    mailbox.publish(Image.new('RGB', (1920, 1080), '#45465b'), 'DOFUS', perf_counter_ns(), 0)
    app = SimpleNamespace(stop_event=stop, frame_mailbox=mailbox, messages=queue.Queue(),
        active_equipment_verified=True, current_slot_tracker=tracker,
        fast_preview_performance=PerformanceTracker(), _verified_item_context=None)
    reading = ItemIdentityRead('Gelano', None, 'catalogue', icon, (), True)
    with patch('forgely.current_icon', return_value=icon), \
         patch('forgely_item_identity.ItemIdentityReader.read', return_value=reading) as read:
        thread = threading.Thread(target=Forgely.item_identity_worker, args=(app,))
        thread.start()
        try:
            try:
                message = app.messages.get(timeout=.5)
            except queue.Empty:
                message = None
        finally:
            stop.set()
            thread.join(timeout=1)
    assert read.call_count == 1
    assert message is not None


def test_calibrated_zero_requires_the_exact_digit_and_complete_pa_label():
    import cv2, numpy as np
    from forgely_cv.lines import GenericLineReader
    from forgely_cv.numbers import NumericReader, number_mask
    from forgely_cv.glyphs import segment_glyphs
    from forgely_review_collection import effect_rows
    profile = Path(__file__).parents[1] / 'Application/forgely_cv/profiles/white_zero_pa_9x11_v1'
    reader = GenericLineReader([NumericReader.from_directory(profile)])
    with Image.open(FIXTURES / 'effects_gelano_20261108.png') as image:
        row = effect_rows(cv2.cvtColor(np.asarray(image.convert('RGB')), cv2.COLOR_RGB2BGR))[-1]
    assert reader.read_line(row) == ('PA', 0)
    parts = segment_glyphs(number_mask(row))
    for glyph in (parts[1], parts[-1]):
        damaged = row.copy()
        y, x = np.argwhere(glyph.pixels > 0)[0]
        damaged[glyph.box.y+y, glyph.box.x+x] = (30, 30, 30)
        assert reader.read_line(damaged) is None
