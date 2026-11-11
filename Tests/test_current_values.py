import pytest
from forgely_dashboard import stat_rows
from forgely_rules import RUNE_CHOICES
from test_known_snapshot import known_app
from forgely_measured_goals import current_snapshot


@pytest.mark.parametrize('stat', list(RUNE_CHOICES))
def test_stale_number_is_never_presented_as_current(stat):
    row = stat_rows({stat:31}, {stat:40}, verified=True, states={stat:'stale'})[0]
    assert row[1] == '—'
    assert row[3] == 'À revérifier'
    fresh = stat_rows({stat:41}, {stat:40}, verified=True, states={stat:'confirmed'})[0]
    assert fresh[1] == '41'


def test_new_rune_masks_previous_complete_snapshot():
    app=known_app()
    app._copilot_masked=True
    assert current_snapshot(app) is None


def test_screenshot_overmax_agility_is_read_from_pixels():
    from pathlib import Path
    from PIL import Image
    from forgely_workshop_layout import WorkshopLocator
    from forgely_atelier import focus_workshop,read_atelier,choose_reliquat
    from forgely_ocr_backend import extract_text
    from forgely_jet import parse_jet
    fixture=Path(__file__).with_name('210012.png')
    with Image.open(fixture) as source:
        image=focus_workshop(WorkshopLocator().normalize(source.convert('RGB'),'regression'))
    result=read_atelier(image,extract_text,history_ocr=lambda _: '',five_zones=True)
    jet=parse_jet(result.effects)
    assert jet['Agilité']==41
    assert jet['Intelligence']==31
    assert jet['Force']==30
    assert choose_reliquat(result.effects,result.reliquat)==2


@pytest.mark.parametrize('stat',list(RUNE_CHOICES))
def test_every_stat_can_be_the_third_outlined_row(stat):
    from PIL import Image,ImageDraw
    from forgely_jet import read_current_jet_ocr,parse_jet
    from forgely_dofocus import normalise_jet,canonical_stat
    image=Image.new('RGB',(200,600),'#38394e')
    draw=ImageDraw.Draw(image)
    for y,height in ((50,20),(150,25),(250,30)):
        draw.rectangle((1,y,198,y+height),outline='#bdbdbd')
    def ocr(patch):
        # Whole-column OCR loses this outlined row; both focused variants
        # recover its value from the row, regardless of the stat name.
        return f'41 {stat}' if patch.height==27 else ''
    assert (normalise_jet(parse_jet(read_current_jet_ocr(image,ocr))) or {}).get(canonical_stat(stat))==41


@pytest.mark.parametrize('stat', list(RUNE_CHOICES))
def test_legacy_effects_reader_confirms_selected_value_for_every_stat(stat):
    from PIL import Image, ImageDraw
    from unittest.mock import patch
    from forgely_jet import read_effects_ocr, parse_jet
    from forgely_dofocus import normalise_jet, canonical_stat
    image = Image.new('RGB', (300, 600), '#38394e')
    ImageDraw.Draw(image).rectangle((97, 250, 299, 280), outline='#bdbdbd')

    def ocr(crop):
        if crop.height == 27:
            return f'41 {stat}'
        if crop.width == 300:
            return f'1 40 40 {stat}'  # Natural bounds are never current values.
        return '200 Vitalité\n6 Tacle'

    with patch('forgely_jet.recover_white_effect_rows', return_value={}):
        values = normalise_jet(parse_jet(read_effects_ocr(image, ocr)))
    assert values[canonical_stat(stat)] == 41


def test_live_recovery_does_not_assume_eleven_stats_is_complete():
    from PIL import Image, ImageDraw
    from forgely_jet import _recover_missing_effects_live
    image = Image.new('RGB', (300, 600), '#38394e')
    ImageDraw.Draw(image).rectangle((75, 250, 290, 280), outline='#bdbdbd')
    existing = {stat: 1 for stat in list(RUNE_CHOICES) if stat != 'Intelligence'}
    recovered, _ = _recover_missing_effects_live(
        image, existing, ocr_engine=lambda crop, psm: '41 Intelligence')
    assert recovered == {'Intelligence': 41}
