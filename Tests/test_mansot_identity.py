from pathlib import Path

from PIL import Image

from forgely_atelier import focus_workshop
from forgely_equipment_identity import slot_equipment_decision
from forgely_item_identity import ItemIdentityReader
from forgely_workshop_layout import WorkshopLocator
from runeforge_observer import extract_text


def mansot_frame():
    with Image.open(Path(__file__).parent / 'fixtures' / 'workshop_mansot_20261110.png') as image:
        locator = WorkshopLocator()
        frame = locator.normalize(image)
        assert locator.verified
        return focus_workshop(frame)


def test_mansot_is_identified_from_real_workshop_capture():
    reading = ItemIdentityReader(artwork_only=True).read(mansot_frame(), extract_text, [])
    assert reading.known == 'Anneau du Mansot Royal'
    assert reading.catalogue_verified


def test_mansot_artwork_cannot_override_contradictory_bounds():
    bounds = (('vitalite', 251, 300), ('sagesse', 21, 30), ('puissance', 16, 20))
    assert slot_equipment_decision(mansot_frame(), bounds).name is None
