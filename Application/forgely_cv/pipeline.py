"""Assemblage de la détection et du masquage, sans état métier de forgemagie."""
from dataclasses import dataclass
from time import perf_counter_ns
import numpy as np
from .detection import InterfaceDetector, Detection
from .geometry import Rect
from .masking import chat_masks


@dataclass
class Analysis:
    detection: Detection | None
    masks: dict
    stats_bgr: np.ndarray | None
    texts: dict
    processing_ns: int
    numbers: object = None


class VisionPipeline:
    def __init__(self, detector: InterfaceDetector, glyph_reader=None, ranges=None, numeric_reader=None,
                 adaptive_rows=False):
        self.detector, self.glyph_reader, self.ranges = detector, glyph_reader, ranges
        self.numeric_reader = numeric_reader
        self.adaptive_rows = adaptive_rows
        self._previous = None

    def process(self, bgr, origin=(0, 0)):
        started = perf_counter_ns()
        found = None
        frame = Rect(origin[0], origin[1], bgr.shape[1], bgr.shape[0])
        if self._previous:
            anchor = self._previous.anchor
            search = Rect(anchor.x-24, anchor.y-24, anchor.w+48, anchor.h+48)
            if frame.contains(search):
                found = self.detector.locate(bgr, origin, search)
        if found is None:
            found = self.detector.locate(bgr, origin)
        self._previous = found  # Aucun rectangle périmé si l'atelier disparaît.
        if found is None:
            return Analysis(None, {}, None, {}, perf_counter_ns()-started)
        masks = chat_masks(found.chat.crop(bgr, origin), self.ranges)
        texts = {}
        if self.glyph_reader is not None:
            for color, mask in masks.items():
                text, matches, accepted = self.glyph_reader.read(mask)
                texts[color] = dict(text=text, accepted=accepted,
                                    unknown=sum(not m.accepted for m in matches))
        stats = found.stats.crop(bgr, origin)
        numbers = ((self.numeric_reader.read_visible(stats) if self.adaptive_rows else self.numeric_reader.read(stats))
                   if self.numeric_reader is not None else None)
        return Analysis(found, masks, stats, texts, perf_counter_ns()-started, numbers)


class ProfilePipeline:
    """Select exactly one calibrated native layout, including its own font.

    Profiles may describe the workshop panel itself as their game rectangle;
    moving that panel is then independent of the inventory or screen borders.
    Never resize a screenshot to force a pixel dictionary to fit.
    """
    def __init__(self, pipelines):
        self.pipelines = list(pipelines)
        if not self.pipelines:
            raise ValueError('Au moins un profil natif requis')

    def process(self, bgr, origin=(0,0)):
        started = perf_counter_ns()
        matches = [r for p in self.pipelines if (r := p.process(bgr, origin)).detection is not None]
        if len(matches) != 1:
            return Analysis(None, {}, None, {}, perf_counter_ns()-started)
        result = matches[0]
        result.processing_ns = perf_counter_ns()-started
        return result
