"""Bounded exact-capture reuse shared by preview and observer workers.

Only successful recognition is retained. Pixels and OCR configuration identify
results, so a changed capture is never treated as the preceding frame.
"""
from collections import OrderedDict
from concurrent.futures import Future
from functools import lru_cache
import hashlib
import os
from pathlib import Path
import shutil
import threading
import time
from contextlib import contextmanager

_RESULTS = OrderedDict()
_PENDING = {}
_CONDITION = threading.Condition()
_MAX_RESULTS = 64
_RESULT_TTL = 2.0
_MAX_PENDING = 32
_ENGINE_CONDITION = threading.Condition()
_ACTIVE = 0
_ACTIVE_CONFIG = None


@lru_cache(maxsize=16)
def _discover(path, localappdata, programfiles, refresh_slot):
    executable = shutil.which('tesseract')
    if not executable:
        candidates = (Path('C:/Program Files/Tesseract-OCR/tesseract.exe'),
                      Path(localappdata) / 'Programs/Tesseract-OCR/tesseract.exe',
                      Path(programfiles) / 'Tesseract-OCR/tesseract.exe')
        executable = next((str(p) for p in candidates if p.is_file()), 'tesseract')
    return executable


@lru_cache(maxsize=16)
def _local_tessdata(localappdata, refresh_slot):
    directory = Path(localappdata) / 'Forgely/tessdata'
    if all((directory / (lang + '.traineddata')).is_file() for lang in ('fra', 'eng')):
        return str(directory)
    return None


@contextmanager
def _engine_configuration(engine, command, tessdata):
    """Keep pytesseract's process-global command stable during subprocess calls.

    Calls using the same configuration can run concurrently. A settings change
    waits for old calls before updating globals, avoiding cross-worker races.
    """
    global _ACTIVE, _ACTIVE_CONFIG
    config = (command, tessdata)
    with _ENGINE_CONDITION:
        _ENGINE_CONDITION.wait_for(lambda: not _ACTIVE or _ACTIVE_CONFIG == config)
        if not _ACTIVE:
            engine.pytesseract.tesseract_cmd = command
            if tessdata is not None:
                os.environ['TESSDATA_PREFIX'] = tessdata
            _ACTIVE_CONFIG = config
        _ACTIVE += 1
    try:
        yield
    finally:
        with _ENGINE_CONDITION:
            _ACTIVE -= 1
            _ENGINE_CONDITION.notify_all()


def extract_text(image, tesseract_cmd=''):
    # Small OCR patches are faster with one OpenMP thread, especially when
    # preview and observer subprocesses overlap. Respect user configuration.
    os.environ.setdefault('OMP_THREAD_LIMIT', '1')
    try:
        import pytesseract
    except ImportError as exc:
        raise RuntimeError('OCR manquant : installe pytesseract avec installer.bat') from exc
    command = tesseract_cmd.strip() or _discover(
        os.environ.get('PATH', ''), os.environ.get('LOCALAPPDATA', ''),
        os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)'), int(time.monotonic() / 5))
    tessdata = _local_tessdata(os.environ.get('LOCALAPPDATA', ''), int(time.monotonic() / 5)) or os.environ.get('TESSDATA_PREFIX')
    # Snapshot before hashing and preprocessing: callers may reuse PIL objects.
    title = bool(getattr(image, 'info', {}).get('forgely_title'))
    snapshot = image.copy()
    # Palette entries and transparency can affect grayscale/fallback recognition.
    palette = snapshot.palette.tobytes() if snapshot.palette else None
    key = (command, tessdata, os.environ.get('OMP_THREAD_LIMIT'), snapshot.mode, snapshot.size, title, palette,
           repr(sorted(((name, value) for name, value in snapshot.info.items()
                        if name != 'forgely_preview_zone'), key=lambda item: item[0])),
           hashlib.sha256(snapshot.tobytes()).digest())
    with _CONDITION:
        if key in _RESULTS and _RESULTS[key][1] <= time.monotonic():
            del _RESULTS[key]
        while key not in _RESULTS and key not in _PENDING and len(_PENDING) >= _MAX_PENDING:
            _CONDITION.wait()
        if key in _RESULTS:
            _RESULTS.move_to_end(key)
            return _RESULTS[key][0]
        pending = _PENDING.get(key)
        owner = pending is None
        if owner:
            pending = _PENDING[key] = Future()
    if not owner:
        return pending.result()
    try:
        with _engine_configuration(pytesseract, command, tessdata):
            result = _recognize(snapshot, title, pytesseract)
    except BaseException as exc:
        with _CONDITION:
            _PENDING.pop(key, None)
            pending.set_exception(exc)
            _CONDITION.notify_all()
        raise
    with _CONDITION:
        _RESULTS[key] = (result, time.monotonic() + _RESULT_TTL)
        while len(_RESULTS) > _MAX_RESULTS:
            _RESULTS.popitem(last=False)
        _PENDING.pop(key, None)
        pending.set_result(result)
        _CONDITION.notify_all()
    return result


def _recognize(image, title, pytesseract):
    try:
        from PIL import ImageOps, ImageEnhance
        gray = ImageOps.grayscale(image)
        if gray.width < 1250:
            gray = gray.resize((gray.width * 2, gray.height * 2))
        gray = ImageEnhance.Contrast(gray).enhance(2)
        return pytesseract.image_to_string(gray, lang='fra+eng',
                                          config='--psm 7' if title else '--psm 6')
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError('Tesseract absent. Installe le logiciel Tesseract pour Windows.') from exc
    except pytesseract.TesseractError:
        try:
            return pytesseract.image_to_string(image, lang='eng', config='--psm 6')
        except pytesseract.TesseractError as exc:
            raise RuntimeError('Tesseract ne peut pas lire cette capture.') from exc
