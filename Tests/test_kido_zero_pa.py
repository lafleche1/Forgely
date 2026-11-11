from pathlib import Path
from PIL import Image
from forgely_atelier import crop_zone
from forgely_jet import parse_jet,read_current_jet_ocr
from forgely_ocr_backend import extract_text


def test_current_reader_recovers_zero_pa_from_user_capture():
    image=Image.open(Path(__file__).parent/'fixtures/kido_zero_pa_20261110.png')
    patch=crop_zone(image,'current_jet')
    def ocr(crop):
        # Reproduce the actual broad OCR failure without manufacturing a zero.
        if crop.size==patch.size:
            return '145 Vitalité\n39 Intelligence\n38 Sagesse\n# OPA\n15 Prospection\n9% Résistance Feu\n10% Résistance Air'
        return extract_text(crop)
    jet=parse_jet(read_current_jet_ocr(patch,ocr))
    assert jet=={'Vitalité':145,'Intelligence':39,'Sagesse':38,'PA':0,
        'Prospection':15,'% Résistance Feu':9,'% Résistance Air':10}


def test_bare_ambiguous_label_is_not_a_numeric_measurement():
    assert parse_jet('# OPA')=={}


def test_capture_normalization_and_focus_use_same_zero_recovery_as_live_app():
    from forgely_workshop_layout import WorkshopLocator
    from forgely_atelier import focus_workshop,read_reliquat_ocr,parse_reliquat
    from forgely_workshop_readings import WorkshopReadings
    from forgely_vision_guidance import reference_for
    image=Image.open(Path(__file__).parent/'fixtures/kido_zero_pa_20261110.png')
    image=focus_workshop(WorkshopLocator().normalize(image,'live-replay'))
    jet=parse_jet(read_current_jet_ocr(crop_zone(image,'current_jet'),extract_text))
    pool=parse_reliquat(read_reliquat_ocr(crop_zone(image,'reliquat'),extract_text))
    tracker=WorkshopReadings()
    tracker.configure(('confirmed','Médaille Kido'),reference_for('Médaille Kido'))
    for sequence in range(3):tracker.observe(jet,pool,sequence=sequence)
    assert jet['PA']==0
    assert tracker.snapshot()==(jet,94)
    assert tracker.waiting_reason is None


def test_pool_crop_contains_complete_label_and_94_on_user_capture():
    from forgely_atelier import read_reliquat_ocr,parse_reliquat
    image=Image.open(Path(__file__).parent/'fixtures/kido_zero_pa_20261110.png')
    assert parse_reliquat(read_reliquat_ocr(crop_zone(image,'reliquat'),extract_text))==94


def test_calibrated_zero_is_rejected_when_digit_or_label_changes():
    import numpy as np,cv2
    from forgely_jet import _trusted_effect_line_reader
    from forgely_review_collection import complete_stat_line
    from forgely_cv.numbers import number_mask
    from forgely_cv.glyphs import segment_glyphs
    image=Image.open(Path(__file__).parent/'fixtures/kido_zero_pa_20261110.png')
    patch=crop_zone(image,'current_jet')
    row=cv2.cvtColor(np.asarray(patch.crop((0,182,patch.width,200))),cv2.COLOR_RGB2BGR)
    row=complete_stat_line(row)
    reader=_trusted_effect_line_reader()
    assert reader.read_line(row)==('PA',0)
    parts=segment_glyphs(number_mask(row))
    for part in (parts[1],parts[-1]):
        changed=row.copy()
        y,x=np.argwhere(part.pixels>0)[0]
        changed[part.box.y+y,part.box.x+x]=(30,30,30)
        assert reader.read_line(changed) is None
