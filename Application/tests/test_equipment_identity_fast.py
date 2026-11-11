from dataclasses import dataclass
from unittest.mock import patch

from PIL import Image, ImageDraw
import pytest

from forgely_equipment_identity import EquipmentIdentityIndex, Reference, perceptual_hash


def art(color='red'):
    image = Image.new('RGB', (32, 32), '#38394e')
    ImageDraw.Draw(image).ellipse((5, 4, 26, 27), fill=color, outline='white', width=2)
    return image


SIG = (('force', 1, 10), ('vitalite', 20, 30), ('chance', 2, 5))


def ref(ident, name, category='Anneau', signature=SIG, image=None):
    return Reference(ident, name, category, signature, art() if image is None else image)


def test_shared_icon_is_excluded_even_with_category_or_discriminating_bounds():
    index = EquipmentIdentityIndex([ref(1, 'Alpha'), ref(2, 'Beta', 'Amulette')])
    assert index.resolve(art(), SIG).name is None
    assert index.resolve(art(), SIG, category='Anneau').name is None
    assert index.resolve(art(), SIG, category='Bottes').name is None
    other = (('force', 2, 11), *SIG[1:])
    index = EquipmentIdentityIndex([ref(1, 'Alpha'), ref(2, 'Beta', signature=other)])
    assert index.resolve(art(), SIG).name is None


def test_sparse_or_conflicting_evidence_never_auto_identifies():
    index = EquipmentIdentityIndex([ref(1, 'Alpha')])
    assert index.resolve(art(), SIG[:1]).name is None
    assert index.resolve(art(), (('force', 2, 10), *SIG[1:])).name is None
    assert index.resolve(Image.new('RGB', (32, 32))).name is None


def test_shared_icon_cannot_be_restored_by_name_ocr():
    index = EquipmentIdentityIndex([ref(1, 'Alpha'), ref(2, 'Beta')])
    calls = []
    def choose(candidates):
        calls.append(candidates)
        return 'Beta'
    result = index.resolve(art(), SIG, name_reader=choose)
    assert result.name is None
    assert calls == []
    assert index.resolve(art(), SIG, name_reader=lambda _: 'Outside').name is None
    unique = EquipmentIdentityIndex([ref(1, 'Alpha')])
    assert unique.resolve(art(), SIG, name_reader=lambda _: pytest.fail('OCR called')).name == 'Alpha'


def test_cache_key_includes_category_signature_and_pixels():
    index = EquipmentIdentityIndex([ref(1, 'Alpha')], cache_size=2)
    assert index.resolve(art(), SIG).name == 'Alpha'
    assert index.resolve(art(), SIG).name == 'Alpha'
    assert index.cache_hits == 1
    assert index.resolve(art(), (('force', 9, 10),)).name is None
    assert index.resolve(art(), SIG, category='Bottes').name is None
    assert len(index.cache) <= 2
    assert index.resolve(art('blue'), SIG).name is None


def test_homonyms_cannot_be_disambiguated_by_name_ocr():
    index = EquipmentIdentityIndex([ref(1, 'Alpha'), ref(2, 'Alpha')])
    assert index.resolve(art(), SIG, name_reader=lambda _: 'Alpha').name is None


def test_phash_is_deterministic_and_resize_tolerant():
    assert perceptual_hash(art()) == perceptual_hash(art().copy())
    assert (perceptual_hash(art()) ^ perceptual_hash(art().resize((64, 64)))).bit_count() <= 6


def test_effect_signature_preserves_elements_negative_bounds_and_current_jet_independence():
    from forgely_continuous_identity import effect_signature
    a = effect_signature('7 10 8 Dommages Terre\n7 10 9 Dommages Feu\n-10 -5 -7 Force')
    assert a == (('dommages feu', 7, 10), ('dommages terre', 7, 10), ('force', -10, -5))
    assert a == effect_signature('7 10 10 Dommages Terre\n7 10 7 Dommages Feu\n-10 -5 -9 Force')


def test_effect_signature_distinguishes_percent_from_flat_resistance():
    from forgely_continuous_identity import effect_signature
    assert effect_signature('7 10 8% Résistances Terre\n7 10 8 Résistance Terre') == (
        ('% resistance terre', 7, 10), ('resistance terre', 7, 10))


