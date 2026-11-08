import numpy as np
from PIL import Image


def test_review_region_keeps_the_last_workshop_row():
    from forgely_atelier import ZONES
    # Normalized workshop bottom is 763/928; the last row must fit above it.
    assert ZONES['review_effects'][3] >= 763/928


def test_known_whole_line_retires_old_unnecessary_review(tmp_path):
    import cv2
    from pathlib import Path
    from forgely_reading_review import ReviewStore
    from forgely_review_collection import ReviewCollector,complete_stat_line
    store=ReviewStore(tmp_path/'review.sqlite3')
    image=cv2.imread(str(Path(__file__).parent/'fixtures/cv_review_intelligence_40.png'))
    ident=store.offer(complete_stat_line(image),scale='old-scale',suggestion='40 Intelligence')
    ReviewCollector(store)
    assert store.get(ident)['state']=='superseded'
    assert not store.pending()


def test_known_review_is_retired_during_observation_too(tmp_path):
    import cv2
    from pathlib import Path
    from forgely_reading_review import ReviewStore
    from forgely_review_collection import ReviewCollector,complete_stat_line
    store=ReviewStore(tmp_path/'review.sqlite3')
    collector=ReviewCollector(store,interval=0)
    base=Path(__file__).parent/'fixtures'
    image=cv2.imread(str(base/'cv_review_intelligence_40.png'))
    ident=store.offer(complete_stat_line(image),scale='old-scale')
    collector.observe(Image.open(base/'cv_cycloide_holdout_224632.png'),
                      Image.new('RGB',(130,28)), '', '',context='test',token=1)
    assert store.get(ident)['state']=='superseded'


def test_collects_only_effect_rows_deduplicates_and_rejects_tooltip(tmp_path):
    from forgely_review_collection import ReviewCollector
    from forgely_reading_review import ReviewStore
    store=ReviewStore(tmp_path/'review.sqlite3')
    service=ReviewCollector(store,interval=0,automatic=False)
    im=np.zeros((400,442,3),np.uint8)
    import cv2
    from pathlib import Path
    source=cv2.imread(str(Path(__file__).parent/'fixtures/cv_review_intelligence_40.png'))
    mask=cv2.cvtColor(source,cv2.COLOR_BGR2GRAY)>130
    for y in (90,135):
        im[y:y+35,12:430]=[75,43,43]
        region=im[y:y+source.shape[0],146:146+source.shape[1]]
        region[mask]=source[mask]
    sy,sx=np.argwhere(mask)[-10]
    im[135+sy,146+sx]=0
    image=Image.fromarray(im[:,:,::-1])
    pool=Image.new('RGB',(130,28),(60,60,90))
    service.observe(image,pool,'10 Vitalité\n0 PA','',context='objet',token=1)
    rows=store.pending()
    assert len(rows)==2
    service.observe(image,pool,'10 Vitalité\n0 PA','',context='autre objet',token=2)
    assert len(store.pending())==2
    other=ReviewStore(tmp_path/'blocked.sqlite3')
    ReviewCollector(other,interval=0).observe(image,pool,'Prix moyen 10 Vitalité','',context='',token=1)
    assert not other.pending()


def test_complete_lines_are_tightly_cropped_and_cut_labels_are_rejected():
    import cv2
    from pathlib import Path
    from forgely_review_collection import complete_stat_line
    image=cv2.imread(str(Path(__file__).parent/'fixtures/cv_review_intelligence_40.png'))
    line=complete_stat_line(image)
    assert line is not None and line.shape[1]<170
    assert complete_stat_line(image[:,:110]) is None
    assert complete_stat_line(image[13:]) is None


def test_bundled_calibration_reads_holdout_and_does_not_ask_user(tmp_path):
    import cv2
    from pathlib import Path
    from forgely_review_collection import ReviewCollector
    from forgely_reading_review import ReviewStore
    service=ReviewCollector(ReviewStore(tmp_path/'review.sqlite3'),interval=0)
    base=Path(__file__).parent/'fixtures'
    image=Image.open(base/'cv_cycloide_holdout_224632.png').convert('RGB')
    # Pool ROI comes from the same held-out image, not a training sample.
    pool=image.crop((78,15,155,35))
    out=service.observe(image,pool,'','',context='Cycloïde',token=1)
    assert len(out['visual_jet'])==11
    assert out['visual_jet']['Vitalité']==297 and out['visual_jet']['Dommages Terre']==7
    assert out['pending']==0
    again=service.observe(image,pool,'','',context='Cycloïde',token=2)
    assert again is not None and again['visual_jet']==out['visual_jet'] and again['token']==2
