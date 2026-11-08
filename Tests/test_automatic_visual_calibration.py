from pathlib import Path
import cv2
from forgely_reading_review import ReviewStore
from forgely_review_collection import ReviewCollector


def test_automatic_label_requires_pixel_digits_and_both_ocr_signals(tmp_path):
    store=ReviewStore(tmp_path/'reviews.sqlite3')
    service=ReviewCollector(store,review_ocr=lambda image:'40 Intelligence')
    image=cv2.imread(str(Path(__file__).parent/'fixtures/cv_review_intelligence_40.png'))
    key=store.offer(image,scale='a',suggestion='40 Intelligence');store.defer_automatic(key)
    service.process_automatic()
    assert store.get(key)['state']=='confirmed'
    assert store.get(key)['origin']=='automatic_numeric_agreement'
    assert store.reader('a') is None  # One example never activates an automatic label.


def test_ocr_agreement_cannot_override_different_known_pixel_value(tmp_path):
    store=ReviewStore(tmp_path/'reviews.sqlite3')
    service=ReviewCollector(store,review_ocr=lambda image:'39 Intelligence')
    image=cv2.imread(str(Path(__file__).parent/'fixtures/cv_review_intelligence_40.png'))
    key=store.offer(image,scale='a',suggestion='39 Intelligence');store.defer_automatic(key)
    service.process_automatic()
    assert store.get(key)['state']=='needs_review'
    assert not store.confirmed()


def test_failed_automatic_candidate_does_not_starve_later_rows(tmp_path):
    store=ReviewStore(tmp_path/'reviews.sqlite3')
    service=ReviewCollector(store,review_ocr=lambda image:'40 Intelligence')
    image=cv2.imread(str(Path(__file__).parent/'fixtures/cv_review_intelligence_40.png'))
    bad=store.offer(image,scale='a',suggestion='39 Intelligence');store.defer_automatic(bad)
    other=image.copy();other[0,0]=255
    good=store.offer(other,scale='a',suggestion='40 Intelligence');store.defer_automatic(good)
    service.process_automatic()
    store.defer_automatic(bad)
    service.process_automatic()
    assert store.get(good)['state']=='confirmed'


def test_better_panel_ocr_can_recover_an_unresolved_example(tmp_path):
    store=ReviewStore(tmp_path/'reviews.sqlite3')
    service=ReviewCollector(store,review_ocr=lambda image:'40 Intelligence')
    image=cv2.imread(str(Path(__file__).parent/'fixtures/cv_review_intelligence_40.png'))
    key=store.offer(image,scale='a',suggestion='39 Intelligence');store.defer_automatic(key)
    service.process_automatic()
    assert store.offer(image,scale='a',suggestion='40 Intelligence')==key
    store.defer_automatic(key);service.process_automatic()
    assert store.get(key)['state']=='confirmed'


def test_pool_can_also_be_calibrated_automatically(tmp_path):
    store=ReviewStore(tmp_path/'reviews.sqlite3')
    service=ReviewCollector(store,review_ocr=lambda image:'reliquat : 1,9')
    image=cv2.imread(str(Path(__file__).parent/'fixtures/cv_review_pool_1_9.png'))
    key=store.offer(image,scale='pool-a',suggestion='reliquat : 1,9',kind='pool')
    store.defer_automatic(key);service.process_automatic()
    assert store.get(key)['state']=='confirmed'
    assert store.get(key)['number']=='1,9'


def test_ocr_cannot_relabel_a_visually_known_characteristic(tmp_path):
    store=ReviewStore(tmp_path/'reviews.sqlite3')
    service=ReviewCollector(store,review_ocr=lambda image:'40 Force')
    image=cv2.imread(str(Path(__file__).parent/'fixtures/cv_review_intelligence_40.png'))
    key=store.offer(image,scale='a',suggestion='40 Force');store.defer_automatic(key)
    service.process_automatic()
    assert store.get(key)['state']=='needs_review'
