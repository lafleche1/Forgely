"""Synthetic geometry and glyph tests; these are not samples of DOFUS's font."""
import numpy as np
import cv2
import pytest

from forgely_cv.geometry import Rect, LayoutProfile
from forgely_cv.detection import InterfaceDetector
from forgely_cv.masking import chat_masks
from forgely_cv.glyphs import GlyphReader, segment_glyphs


def scene():
    rng = np.random.default_rng(13)
    template = rng.integers(0, 255, (12, 20, 3), dtype=np.uint8)
    image = np.zeros((160, 260, 3), np.uint8)
    image[25:37, 45:65] = template
    profile = LayoutProfile(Rect(-10, -10, 180, 110),
                            Rect(20, 20, 100, 40), Rect(10, 65, 150, 30))
    return image, template, profile


def test_anchor_returns_absolute_game_and_subregions_with_negative_monitor_origin():
    image, template, profile = scene()
    found = InterfaceDetector(template, profile).locate(image, origin=(-400, 100))
    assert found.game == Rect(-365, 115, 180, 110)
    assert found.stats == Rect(-345, 135, 100, 40)
    assert found.chat == Rect(-355, 180, 150, 30)


def test_duplicate_anchor_is_ambiguous_and_a_missing_anchor_clears_detection():
    image, template, profile = scene()
    detector = InterfaceDetector(template, profile)
    assert detector.locate(image) is not None
    image[25:37, 75:95] = template
    assert detector.locate(image) is None
    assert detector.locate(np.zeros_like(image)) is None


def test_flat_anchor_and_out_of_bounds_profile_are_rejected():
    _, _, profile = scene()
    with pytest.raises(ValueError):
        InterfaceDetector(np.zeros((10, 10), np.uint8), profile)
    with pytest.raises(ValueError):
        LayoutProfile(Rect(0, 0, 30, 30), Rect(20, 20, 20, 20), Rect(0, 0, 10, 10))


def test_hsv_red_wraparound_and_exact_black_background():
    hsv = np.array([[[0, 255, 255], [179, 255, 255], [60, 255, 255],
                     [110, 255, 255], [60, 0, 200], [60, 255, 20]]], np.uint8)
    masks = chat_masks(cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR))
    assert masks['red'].tolist() == [[255, 255, 0, 0, 0, 0]]
    assert masks['green'].tolist() == [[0, 0, 255, 0, 0, 0]]
    assert set(np.unique(masks['green'])) <= {0, 255}


def test_disconnected_dot_is_grouped_with_its_stem_and_minus_is_retained():
    mask = np.zeros((20, 30), np.uint8)
    mask[2:4, 3:5] = 255
    mask[6:13, 3:5] = 255
    mask[9:10, 15:20] = 255
    glyphs = segment_glyphs(mask)
    assert len(glyphs) == 2
    assert glyphs[0].box == Rect(3, 2, 2, 11)
    assert glyphs[1].box == Rect(15, 9, 5, 1)


def test_glyph_reader_rejects_unknown_and_ambiguous_characters():
    a = np.array([[255, 0], [255, 255], [255, 0]], np.uint8)
    reader = GlyphReader({'a': [a]})
    assert reader.recognize(a).text == 'a'
    assert reader.recognize(np.ones((6, 6), np.uint8) * 255).text == '?'
    assert GlyphReader({'a': [a], 'b': [a]}).recognize(a).text == '?'


def test_profile_round_trip_keeps_scale_tag_and_rectangles(tmp_path):
    _, _, profile = scene()
    path = tmp_path / 'profile.json'
    profile.save(path)
    assert LayoutProfile.load(path) == profile


def test_pipeline_drops_old_boxes_and_masks_when_interface_closes():
    from forgely_cv.pipeline import VisionPipeline
    image, template, profile = scene()
    pipeline = VisionPipeline(InterfaceDetector(template, profile))
    assert pipeline.process(image).detection is not None
    closed = pipeline.process(np.zeros_like(image))
    assert closed.detection is None and not closed.masks and closed.stats_bgr is None


def test_mss_capture_owns_a_stable_bgr_buffer(monkeypatch):
    import mss
    from forgely_cv.capture import MSSCapture
    source = np.zeros((10, 20, 4), np.uint8)
    source[:, :] = [10, 20, 30, 255]
    class FakeMSS:
        monitors = [{'left': -20, 'top': 0, 'width': 20, 'height': 10}]
        def grab(self, area):
            assert area['left'] == -20
            return source
        def close(self):
            pass
    monkeypatch.setattr(mss, 'mss', FakeMSS)
    with MSSCapture(monitor=0) as capture:
        first = capture.grab()
        source[:, :] = 0
        second = capture.grab()
        assert first.bgr[0, 0].tolist() == [10, 20, 30]
        assert second.bgr[0, 0].tolist() == [0, 0, 0]
        assert first.region == Rect(-20, 0, 20, 10)


def test_empty_mask_never_becomes_an_accepted_reading():
    assert GlyphReader({}).read(np.zeros((10, 10), np.uint8)) == ('', [], False)


def test_cli_calibration_and_offline_benchmark(tmp_path, capsys):
    import json
    from forgely_cv.__main__ import main
    image, _, _ = scene()
    path = tmp_path/'scene.png'
    assert cv2.imwrite(str(path), image)
    folder = tmp_path/'calibration'
    main(['calibrate', '--image', str(path), '--game', '35', '15', '180', '110',
          '--anchor', '45', '25', '20', '12', '--stats', '55', '35', '100', '40',
          '--chat', '45', '80', '150', '30', '--output', str(folder)])
    capsys.readouterr()
    assert (folder/'anchor.png').exists()
    main(['benchmark', '--profile', str(folder/'profile.json'),
          '--image', str(path), '--iterations', '4'])
    report = json.loads(capsys.readouterr().out)
    assert report['detected'] == 4
    assert report['scope'] == 'traitement_seul_sans_capture'
