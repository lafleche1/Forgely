"""Capture MSS persistante, sans disque, sans PIL et sans file d'attente."""
from contextlib import contextmanager
from dataclasses import dataclass
from threading import get_ident
from time import perf_counter_ns, sleep
import ctypes
import cv2
import numpy as np
from .geometry import Rect


@contextmanager
def physical_pixels():
    """Windows : garder MSS et les coordonnées en pixels physiques (DPI)."""
    previous = setter = None
    try:
        from ctypes import wintypes
        setter = ctypes.windll.user32.SetThreadDpiAwarenessContext
        setter.argtypes, setter.restype = [wintypes.HANDLE], wintypes.HANDLE
        previous = setter(wintypes.HANDLE(-4))
    except (AttributeError, OSError):
        pass
    try:
        yield
    finally:
        if previous and setter:
            setter(previous)


@dataclass(frozen=True)
class CaptureFrame:
    bgr: np.ndarray
    region: Rect
    started_ns: int
    capture_ns: int


class MSSCapture:
    """Créer, capturer et fermer sur le même thread ; une session par worker.

    Les captures écran contiennent les fenêtres qui recouvrent le jeu. MSS ne
    permet pas de reconstruire une fenêtre cachée ou minimisée.
    """
    def __init__(self, region=None, monitor=1):
        self.region, self.monitor = region, monitor
        self._session = None
        self._thread = None

    def __enter__(self):
        import mss
        if self._session is not None:
            raise RuntimeError('Session déjà ouverte')
        with physical_pixels():
            self._session = mss.mss()
            try:
                if self.region is None:
                    if not 0 <= self.monitor < len(self._session.monitors):
                        raise ValueError('Moniteur absent (0 = bureau virtuel, 1 = principal)')
                    area = self._session.monitors[self.monitor]
                    self.region = Rect(area['left'], area['top'], area['width'], area['height'])
            except Exception:
                self._session.close()
                self._session = None
                raise
        self._thread = get_ident()
        return self

    def grab(self):
        if self._session is None or get_ident() != self._thread:
            raise RuntimeError('Utiliser la session MSS sur son thread créateur')
        started = perf_counter_ns()
        with physical_pixels():
            shot = self._session.grab(dict(left=self.region.x, top=self.region.y,
                                          width=self.region.w, height=self.region.h))
        # Vue BGRA sans copie puis conversion native : le BGR final possède son
        # propre tampon et reste stable après la capture suivante.
        bgr = cv2.cvtColor(np.asarray(shot), cv2.COLOR_BGRA2BGR)
        return CaptureFrame(bgr, self.region, started, perf_counter_ns()-started)

    def frames(self, fps=60., count=None):
        """Fréquence CIBLE ; aucune garantie si capture + traitement sont trop lents."""
        if not 0 < fps <= 240 or count is not None and (type(count) is not int or count < 1):
            raise ValueError('Cadence ou nombre de captures invalide')
        period = int(1e9/fps)
        index = 0
        while count is None or index < count:
            started = perf_counter_ns()
            yield self.grab()
            index += 1
            # Le consommateur traite le frame courant. Aucun rattrapage de
            # captures anciennes si le traitement dépasse le budget.
            remaining = period-(perf_counter_ns()-started)
            if remaining > 0:
                sleep(remaining/1e9)

    def __exit__(self, *args):
        if self._session is not None:
            if get_ident() != self._thread:
                raise RuntimeError('Fermer MSS sur son thread créateur')
            self._session.close()
            self._session = None
