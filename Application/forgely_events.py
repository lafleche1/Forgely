"""Guardrails for local, fully automated OCR collection.

Only an unambiguous explicit rune name and result are accepted. Repeated
stationary OCR text is never counted twice. Continuous identical successive
attempts *may* be missed; this is preferable to inventing statistics.
"""
from dataclasses import dataclass
from runeforge_observer import find_outcome, find_rune

@dataclass(frozen=True)
class RecordedEvent:
    rune: str
    outcome: str
    evidence: str

class AutoEventDetector:
    """Arm on a clean screen, count one explicit rune/result transition.

    We must see two consecutive polls without a readable outcome before
    accepting the next event. This avoids counting a historical/stale result
    at startup and avoids duplicates from a result that remains visible.
    It can miss events when results persist or occur between polls.
    """
    def __init__(self, runes):
        self.runes = tuple(runes)
        self.armed = False
        self.clean_frames = 0
        self.visible = False
        self.saved = 0
        self.uncertain = 0

    def observe(self, text):
        result = find_outcome(text)
        if result is None:
            self.clean_frames += 1
            if self.clean_frames >= 2:
                self.armed = True
                self.visible = False
            return None
        self.clean_frames = 0
        if self.visible or not self.armed:
            return None
        self.visible = True
        self.armed = False
        rune = find_rune(text, self.runes)
        if rune is None:
            self.uncertain += 1
            return None
        self.saved += 1
        return RecordedEvent(rune, result, ' '.join(text.split())[:350])
