import numpy as np
import pytest


def sample():
    im = np.zeros((16,80,3),np.uint8)
    digit=np.array([[255,0],[255,255],[255,0]],np.uint8)
    label=np.array([[255,0,255,0,255],[0,255,0,255,0],[255,255,255,0,0]],np.uint8)
    im[5:8,15:17]=digit[:,:,None]
    im[5:8,23:28]=label[:,:,None]
    return im,digit


def test_candidates_deduplicate_persist_and_ill_readable_is_not_reasked(tmp_path):
    from forgely_reading_review import ReviewStore
    s=ReviewStore(tmp_path/'review.sqlite3',limit=2)
    im,_=sample()
    a=s.offer(im,scale='a',suggestion='1 Vitalité',context='objet A')
    assert s.offer(im.copy(),scale='a',context='objet B')==a
    assert len(ReviewStore(s.path).pending())==1
    s.reject(a)
    assert s.offer(im,scale='a')==a
    assert not s.pending()


def test_human_labels_require_distinct_examples_and_can_be_disabled(tmp_path):
    from forgely_reading_review import ReviewStore
    s=ReviewStore(tmp_path/'review.sqlite3')
    im,_=sample()
    a=s.offer(im,scale='a')
    s.confirm(a,'1','Vitalité',(15,5,2,3),(23,5,5,3))
    assert not s.reader('a')
    # Same glyph in a genuinely different mask: label differs by one pixel.
    im[6,25]=255
    b=s.offer(im,scale='a')
    s.confirm(b,'1','Vitalité',(15,5,2,3),(23,5,5,3))
    reader=s.reader('a')
    assert reader is not None
    assert reader.read_visible(im).jet=={'Vitalité':1}
    assert s.reader('other-scale') is None
    s.disable(b)
    assert s.reader('a') is None


def test_conflicting_shape_is_quarantined_and_bad_boxes_rejected(tmp_path):
    from forgely_reading_review import ReviewStore
    s=ReviewStore(tmp_path/'review.sqlite3')
    im,_=sample();a=s.offer(im,scale='a')
    with pytest.raises(ValueError):
        s.confirm(a,'1','Vitalité',(15,5,2,3),(15,5,2,3))
    s.confirm(a,'1','Vitalité',(15,5,2,3),(23,5,5,3))
    im[6,25]=255;b=s.offer(im,scale='a')
    s.confirm(b,'2','Vitalité',(15,5,2,3),(23,5,5,3))
    assert s.reader('a') is None


def test_queue_is_bounded_and_confirmation_never_uses_suggested_text(tmp_path):
    from forgely_reading_review import ReviewStore
    s=ReviewStore(tmp_path/'review.sqlite3',limit=1)
    im,_=sample();a=s.offer(im,scale='a',suggestion='999 Force')
    assert s.offer(im,scale='b') is None
    s.confirm(a,'1','Vitalité',(15,5,2,3),(23,5,5,3))
    row=s.get(a)
    assert row['number']=='1' and row['label']=='Vitalité'
    assert row['state']=='confirmed'


def test_same_label_pixels_cannot_mean_two_different_characteristics(tmp_path):
    from forgely_reading_review import ReviewStore
    s=ReviewStore(tmp_path/'review.sqlite3')
    im,_=sample();a=s.offer(im,scale='a')
    s.confirm(a,'1','Vitalité',(15,5,2,3),(23,5,5,3))
    im[12,60]=255;b=s.offer(im,scale='a')
    s.confirm(b,'1','Force',(15,5,2,3),(23,5,5,3))
    assert s.reader('a') is None


def test_partial_number_selection_cannot_train_a_truncated_value(tmp_path):
    from forgely_reading_review import ReviewStore
    s=ReviewStore(tmp_path/'review.sqlite3')
    im,digit=sample();label=im[5:8,23:28].copy();im[:]=0
    for x in (15,18,21):im[5:8,x:x+2]=digit[:,:,None]
    im[5:8,29:34]=label
    a=s.offer(im,scale='a')
    with pytest.raises(ValueError):
        s.confirm(a,'1','Vitalité',(21,5,2,3),(29,5,5,3))
    assert s.get(a)['state']=='pending'


def test_real_visible_40_intelligence_can_be_confirmed(tmp_path):
    import cv2
    from pathlib import Path
    from forgely_reading_review import ReviewStore
    image=cv2.imread(str(Path(__file__).parent/'fixtures/cv_review_intelligence_40.png'))
    s=ReviewStore(tmp_path/'review.sqlite3')
    ident=s.offer(image,scale='real-442x625')
    s.confirm(ident,'40','Intelligence',(43,7,19,16),(64,7,85,16))
    assert s.get(ident)['state']=='confirmed'


def test_real_decimal_pool_can_be_confirmed_without_rounding(tmp_path):
    import cv2
    from pathlib import Path
    from forgely_reading_review import ReviewStore
    image=cv2.imread(str(Path(__file__).parent/'fixtures/cv_review_pool_1_9.png'))
    s=ReviewStore(tmp_path/'review.sqlite3')
    ident=s.offer(image,scale='pool-real',kind='pool')
    s.confirm(ident,'1,9','Puits',(58,2,17,13),(7,2,48,13))
    assert s.get(ident)['number']=='1,9'
def test_retiring_pending_example_invalidates_collector_cache(tmp_path):
    import cv2
    from pathlib import Path
    from forgely_reading_review import ReviewStore
    store=ReviewStore(tmp_path/'reviews.sqlite3')
    image=cv2.imread(str(Path(__file__).parent/'fixtures/cv_review_intelligence_40.png'))
    ident=store.offer(image,scale='test')
    before=store.revision()
    store.retire(ident)
    assert store.revision()>before
    after=store.revision()
    store.retire(ident)
    assert store.revision()==after

