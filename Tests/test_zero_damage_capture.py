from pathlib import Path
from unittest.mock import patch

from PIL import Image
from forgely_jet import parse_jet, read_effects_ocr
from runeforge_observer import extract_text


FIXTURE = Path(__file__).parent / 'fixtures/effects_zero_damage_20261108.png'


def test_real_white_zero_rows_are_not_lost_or_replaced_by_natural_maximum():
    with Image.open(FIXTURE) as image:
        jet = parse_jet(read_effects_ocr(image, extract_text))
    assert jet['Dommages Terre'] == 0
    assert jet['Dommages Feu'] == 0
    assert jet['Dommages Air'] == 9
    assert jet['Vitalité'] == 279
    assert jet['Tacle'] == 2


def test_targeted_row_reader_requires_two_matching_explicit_numbers():
    from forgely_jet import recover_white_effect_rows
    with Image.open(FIXTURE) as image:
        result = recover_white_effect_rows(image, lambda _: 'O Dommage Terre', {})
        assert result == {}
        values = iter(['0 Dommage Terre', '1 Dommage Terre'] * 4)
        assert recover_white_effect_rows(image, lambda _: next(values), {}) == {}


def test_letter_o_cannot_overwrite_an_existing_tackle_value():
    from forgely_jet import recover_white_effect_rows
    with Image.open(FIXTURE) as image:
        assert recover_white_effect_rows(image, lambda _: 'O Tacle', {'Tacle': 2}) == {}


def test_missing_earth_zero_is_recovered_from_its_own_pixels():
    from forgely_jet import recover_white_effect_rows
    with Image.open(FIXTURE) as image:
        result = recover_white_effect_rows(image, extract_text, {'Force': 38})
    assert result['Dommages Terre'] == 0
    assert result['Dommages Feu'] == 0
    assert 'Force' not in result


def test_table_omission_of_earth_does_not_leave_dashboard_unread():
    from forgely_workshop_readings import WorkshopReadings
    from forgely_dashboard import stat_rows
    with Image.open(FIXTURE) as image:
        table_sizes = {image.size, (image.width-round(image.width*.32), image.height)}
        def ocr(patch_image):
            text = extract_text(patch_image)
            if patch_image.size in table_sizes:
                return '\n'.join(line for line in text.splitlines() if 'terre' not in line.lower())
            return text
        jet = parse_jet(read_effects_ocr(image, ocr))
    readings = WorkshopReadings()
    for _ in range(3):
        readings.observe(jet, 4.9)
    snapshot = readings.snapshot()
    assert snapshot is not None
    rows = stat_rows(snapshot[0], {'Dommages Terre': 10}, verified=True)
    earth = next(row for row in rows if row[0] == 'Dommages Terre')
    assert earth[1] == '0'
    assert earth[3] != 'À lire'
