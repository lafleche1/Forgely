from pathlib import Path
import cv2
import numpy as np
from forgely_cv.numbers import NumericReader

ROOT = Path(__file__).resolve().parents[1]


def test_numeric_labels_follow_translated_and_scrolled_rows():
    reader = NumericReader.from_directory(ROOT/'Application/forgely_cv/profiles/cycloide')
    im = cv2.imread(str(ROOT/'Tests/fixtures/effects_vitalite_342.png'))
    expected = reader.read(im)
    assert expected.accepted
    moved = cv2.warpAffine(im, np.float32([[1,0,25],[0,1,20]]),
                           (im.shape[1]+50, im.shape[0]+40))
    actual = reader.read_visible(moved)
    assert actual.jet == expected.jet
    assert actual.pool == expected.pool


def test_missing_rows_are_partial_not_zero_and_duplicate_labels_rejected():
    reader = NumericReader.from_directory(ROOT/'Application/forgely_cv/profiles/cycloide')
    im = cv2.imread(str(ROOT/'Tests/fixtures/effects_vitalite_342.png'))
    actual = reader.read_visible(im[220:].copy())
    assert 'Vitalité' not in actual.jet
    assert actual.jet['Intelligence'] == 40
    assert not actual.accepted
    doubled = np.concatenate([im, im], axis=0)
    assert not reader.read_visible(doubled).jet


def test_native_profiles_select_windowed_or_fullscreen_and_reject_ambiguity():
    from forgely_cv.pipeline import VisionPipeline, ProfilePipeline
    from forgely_cv.detection import InterfaceDetector
    from test_cv_pipeline import scene
    im, template, profile = scene()
    variant = 255-template
    pipeline = ProfilePipeline([
        VisionPipeline(InterfaceDetector(template, profile)),
        VisionPipeline(InterfaceDetector(variant, profile))])
    assert pipeline.process(im).detection is not None
    other = im.copy()
    other[25:37,45:65] = variant
    assert pipeline.process(other).detection is not None
    ambiguous = np.zeros((180,500,3),np.uint8)
    ambiguous[25:37,45:65] = template
    ambiguous[25:37,300:320] = variant
    assert pipeline.process(ambiguous).detection is None
    assert pipeline.process(np.zeros_like(im)).detection is None


def test_moving_label_does_not_truncate_a_longer_number():
    from forgely_cv.numbers import NumericField
    from forgely_cv.geometry import Rect
    from forgely_cv.glyphs import GlyphReader
    # Deliberately narrow original number box (one digit); later display 111.
    digit = np.array([[255,0],[255,255],[255,0]],np.uint8)
    label = np.array([[255,0,255,0,255],[0,255,0,255,0],[255,255,255,0,0]],np.uint8)
    im = np.zeros((10,100,3),np.uint8)
    for x in (30,33,36):
        im[3:6,x:x+2] = digit[:,:,None]
    im[3:6,41:46] = label[:,:,None]
    field = NumericField('Vitalité','stat',Rect(34,3,2,3),Rect(39,3,5,3),label,guard_error=0)
    reader = NumericReader(GlyphReader({'1':[digit]},max_error=0),[field])
    assert reader.read_visible(im).jet == {'Vitalité':111}
