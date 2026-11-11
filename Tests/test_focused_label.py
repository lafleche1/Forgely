from pathlib import Path
from PIL import Image,ImageDraw
from forgely_jet import read_current_jet_ocr,parse_jet


def test_exported_live_frame_confirms_outlined_vitality():
    from forgely_ocr_backend import extract_text
    image=Image.open(Path(__file__).with_name('live-effects.png'))
    patch=image.crop((144,95,346,653))
    values=parse_jet(read_current_jet_ocr(patch,extract_text))
    assert values=={'Vitalité':22,'Agilité':19}
    from forgely_workshop_readings import WorkshopReadings
    from forgely_decision import advise
    targets={'Vitalité':20,'Agilité':20}
    readings=WorkshopReadings(required_frames=2);readings.configure('Champêtre',targets)
    assert not readings.observe(values,.2,sequence=1)
    assert readings.observe(values,.2,sequence=2)
    jet,pool=readings.snapshot()
    assert advise(jet,targets,targets,pool,predictive_policy=True).rune=='Age'


def outlined():
    image=Image.new('RGB',(200,600),'#38394e')
    ImageDraw.Draw(image).rectangle((1,50,198,70),outline='#bdbdbd')
    return image


def test_label_typo_can_agree_but_different_number_cannot():
    for text,accepted in [('22 Vitalita',True),('23 Vitalita',False),('-22 Vitalita',False),('−22 Vitalita',False),
                          ('22 Agilite',False),('22 VitalXYZ',False),('22 PM',False)]:
        calls=iter(['19 Agilité','22 Vitalité',text])
        values=parse_jet(read_current_jet_ocr(outlined(),lambda _:next(calls)))
        assert ('Vitalité' in values)==accepted
        if accepted:assert values['Vitalité']==22


def test_short_pa_pm_names_are_never_fuzzily_confused():
    calls=iter(['19 Agilité','1 PA','1 PB'])
    assert 'PA' not in parse_jet(read_current_jet_ocr(outlined(),lambda _:next(calls)))
