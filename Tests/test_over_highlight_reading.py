from pathlib import Path
from PIL import Image
from forgely_atelier import crop_zone
from forgely_jet import parse_jet


def test_real_white_outlined_over_reads_eleven_not_missing_or_previous_five():
    from forgely_jet import read_current_jet_ocr
    from forgely_ocr_backend import extract_text
    image=Image.open(Path(__file__).parent/'fixtures/history_unity_20261109/160626.png')
    values=parse_jet(read_current_jet_ocr(crop_zone(image,'current_jet'),extract_text))
    assert values['Dommages Neutre']==11
    assert values['Vitalité']==281
    assert values['Force']==38
    assert values['% Résistance Eau']==0


def test_real_dim_outline_reads_current_eleven_after_a_new_rune():
    from forgely_jet import read_current_jet_ocr
    from forgely_ocr_backend import extract_text
    from forgely_workshop_layout import WorkshopLocator
    image=WorkshopLocator().normalize(Image.open(
        Path(__file__).parent/'fixtures/history_unity_20261109/180326.png'),'regression')
    values=parse_jet(read_current_jet_ocr(crop_zone(image,'current_jet'),extract_text))
    assert values['Dommages Neutre']==11
    assert values['Vitalité']==244
    assert values['Force']==13
    assert values['% Résistance Eau']==0


def test_partial_pool_is_explicit_in_report_and_never_becomes_advice_state():
    from forgely_predictive import report_measurements,report_text
    from forgely_decision import Proposal
    from forgely_workshop_readings import WorkshopReadings
    r=WorkshopReadings();r.configure('current',{'Force':40,'Dommages Neutre':10})
    for _ in range(3):r.observe({'Force':38},1.3)
    p=Proposal(None,'suspendu','Conseil suspendu · jet à relire','','')
    jet,pool,origin=report_measurements(p,{},None,readings=r,active=True)
    assert pool==1.3 and 'provisoire' in origin
    text=report_text(p,jet,{},None,pool,pool_origin=origin,compact=True)
    assert '1.3' in text and 'provisoire' in text
    assert r.snapshot() is None
    assert report_measurements(p,{},None,readings=r,active=False)[1] is None
    r.invalidate()
    assert report_measurements(p,{},None,readings=r,active=True)[1] is None
