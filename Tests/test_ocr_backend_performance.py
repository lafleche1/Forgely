import concurrent.futures
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Application'))
import runeforge_observer as observer


@pytest.fixture
def engine(monkeypatch):
    calls = []
    class TessError(Exception):
        pass
    def recognize(image, **kwargs):
        calls.append((image.copy(), kwargs))
        time.sleep(.03)
        return str(image.getpixel((0, 0)))
    fake = SimpleNamespace(pytesseract=SimpleNamespace(tesseract_cmd='tesseract'),
                           image_to_string=recognize, TesseractError=TessError,
                           TesseractNotFoundError=type('NotFound', (Exception,), {}))
    monkeypatch.setitem(sys.modules, 'pytesseract', fake)
    # Separate test requests from the process-wide completed-results cache.
    command = 'test-' + str(time.monotonic_ns())
    return fake, calls, command


def test_identical_pixels_share_one_ocr_across_workers(engine):
    fake, calls, command = engine
    image = Image.new('RGB', (30, 15), 'white')
    with concurrent.futures.ThreadPoolExecutor(8) as pool:
        results = list(pool.map(lambda _: observer.extract_text(image.copy(), command), range(8)))
    assert len(set(results)) == 1
    assert len(calls) == 1
    assert observer.extract_text(image.copy(), command) == results[0]
    assert len(calls) == 1


def test_changed_pixels_title_and_command_are_independent(engine):
    _, calls, command = engine
    image = Image.new('RGB', (30, 15), 'white')
    observer.extract_text(image, command)
    image.putpixel((1, 1), (0, 0, 0))
    observer.extract_text(image, command)
    image.info['forgely_title'] = True
    observer.extract_text(image, command)
    observer.extract_text(image, command + '-other')
    assert len(calls) == 4
    assert [c[1]['config'] for c in calls] == ['--psm 6', '--psm 6', '--psm 7', '--psm 7']
    assert all(c[1]['lang'] == 'fra+eng' for c in calls)
    assert calls[0][0].size == (60, 30)


def test_ocr_failures_are_retried_and_fallback_preserves_original(engine):
    fake, calls, command = engine
    image = Image.new('RGB', (30, 15), 'white')
    def broken(image, **kwargs):
        calls.append((image.copy(), kwargs))
        raise fake.TesseractError('broken')
    fake.image_to_string = broken
    for _ in range(2):
        with pytest.raises(RuntimeError, match='ne peut pas lire'):
            observer.extract_text(image, command)
    assert len(calls) == 4
    assert calls[1][0].mode == 'RGB'
    assert calls[1][0].size == image.size
    assert calls[1][1] == {'lang': 'eng', 'config': '--psm 6'}


def test_executable_discovery_is_reused(engine, monkeypatch):
    import shutil
    _, calls, _ = engine
    discoveries = []
    monkeypatch.setenv('PATH', '/unique-' + str(time.monotonic_ns()))
    monkeypatch.setattr(shutil, 'which', lambda name: discoveries.append(name) or '/tesseract')
    observer.extract_text(Image.new('RGB', (31, 15), 'white'))
    observer.extract_text(Image.new('RGB', (32, 15), 'white'))
    assert discoveries == ['tesseract']


def test_completed_cache_is_bounded_and_evicted_images_are_recognized(engine):
    import forgely_ocr_backend as backend
    _, calls, command = engine
    for n in range(backend._MAX_RESULTS + 1):
        observer.extract_text(Image.new('L', (2, 2), n), command)
    assert len(backend._RESULTS) <= backend._MAX_RESULTS
    observer.extract_text(Image.new('L', (2, 2), 0), command)
    assert len(calls) == backend._MAX_RESULTS + 2


def test_different_commands_remain_stable_through_overlapping_calls(engine):
    fake, _, command = engine
    observed = []
    def recognize(image, **kwargs):
        before = fake.pytesseract.tesseract_cmd
        time.sleep(.02)
        observed.append((before, fake.pytesseract.tesseract_cmd))
        return before
    fake.image_to_string = recognize
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        futures = [pool.submit(observer.extract_text, Image.new('L', (4, 4)), cmd)
                   for cmd in (command, command + '-other')]
        assert [f.result() for f in futures] == [command, command + '-other']
    assert all(a == b for a, b in observed)


def test_success_cache_expires_for_runtime_model_updates(engine, monkeypatch):
    import forgely_ocr_backend as backend
    _, calls, command = engine
    now = [100.0]
    monkeypatch.setattr(time, 'monotonic', lambda: now[0])
    image = Image.new('L', (7, 7))
    observer.extract_text(image, command)
    now[0] += getattr(backend, '_RESULT_TTL', 2.0) + .01
    observer.extract_text(image, command)
    assert len(calls) == 2


def test_exception_releases_all_waiters_and_next_call_retries(engine):
    fake, calls, command = engine
    def broken(image, **kwargs):
        calls.append(1)
        time.sleep(.03)
        raise fake.TesseractNotFoundError('missing')
    fake.image_to_string = broken
    with concurrent.futures.ThreadPoolExecutor(5) as pool:
        futures = [pool.submit(observer.extract_text, Image.new('L', (8, 8)), command)
                   for _ in range(5)]
        for future in futures:
            with pytest.raises(RuntimeError, match='Tesseract absent'):
                future.result(timeout=2)
    assert len(calls) == 1
    with pytest.raises(RuntimeError):
        observer.extract_text(Image.new('L', (8, 8)), command)
    assert len(calls) == 2


def test_diagnostic_preview_zone_shares_recognition_but_other_metadata_does_not(engine):
    _, calls, command = engine
    image = Image.new('RGB', (11, 11), 'white')
    observer.extract_text(image, command)
    preview = image.copy()
    preview.info['forgely_preview_zone'] = 'effects'
    observer.extract_text(preview, command)
    assert len(calls) == 1
    preview.info['transparency'] = (255, 255, 255)
    observer.extract_text(preview, command)
    assert len(calls) == 2


def test_ocr_defaults_to_one_openmp_thread(engine, monkeypatch):
    import os
    fake, _, command = engine
    monkeypatch.delenv('OMP_THREAD_LIMIT', raising=False)
    observed = []
    fake.image_to_string = lambda image, **kwargs: observed.append(os.environ.get('OMP_THREAD_LIMIT')) or 'ok'
    observer.extract_text(Image.new('L', (12, 12)), command)
    assert observed == ['1']


def test_ocr_preserves_explicit_openmp_thread_override(engine, monkeypatch):
    import os
    fake, _, command = engine
    monkeypatch.setenv('OMP_THREAD_LIMIT', '3')
    observed = []
    fake.image_to_string = lambda image, **kwargs: observed.append(os.environ.get('OMP_THREAD_LIMIT')) or 'ok'
    observer.extract_text(Image.new('L', (13, 13)), command)
    assert observed == ['3']
