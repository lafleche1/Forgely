from decimal import Decimal
import cv2
import numpy as np
from forgely_cv.numbers import parse_number, NumericReader, NumericField, number_mask
from forgely_cv.glyphs import GlyphReader
from forgely_cv.geometry import Rect


def test_decimal_pool_is_exact_and_invalid_or_negative_pool_is_unknown():
    assert parse_number('0,1', 'pool') == Decimal('0.1')
    assert parse_number('-12', 'stat') == Decimal('-12')
    for text in ('', '?', 'O', '1 2', '--2', '1,2,3', '-0.1', '-0', '01'):
        assert parse_number(text, 'pool') is None
    assert parse_number('1,2', 'stat') is None
    assert parse_number('30001', 'stat') is None


def test_number_roi_and_label_guard_are_required_for_acceptance():
    image = np.zeros((30, 60, 3), np.uint8)
    zero = np.array([[255,255,255],[255,0,255],[255,0,255],[255,255,255]], np.uint8)
    image[10:14, 4:7] = cv2.cvtColor(zero, cv2.COLOR_GRAY2BGR)
    image[10:14, 20:30] = 255
    guard = number_mask(image[10:14,20:30])
    field = NumericField('PA', 'stat', Rect(3,9,6,6), Rect(20,10,10,4), guard)
    reader = NumericReader(GlyphReader({'0':[zero]},max_error=0), [field])
    result = reader.read(image)
    assert result.accepted and result.jet == {'PA':0}
    image[10:14,20:30] = 0
    assert not reader.read(image).accepted
    assert reader.read(image).jet == {}


def test_unknown_digit_never_becomes_zero():
    image = np.zeros((30,60,3),np.uint8)
    image[10:15,4:8] = 255
    image[10:14,20:30] = 255
    field = NumericField('PA','stat',Rect(3,9,8,8),Rect(20,10,10,4),number_mask(image[10:14,20:30]))
    result = NumericReader(GlyphReader({}),[field]).read(image)
    assert not result.accepted and result.jet == {}


def test_stabilization_requires_distinct_fresh_frames_and_same_context():
    from forgely_cv.numbers import NumericStabilizer,NumericReading
    value=NumericReading({'PA':0},Decimal('0.1'),{},True)
    stable=NumericStabilizer()
    assert not stable.observe(value,context='a',sequence=1,captured_ns=100,now_ns=200)
    assert not stable.observe(value,context='a',sequence=1,captured_ns=100,now_ns=200)
    for sequence in (2,3):
        assert not stable.observe(value,context='a',sequence=sequence,captured_ns=sequence*100,now_ns=sequence*100+100)
    assert stable.observe(value,context='a',sequence=4,captured_ns=400,now_ns=500)
    assert not stable.observe(value,context='b',sequence=1,captured_ns=500,now_ns=600)
    assert not stable.observe(value,context='b',sequence=2,captured_ns=100,now_ns=2_000_000_000)


def test_confirmation_history_expires_even_when_each_new_frame_is_fresh():
    from forgely_cv.numbers import NumericStabilizer,NumericReading
    value=NumericReading({'PA':0},Decimal('0.1'),{},True)
    stable=NumericStabilizer()
    for i in range(1,4):
        assert not stable.observe(value,context='a',sequence=i,captured_ns=i*10_000_000_000,now_ns=i*10_000_000_000)


def test_real_calibration_profile_reads_342_and_decimal_pool():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    reader=NumericReader.from_directory(root/'Application/forgely_cv/profiles/cycloide')
    image=cv2.imread(str(root/'Tests/fixtures/effects_vitalite_342.png'))
    result=reader.read(image)
    assert result.accepted and result.jet['Vitalité']==342 and result.jet['Tacle']==0
    assert result.pool==Decimal('0.1')
    # Même position et bon libellé mais un pixel perturbé dans le nombre :
    # aucune correction automatique vers la valeur de calibration.
    image[152,194]=0
    assert not reader.read(image).accepted


def test_recomposed_new_number_is_read_without_reusing_calibration_value():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    reader=NumericReader.from_directory(root/'Application/forgely_cv/profiles/cycloide')
    image=cv2.imread(str(root/'Tests/fixtures/effects_vitalite_342.png'))
    # Recomposition synthétique à partir de deux glyphes réels : test de code,
    # pas une nouvelle capture indépendante de DOFUS.
    font=root/'Application/forgely_cv/profiles/cycloide/font'
    import json
    entries=json.loads((font/'manifest.json').read_text(encoding='utf8'))['glyphs']
    two=cv2.imread(str(font/next(r['file'] for r in entries if r['char']=='2')),0)
    four=cv2.imread(str(font/next(r['file'] for r in entries if r['char']=='4')),0)
    field=next(f for f in reader.fields if f.name=='Force')
    crop=field.box.crop(image);crop[:]=0
    x=1
    for glyph in (two,four):
        h,w=glyph.shape
        crop[3:3+h,x:x+w]=cv2.cvtColor(glyph,cv2.COLOR_GRAY2BGR)
        x+=w+1
    result=reader.read(image)
    assert result.accepted and result.jet['Force']==24
