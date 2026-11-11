import pytest
from pathlib import Path
import cv2


@pytest.mark.skipif(not (Path(__file__).parent/'fixtures'/'cv_padgref_native_bottom_panel.png').exists() or not (Path(__file__).parent/'fixtures'/'cv_padgref_native_top_panel.png').exists(),reason='Capture privée de référence non fournie')
def test_native_padgref_calibration_preserves_all_pages_and_negative_lines():
    # Calibration smoke test, not an independent accuracy measurement.
    from forgely_cv.lines import GenericLineReader
    from forgely_review_collection import calibrated_export_readers
    from forgely_workshop_readings import WorkshopReadings
    reader=GenericLineReader(calibrated_export_readers())
    base=Path(__file__).parent/'fixtures'
    top=reader.read_effects(cv2.imread(str(base/'cv_padgref_native_top_panel.png')))
    bottom=reader.read_effects(cv2.imread(str(base/'cv_padgref_native_bottom_panel.png')))
    expected={'PM':1,'Vitalité':96,'Intelligence':60,'Agilité':58,'Sagesse':30,
              'Coups Critiques':6,'Portée':1,'Invocation':1,'Dommages Feu':6,
              'Dommages Air':6,'% Résistance Eau':8,'Résistance Terre':7,
              'Résistance Air':7,'Dommages Critiques':11,'Tacle':-4,'Esquive PM':-3}
    assert {**top,**bottom}==expected
    tracker=WorkshopReadings();tracker.configure('padgref',expected)
    for i in range(3):tracker.observe(top,0,sequence=i)
    assert tracker.snapshot() is None
    for i in range(3,6):tracker.observe(bottom,0,sequence=i)
    from forgely_dofocus import normalise_jet
    assert tracker.snapshot()==(normalise_jet(expected),0)
    assert not tracker.atomic_snapshot


@pytest.mark.skipif(not (Path(__file__).parent/'fixtures'/'cv_cycloide_holdout_224632.png').exists(),reason='Capture privée de référence non fournie')
def test_generic_reader_reads_whole_heldout_jet_without_item_name():
    from forgely_cv.lines import GenericLineReader
    from forgely_review_collection import calibrated_export_readers
    reader=GenericLineReader(calibrated_export_readers())
    image=cv2.imread(str(Path(__file__).parent/'fixtures/cv_cycloide_holdout_224632.png'))
    jet=reader.read_effects(image)
    assert jet=={'Vitalité':297,'Force':38,'Intelligence':40,'Agilité':39,
                 'Dommages Neutre':7,'Dommages Terre':7,'Dommages Feu':0,'Dommages Air':1,
                 'Initiative':142,'% Résistance Eau':2,'Tacle':0}


@pytest.mark.skipif(not (Path(__file__).parent/'fixtures'/'cv_review_intelligence_40.png').exists(),reason='Capture privée de référence non fournie')
def test_generic_reader_values_are_not_fixed_by_the_training_item():
    from forgely_cv.lines import GenericLineReader
    from forgely_review_collection import calibrated_export_readers
    from forgely_cv.numbers import number_mask
    from forgely_cv.glyphs import segment_glyphs
    reader=GenericLineReader(calibrated_export_readers())
    image=cv2.imread(str(Path(__file__).parent/'fixtures/cv_review_intelligence_40.png'))
    # Move the row and surround it with unrelated screen padding.
    import numpy as np
    padded=np.zeros((70,500,3),np.uint8);padded[20:54,100:392]=image
    assert reader.read_line(padded)==('Intelligence',40)
    changed=image.copy();changed[:,53:61]=image[:,44:52]
    assert reader.read_line(changed)==('Intelligence',44)
    assert reader.read_line(image[:,:110]) is None


@pytest.mark.skipif(not (Path(__file__).parent/'fixtures'/'cv_padgref_negative.png').exists(),reason='Capture privée de référence non fournie')
def test_negative_sign_is_not_lost_during_row_extraction():
    from forgely_cv.lines import GenericLineReader
    from forgely_review_collection import calibrated_export_readers
    image=cv2.imread(str(Path(__file__).parent/'fixtures/cv_padgref_negative.png'))
    reader=GenericLineReader(calibrated_export_readers())
    assert reader.read_line(image[:35])==('Tacle',-4)
    assert reader.read_line(image[40:])==('Esquive PM',-3)
