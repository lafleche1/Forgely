from pathlib import Path
from unittest.mock import patch

from PIL import Image
import pytest
from forgely_equipment_identity import bundled_identity_index


FIXTURES = Path(__file__).parent / 'fixtures'
RAT_SIGNATURE = (('vitalite', 51, 100), ('portee', 1, 1),
                 ('dommages air', 3, 5), ('esquive pm', -10, -10))
CYCLO_SIGNATURE = (('vitalite', 251, 300), ('force', 31, 40),
                   ('intelligence', 31, 40), ('agilite', 31, 40))


def test_full_slot_names_rat_from_catalogue_without_header_ocr():
    with Image.open(FIXTURES / 'slot_rat_brakmarien_20261108.png') as slot:
        decision = bundled_identity_index().resolve_slot(slot, RAT_SIGNATURE)
    assert decision.name == 'Anneau du rat brâkmarien'
    assert decision.method == 'slot_artwork_bounds'


def test_full_slot_names_cycloid_and_rejects_incompatible_bounds():
    with Image.open(FIXTURES / 'slot_cycloide_20261108.png') as slot:
        index = bundled_identity_index()
        assert index.resolve_slot(slot, CYCLO_SIGNATURE).name == 'Anneau du Cycloïde'
        assert index.resolve_slot(slot, RAT_SIGNATURE).name is None
        assert index.resolve_slot(slot, ()).name == 'Anneau du Cycloïde'


def test_blank_slot_with_known_bounds_cannot_supply_a_name():
    assert bundled_identity_index().resolve_slot(Image.new('RGB', (50, 45), '#45465b'), RAT_SIGNATURE).name is None


def test_automatic_reader_never_calls_name_ocr_or_registered_name_lookup():
    from forgely_item_identity import ItemIdentityReader
    frame = Image.new('RGB', (1920, 1080))
    with Image.open(FIXTURES / 'slot_rat_brakmarien_20261108.png') as slot:
        frame.paste(slot, (round(.380*1920), round(.185*1080)))
    def registered():
        raise AssertionError('No name lookup from OCR is permitted')
    calls = []
    def effects_ocr(image):
        calls.append(image.size)
        return '51 100 75 Vitalité\n1 1 1 Portée\n3 5 3 Dommages Air\n-10 -10 -10 Esquive PM'
    with patch('forgely_item_identity.workshop_visual_fallback', return_value=True), \
         patch('forgely_item_identity.current_icon', return_value=Image.effect_noise((32, 32), 50).convert('RGB')), \
         patch('forgely_item_identity.recognize_item_header', side_effect=AssertionError('Name OCR forbidden')):
        reading = ItemIdentityReader().read(frame, effects_ocr, registered)
    assert reading.known == 'Anneau du rat brâkmarien'
    assert len(calls) == 1


def test_unknown_automatic_reader_does_not_fall_back_to_name_ocr():
    from forgely_item_identity import ItemIdentityReader
    frame = Image.new('RGB', (1920, 1080), '#45465b')
    with patch('forgely_item_identity.workshop_visual_fallback', return_value=True), \
         patch('forgely_item_identity.current_icon', return_value=Image.effect_noise((32, 32), 50).convert('RGB')), \
         patch('forgely_item_identity.recognize_item_header', side_effect=AssertionError('Name OCR forbidden')):
        assert ItemIdentityReader().read(frame, lambda _: '', []).known is None


def test_shared_artwork_is_excluded_even_with_category_and_natural_bounds():
    from dataclasses import replace
    from forgely_equipment_identity import EquipmentIdentityIndex
    reference = next(r for r in bundled_identity_index().references if r.name == 'Anneau du rat brâkmarien')
    index = EquipmentIdentityIndex([replace(reference, item_id=1, name='Alpha', category='Anneau'),
                                    replace(reference, item_id=2, name='Beta', category='Amulette')])
    with Image.open(FIXTURES / 'slot_rat_brakmarien_20261108.png') as slot:
        assert index.resolve_slot(slot, RAT_SIGNATURE).name is None
        assert index.resolve_slot(slot, RAT_SIGNATURE, 'Anneau').name is None
        assert index.resolve_slot(slot, RAT_SIGNATURE, 'Bottes').name is None
    with Image.open(reference.image) as image:
        assert index.resolve(image, RAT_SIGNATURE, 'Anneau',
                             name_reader=lambda candidates:'Alpha').name is None


def test_verified_automatic_card_displays_catalogue_name_and_icon():
    from forgely_dashboard import equipment_card
    card = equipment_card('automatic', True, 'Anneau du rat brâkmarien')
    assert card['title'] == 'Anneau du rat brâkmarien'
    assert card['equipment'].icon_id == 9363


@pytest.mark.parametrize('old_name', [None, 'Ancien objet'])
def test_catalogue_identity_is_not_rejected_by_legacy_one_icon_one_name_storage(old_name):
    import queue
    from unittest.mock import Mock
    from forgely import Forgely
    from forgely_continuous_identity import CurrentSlotTracker
    from forgely_item_icons import ItemVisualTracker
    app = Mock()
    app.messages = queue.Queue()
    app.current_slot_tracker = CurrentSlotTracker()
    app.item_visual_tracker = ItemVisualTracker()
    app.active_equipment_verified = False
    app.item.get.return_value = ''
    app.winfo_exists.return_value = False
    app.workshop_readings.snapshot.return_value = None
    name = 'Anneau du rat brâkmarien'
    icon = Image.effect_noise((32, 32), 50).convert('RGB')
    with patch('forgely.match_current_item', return_value=old_name), \
         patch('forgely.natural_bounds', return_value={label: (lo, hi) for label, lo, hi in RAT_SIGNATURE}), \
         patch('forgely.register_item', return_value=(1, name)), \
         patch('forgely.remember_current_item', side_effect=ValueError('Legacy icon collision')), \
         patch('forgely.register_item_with_icon', side_effect=ValueError('Legacy icon collision')):
        for _ in range(3):
            app.messages.put(('item_visual', (name, None, '', icon, None, None, RAT_SIGNATURE, [], None, None)))
            Forgely.process_messages(app)
    assert app.active_equipment_verified is True