def test_reader_ocr_does_not_accept_name_outside_visual_candidates():
    from forgely_item_identity import ItemIdentityReader
    from forgely_equipment_identity import IdentityDecision
    image = Image.new('RGB', (1648, 928), '#292040')
    with patch('forgely_item_identity.workshop_visual_fallback', return_value=True), \
         patch('forgely_item_identity.current_icon', return_value=art()), \
         patch('forgely_item_identity.fast_equipment_match', return_value=None), \
         patch('forgely_item_identity.fast_equipment_decision', return_value=IdentityDecision(None, ((1, 'Alpha'), (2, 'Beta')), 'ambiguous')), \
         patch('forgely_item_identity.recognize_item_header', return_value=('Outside', None, 'Outside')):
        result = ItemIdentityReader(allow_name_ocr=True).read(image, lambda _: '', [(3, 'Outside')])
        assert result.known is None and result.candidate is None


def test_reader_uses_effects_before_name_and_invalidates_header_on_evidence_change():
    from forgely_item_identity import ItemIdentityReader
    image = Image.new('RGB', (1648, 928), '#292040')
    with patch('forgely_item_identity.workshop_visual_fallback', return_value=True), \
         patch('forgely_item_identity.current_icon', return_value=art()), \
         patch('forgely_item_identity.fast_equipment_match', return_value='Alpha'), \
         patch('forgely_item_identity.recognize_item_header') as header:
        assert ItemIdentityReader().read(image, lambda _: '1 10 5 Force', []).known == 'Alpha'
        header.assert_not_called()


def test_one_conflicting_bound_vetoes_old_bundled_slot_reference():
    from forgely_continuous_identity import match_current_item
    from forgely_equipment_identity import IdentityDecision
    with patch('forgely_equipment_identity.fast_equipment_decision', return_value=IdentityDecision(None, (), 'no_match')), \
         patch('forgely_continuous_identity.match_bundled_slot_icon', return_value='Alpha'), \
         patch('forgely_tools.natural_bounds', return_value={'Force': (1, 10)}):
        assert match_current_item(art(), (('force', 2, 10),)) is None


def test_missing_artwork_does_not_remove_homonym_guard(tmp_path):
    index = EquipmentIdentityIndex([ref(1, 'Alpha'), ref(2, 'Alpha', image=tmp_path/'missing.png')])
    assert index.resolve(art(), SIG).name is None


def test_duplicate_conflicting_natural_ranges_are_rejected():
    index = EquipmentIdentityIndex([ref(1, 'Alpha')])
    assert index.resolve(art(), (('force', 0, 9), *SIG)).name is None


def test_close_runner_outside_acceptance_threshold_still_blocks_winner():
    import numpy as np
    base = np.asarray(art(), dtype=np.int16)
    # Same structure/pHash, close colors: first distance ~9, runner ~11.
    shifted = lambda n: Image.fromarray(np.clip(base+n, 0, 255).astype('uint8'))
    index = EquipmentIdentityIndex([ref(1, 'Alpha', image=shifted(11)), ref(2, 'Beta', image=shifted(14))])
    assert index.resolve(art(), SIG).name is None


def test_reader_cannot_reaccept_an_item_vetoed_by_natural_bounds():
    from forgely_item_identity import ItemIdentityReader
    index = EquipmentIdentityIndex([ref(1, 'Alpha')])
    image = Image.new('RGB', (1648, 928), '#292040')
    with patch('forgely_item_identity.workshop_visual_fallback', return_value=True), \
         patch('forgely_item_identity.current_icon', return_value=art()), \
         patch('forgely_equipment_identity.bundled_identity_index', return_value=index), \
         patch('forgely_item_identity.recognize_item_header', return_value=('Alpha', None, 'Alpha')):
        assert ItemIdentityReader(allow_name_ocr=True).read(image, lambda _: '2 10 3 Force', [(1, 'Alpha')]).known is None


def test_reader_cannot_ocr_disambiguate_homonym_with_missing_artwork(tmp_path):
    from forgely_item_identity import ItemIdentityReader
    index = EquipmentIdentityIndex([ref(1, 'Alpha'), ref(2, 'Alpha', image=tmp_path/'missing.png')])
    image = Image.new('RGB', (1648, 928), '#292040')
    with patch('forgely_item_identity.workshop_visual_fallback', return_value=True), \
         patch('forgely_item_identity.current_icon', return_value=art()), \
         patch('forgely_equipment_identity.bundled_identity_index', return_value=index), \
         patch('forgely_item_identity.recognize_item_header', return_value=('Alpha', None, 'Alpha')):
        assert ItemIdentityReader(allow_name_ocr=True).read(image, lambda _: '', [(1, 'Alpha')]).known is None
